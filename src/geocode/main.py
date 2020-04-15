"""
Retrieves coordinates for entities (accommodations, points of interest and destinations). Each task
includes enough information to determine the entity (ID and type) and its location (e.g. address for
accommodations).

The geocoder can be triggered using the Kinesis stream. Output is written to DynamoDB.

More complex functionality:
- Results are stored in a cache database for a certain amount of time (CACHE_TTL). This prevents
  unnecessary quota spending (e.g. Kafka changes on irrelevant fields).
- The DynamoDB table has time-to-live enabled to conform to storage restrictions imposed by
  individual providers. In case of no restrictions, results are kept indefinitely unless updated.
- Automatic provider disabling and reenabling in case of quota exhaustion.
- Tasks that fail due to server side faults or quota exhaustion are rescheduled the next day.
- Address information supplied to a provider is reduced interatively until a result is obtained.
  You can specify address fields which should always be supplied (e.g. country code)
- In many cases you can supply a guess coordinate to bias results.
"""
import base64
import collections
import hashlib
import itertools
import json
import logging
import os
import datetime
import time

import boto3
import jsonschema
import redis
import rollbar

from geocode import entity, logger, helpers

print("Main imports")

# Logging (Rollbar)
ROLLBAR = {
    'access_token': '05bb6dde218b4c0ab4e27567f2c801ee',
    'environment': os.environ.get('ENVIRONMENT'),
    'handler': 'blocking',
    'locals': {'enabled': False}
}
if ROLLBAR['environment'] in ('production',):
    rollbar.init(**ROLLBAR)

# Input validation (JSON)
SCHEMA = helpers.load_validation_schema()

# Parameters
EXHAUSTED = dict()  # providers for which quota is exhausted
CACHE_TTL = 60*60*24*30     # time spent in cache layer in seconds


def batch(iterable, batch_size=1):
    """
    Batches an iterable in chunks of size batch_size.
    """
    sourceiter = iter(iterable)
    while True:
        batchiter = itertools.islice(sourceiter, batch_size)
        yield itertools.chain([next(batchiter)], batchiter)


def send_to_buffer_queue(task_batch):
    """
    Sends geocoder tasks to the buffer stream to be processed at a later date.
    """
    queue = boto3.resource('sqs').get_queue_by_name(QueueName=os.environ.get('QUEUE'))

    for sqs_batch in batch(task_batch, batch_size=10):
        response = queue.send_messages(
            Entries=[
                {
                    'Id': str(i),
                    'MessageBody': json.dumps(task)
                } for i, task in enumerate(sqs_batch)
            ]
        )

    return response


def load_provider(provider):
    """
    Return a geocoder API object for the given provider.
    """
    from geocode import providers
    return getattr(
        providers,
        ''.join([token.capitalize() for token in provider.split('_')])
    )()


def load_entity(entity_id, entity_type, address):
    """
    Return an entity object for the given entity data.
    """
    entity_object = getattr(
        entity,
        ''.join([token.capitalize() for token in entity_type.split('_')])
    )(entity_id, **address)

    return entity_object


def check_exhausted_quota():
    """
    Check reset times for provider that hit quota limits. If the current time exceeds it, then
    reenable.
    """
    current_timestamp = datetime.datetime.now().timestamp()

    reenable = []
    for k, v in EXHAUSTED.items():
        if current_timestamp > v:
            reenable.append(k)

            event = {
                'state': 'provider reenabling',
                'field': 'timestamp',
                'value': v
            }

            logger.log_event(logging.INFO, event, provider=k)

    for provider in reenable:
        del EXHAUSTED[provider]


def cache_hash(task, geocoder_version):
    """
    Computes a hash for the supplied task and geocoder version to use in Redis. The hash is entity
    agnostic, meaning it only looks at the address and the provider (+ version).
    """
    data = task['address'].copy()

    data['provider'] = '{provider}:{version}'.format(
        provider=task['provider'],
        version=geocoder_version
    )

    return hashlib.md5(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()


def load_tasks(records : list):
    """
    Decode and validate all incoming tasks from Kinesis.
    """
    tasks = []

    for record in records:
        if 'kinesis' in record:
            task = json.loads(base64.b64decode(record['kinesis']['data']).decode('utf-8'))
        elif 'lambda' in record:
            task = record['lambda']['data']
        elif record['eventSource'] == 'aws:sqs':
            task = json.loads(record['body'])
        else:
            continue

        try:
            # validate the JSON input
            jsonschema.validate(task, SCHEMA)

            tasks.append(task)
        except jsonschema.ValidationError:
            log_task = dict((k, task[k]) for k in [
                'entity_id',
                'entity_type',
                'provider'
            ] if k in task)

            event = {
                'state': 'invalid task'
            }

            logger.log_event(logging.ERROR, event, **log_task)

        except json.JSONDecodeError:
            event = {
                'state': 'decoding error'
            }
            logger.log_event(logging.CRITICAL, event, data=record['body'])

    return tasks


# def load_cache(tasks : list):
#     """
#     Returns cache keys and if present, cache results for the given tasks, None otherwise.
#     """
#     keys = []
#
#     read_pipe = REDIS.pipeline()
#
#     for task in tasks:
#         provider = load_provider(task['provider'])
#
#         key = cache_hash(task, provider.version)
#
#         read_pipe.get(key)
#         keys.append(key)
#
#
#     cache = None
#     while not cache:
#         try:
#             cache = map(lambda x: json.loads(x) if x else None, read_pipe.execute())
#         except TimeoutError:
#             time.sleep(5)
#
#     return keys, cache


def filter_tasks(keys : list, tasks : list, cache : list):
    """
    Returns keys and tasks for which cache results are inexistent or irrelevant (not same address).
    Complete tasks get written to DynamoDB.
    """
    table = boto3.resource('dynamodb').Table(os.environ.get('TABLE'))

    with helpers.BatchWriterOCC(table, overwrite_by_pkeys=('entity', 'provider')) as batch_writer:
        for key, task, cache_result in zip(keys, tasks, cache):
            if cache_result and task['address'] == cache_result['meta'].get('address'):
                # add entity identifiers
                cache_result.update(dict(
                    entity_id=task['entity_id'],
                    entity_type=task['entity_type'],
                    provider=task['provider'],
                    batch_id=task.get('batch_id')
                ))

                cache_result['entity'] = '{entity_type}:{entity_id}'.format(**task)

                task = dict(
                    entity_id=task['entity_id'],
                    entity_type=task['entity_type'],
                    provider=task['provider'],
                    batch_id=task.get('batch_id')
                )

                event = dict(
                    state='reusing cached result'
                )

                logger.log_event(logging.INFO, event, **task)
                logger.log_status(logging.INFO, 'CACHE', status_code=0, **task)

                batch_writer.put_item(
                    Item=helpers.dynamo_sanitize(cache_result)
                )
            else:
                yield key, task


def geocode_task(task : dict):
    """
    Runs a task through the specified geocoding API. If the quota for the provider is exceeded,
    return None.
    """
    if task['provider'] in EXHAUSTED:
        raise helpers.QuotaExhaustedError(task['provider'])

    provider_object = load_provider(task['provider'])
    entity_object = load_entity(
        task['entity_id'],
        task['entity_type'],
        task['address']
    )

    result = provider_object.geocode(entity_object)

    return result


def store_results(results : dict):
    """
    Writes results to DynamoDB, Firehose (historization) and update cache layer.
    """
    if not results:
        return

    # write_pipe = REDIS.pipeline()

    # for k, v in results.items():
    #     write_pipe.set(k, json.dumps(v), CACHE_TTL)
    
    # write_pipe.execute()

    # to DynamoDB
    table = boto3.resource('dynamodb').Table(os.environ.get('TABLE'))

    with helpers.BatchWriterOCC(table, overwrite_by_pkeys=('entity', 'provider')) as batch_writer:
        for result in results:
            batch_writer.put_item(
                Item=helpers.dynamo_sanitize(result)
            )


def lambda_handler(event, context):
    """
    Processes messages from Kinesis to find geocodes for a supplied entity for a supplied provider.
    If results are already available in the cache, they are reused, otherwise the supplied address
    is sent to the specified geocoding API.

    Example task:

    {
        'provider': 'google',
        'entity_id': 123,
        'entity_type': 'hotel',
        'address': {
            'street': 'string',
            'name': 'string',
            'city': 'string',
            'postal_code': 'string',
            'country_code': 'string'
        }
    }
    
    {
        'provider': 'geonames',
        'entity_id': 123,
        'entity_type': 'destination',
        'address': {
            'name': 'string',
            'country': 'string'
        }
    }
    """
    try:
        check_exhausted_quota()

        tasks = load_tasks(event['Records'])
        # keys, cache = load_cache(tasks)

        results = []
        reschedules = []

        # for key, task in filter_tasks(keys, tasks, cache):
        for task in tasks:
            log_data = dict(
                entity_id=task['entity_id'],
                entity_type=task['entity_type'],
                batch_id=task.get('batch_id'),
                provider=task['provider']
            )

            try:
                task_result = geocode_task(task)
                task_result['batch_id'] = task.get('batch_id')
                results.append(task_result)

                logger.log_status(logging.INFO, 'OK', status_code=0, **log_data)
            except helpers.NoResultsFoundError as error:
                logger.log_status(logging.INFO, error.status, status_code=error.status_code, **log_data)
            except (helpers.FailedRequestError, helpers.RateLimitExceededError) as error:
                # Task failed on geocoder end or too many retries
                logger.log_status(logging.WARNING, error.status, status_code=error.status_code, **log_data)
            except helpers.InvalidRequestError as error:
                # Error on our end, report the task and return no results
                logger.log_status(logging.WARNING, error.status, status_code=error.status_code, **log_data)
                rollbar.report_exc_info(payload_data=task['address'])
            except helpers.QuotaExhaustedError:
                provider = task['provider']

                if provider not in EXHAUSTED:
                    # disable processing for provider
                    provider_object = load_provider(provider)
                    EXHAUSTED[provider] = provider_object.quota_reset()

                    event = {
                        'state': 'provider disabling',
                        'field': 'timestamp',
                        'value': EXHAUSTED[provider]
                    }

                    logger.log_event(logging.INFO, event, provider=provider)

                logger.log_status(logging.INFO, 'RESCHEDULE', status_code=-2, **log_data)
                reschedules.append(task)
            except helpers.GeocoderError:
                reschedules.append(task)
        
        store_results(results)
        # if reschedules:
        #     send_to_buffer_queue(reschedules)

    except Exception as error:
        logger.log_exception(error)
        if 'task' in locals():
            rollbar.report_exc_info(payload_data=task)
        else:
            rollbar.report_exc_info()

        raise error

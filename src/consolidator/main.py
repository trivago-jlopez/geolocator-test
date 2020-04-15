"""
Consolidates coordinates from several sources (geocoding APIs, scraped metadata, ...) according to
a ruleset.
"""
import json
import logging
import os

import boto3
import jsonschema
import rollbar

from consolidator import entity, logger
from consolidator.utils import fetcher, storer

# Logging (Rollbar)
ROLLBAR = {
    'access_token': 'ac69d5b500d5439a8d90ca340ed19e1c',
    'environment': os.environ.get('ENVIRONMENT'),
    'handler': 'blocking',
    'locals': {'enabled': False}
}
if ROLLBAR['environment'] == 'production':
    rollbar.init(**ROLLBAR)

# Resources
GEOCODER_TABLE_NAME = os.environ['GEOCODES_TABLE']


def load_tasks(records : list):
    """
    Validate incoming tasks from SQS.
    """
    tasks = []
    with open('schemas/consolidator.json') as f:
        schema = json.load(f)

    for record in records:
        try:
            task = json.loads(record['body'])

            # validate the JSON input
            jsonschema.validate(task, schema)

            tasks.append(task)
        except jsonschema.ValidationError:
            event = {
                'state': 'invalid task'
            }
            logger.log_event(logging.ERROR, event, **task)

        except json.JSONDecodeError:
            event = {
                'state': 'decoding error'
            }
            logger.log_event(logging.CRITICAL, event, data=record['body'])

    return tasks


def load_entity(task, data_fetcher : fetcher.Fetcher):
    return getattr(
        entity,
        ''.join([token.capitalize() for token in task['entity_type'].split('_')])
    )(task['entity_id'], data_fetcher)


def lambda_handler(event, context):
    """
    Processes SQS events and pushes the consolidated entities to Kinesis.

    Example task:

    {
        'entity_id': int,
        'entity_type': string,
        'batch_id': string
    }
    """
    try:
        data_fetcher = fetcher.Fetcher()
        data_storer = storer.Storer()

        tasks = load_tasks(event['Records'])

        consolidated_entities = []
        for task in tasks:
            entity = load_entity(task, data_fetcher)

            if entity.consolidated:
                consolidated_entities.append({
                    'entity': entity.key,
                    'batch_id': task.get('batch_id'),
                    **entity.to_dict(),
                    **entity.consolidated.to_dict(),
                    'score': entity.consolidated.score
                })

                logger.log_status(logging.INFO, 'OK',
                    batch_id=task.get('batch_id'),
                    **entity.to_dict(),
                    **entity.consolidated.to_dict(),
                    score=entity.consolidated.score
                )
            else:
                logger.log_status(logging.INFO, 'NO RESULTS',
                    batch_id=task.get('batch_id'),
                    **entity.to_dict()
                )

        if consolidated_entities:
            data_storer.store_consolidations(consolidated_entities, os.environ['ENVIRONMENT'])

    except Exception as error:
        logger.log_exception(error)

        if 'task' in locals():
            # some task caused the exception
            rollbar.report_exc_info(payload_data=task)
        else:
            # initialization, data loading, ... errors
            rollbar.report_exc_info()

        raise error

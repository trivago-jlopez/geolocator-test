import decimal
import json
import os

from botocore.stub import Stubber, ANY

from consolidator.utils import storer


class TestStorer:
    def test_initialize(self):
        storer.Storer()

    def test_store_consolidations(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'ENVIRONMENT', 'test')
            m.setitem(os.environ, 'GEOCODES_TABLE', 'test')
            data_storer = storer.Storer()

            stubber = Stubber(data_storer.client_dynamodb)
            stubber.add_response(
                'batch_write_item',
                service_response={
                    'UnprocessedItems': {},
                    'ConsumedCapacity': [
                        {
                            'TableName': os.environ['GEOCODES_TABLE'],
                            'CapacityUnits': 5.0,
                            'Table': {
                                'CapacityUnits': 5.0
                            }
                        }
                    ]
                },
                expected_params={
                    'RequestItems': {
                        os.environ['GEOCODES_TABLE']: [
                            {
                                'PutRequest': {
                                    'Item': {
                                        'entity': 'accommodation:1',
                                        'entity_id': 1,
                                        'entity_type': 'accommodation',
                                        'batch_id': None,
                                        'provider': 'consolidated_test',
                                        'longitude': decimal.Decimal('23.9482'),
                                        'latitude': decimal.Decimal('83.8779'),
                                        'score': decimal.Decimal('0.9'),
                                        'timestamp': ANY,
                                        'meta': {
                                            'city': 'Boston',
                                            'country_code': 'US'
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            )

            with stubber:
                data_storer.store_consolidations(
                    [
                        {
                            'entity': 'accommodation:1',
                            'entity_id': 1,
                            'entity_type': 'accommodation',
                            'provider': 'consolidated_' + os.environ['ENVIRONMENT'],
                            'longitude': 23.9482,
                            'latitude': 83.8779,
                            'score': 0.9,
                            'city': 'Boston',
                            'country_code': 'US'
                        }
                    ],
                    'test'
                )

    def test_broadcast_consolidations(self, monkeypatch):
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'OUTPUT_STREAM', 'test')
            data_storer = storer.Storer()

            records = [
                {
                    'entity_id': 1,
                    'entity_type': 'accommodation',
                    'longitude': decimal.Decimal('23.9482'),
                    'latitude': decimal.Decimal('83.8779'),
                    'score': decimal.Decimal('0.9'),
                    'meta': {
                        'city': 'Boston',
                        'country_code': 'US'
                    }
                },
                {
                    'entity_id': 2,
                    'entity_type': 'accommodation',
                    'longitude': decimal.Decimal('11.8882'),
                    'latitude': decimal.Decimal('84.3956'),
                    'score': decimal.Decimal('0.8'),
                    'meta': {
                        'city': 'Amsterdam',
                        'country_code': 'NL'
                    }
                }
            ]

            stubber = Stubber(data_storer.client_kinesis)
            stubber.add_response(
                'put_records',
                service_response={
                    'FailedRecordCount': 1,
                    'Records': [
                        {
                            'SequenceNumber': '1',
                            'ShardId': '0'
                        },
                        {
                            'SequenceNumber': '2',
                            'ShardId': '0',
                            'ErrorCode': 'test'
                        }
                    ]
                },
                expected_params={
                    'Records': [
                        {
                            'Data': json.dumps(record, cls=storer.DecimalEncoder).encode('utf-8'),
                            'PartitionKey': '{entity_type}:{entity_id}'.format(**record)
                        } for record in records
                    ],
                    'StreamName': os.environ['OUTPUT_STREAM']
                }
            )

            stubber.add_response(
                'put_records',
                service_response={
                    'Records': [
                        {
                            'SequenceNumber': '2',
                            'ShardId': '0'
                        }
                    ]
                },
                expected_params={
                    'Records': [
                        {
                            'Data': json.dumps(record, cls=storer.DecimalEncoder).encode('utf-8'),
                            'PartitionKey': '{entity_type}:{entity_id}'.format(**record)
                        } for record in records[1:]
                    ],
                    'StreamName': os.environ['OUTPUT_STREAM']
                }
            )

            with stubber:
                data_storer.broadcast_consolidations(records)

                stubber.assert_no_pending_responses()

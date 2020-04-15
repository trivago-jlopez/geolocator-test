"""
Tests destination entity processing and address components
"""
import jsonschema
import pytest

from geocode import main


@pytest.fixture
def setup_task():
    return {
        "provider": "geonames",
        "entity_id": 1,
        "entity_type": "destination",
        "address": {
            "city": "Wainuiomata",
            "country_code": "NZ"
        }
    }


@pytest.fixture
def setup_task_with_guess():
    return {
        "provider": "geonames",
        "entity_id": 1,
        "entity_type": "destination",
        "address": {
            "city": "Wainuiomata",
            "country_code": "NZ",
            "guess": {
                "longitude": 174.9546349,
                "latitude": -41.2592894
            }
        }
    }


def test_destination_validation(setup_task):
    """
    Tests JSON validation of destination geocoding tasks.
    """
    # valid destination job
    jsonschema.validate(setup_task, main.SCHEMA)

    # missing destination specific fields
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "provider": "geonames",
                "entity_id": 1,
                "entity_type": "destination",
                "address": {
                    "city": "Wainuiomata"
                }
            },
            main.SCHEMA
        )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "provider": "geonames",
                "entity_id": 1,
                "entity_type": "destination",
                "address": {
                    "country_code": "NZ"
                }
            },
            main.SCHEMA
        )


def test_destination_validation_guess_coordinate(setup_task_with_guess):
    """
    Tests validation of destination geocoding tasks with a guess coordinate.
    """
    jsonschema.validate(setup_task_with_guess, main.SCHEMA)


def test_destination_load(setup_task):
    destination = main.load_entity(
        setup_task['entity_id'],
        setup_task['entity_type'],
        setup_task['address']
    )

    assert destination.entity_id == 1
    assert destination.entity_type == 'destination'
    assert destination.country_code == setup_task['address']['country_code']
    assert destination.city == setup_task['address']['city']


def test_destination_address(setup_task):
    destination = main.load_entity(
        setup_task['entity_id'],
        setup_task['entity_type'],
        setup_task['address']
    )
    
    assert type(destination.address) == dict


def test_destination_address_fields(setup_task):
    destination = main.load_entity(
        setup_task['entity_id'],
        setup_task['entity_type'],
        setup_task['address']
    )
    address = destination.address
    
    assert 'entity_id' not in address
    assert 'entity_type' not in address
    assert address['country_code'] == setup_task['address']['country_code']
    assert address['city'] == setup_task['address']['city']
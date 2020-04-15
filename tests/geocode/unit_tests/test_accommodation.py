"""
Tests hotel entity processing and address components
"""
import jsonschema
import pytest

from geocode import main


@pytest.fixture
def setup_task():
    return {
        "provider": "google",
        "entity_id": 1,
        "entity_type": "accommodation",
        "address": {
            "name": "Hotel Beatles",
            "street": "30 Abbey Road",
            "district": "Camden",
            "city": "London",
            "region": "Greater London",
            "country": "United Kingdom",
            "country_code": "UK",
            "postal_code": "SW1A"
        }
    }
    

@pytest.fixture
def setup_task_with_guess():
    return {
        "provider": "google",
        "entity_id": 1,
        "entity_type": "accommodation",
        "address": {
            "name": "Hotel Beatles",
            "street": "30 Abbey Road",
            "district": "Camden",
            "city": "London",
            "region": "Greater London",
            "country": "United Kingdom",
            "country_code": "UK",
            "postal_code": "SW1A",
            "guess": {
                "longitude": 0.0,
                "latitude": 0.0
            }
        }
    }


def test_hotel_validation(setup_task):
    """
    Tests JSON validation of hotel geocoding tasks.
    """
    # valid hotel job
    jsonschema.validate(setup_task, main.SCHEMA)

    # invalid hotel job (lower case country code)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "provider": "google",
                "entity_id": 1,
                "entity_type": "accommodation",
                "address": {
                    "street": "11 Candycane",
                    "name": "Feed Me!",
                    "city": "Chickentown",
                    "region": "Chocolate quarter",
                    "country_code": "de",
                }
            },
            main.SCHEMA
        )

    # missing hotel specific fields
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "provider": "google",
                "entity_id": 1,
                "entity_type": "accommodation",
                "address": {
                    "region": "Chocolate quarter",
                    "country_code": "DE"
                }
            },
            main.SCHEMA
        )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "provider": "google",
                "entity_id": 1,
                "entity_type": "accommodation",
                "address": {
                    "street": "11 Candycane",
                    "region": "Chocolate quarter",
                }
            },
            main.SCHEMA
        )


def test_hotel_validation_unknown_provider():
    """
    Tests invalidation of hotel geocoding tasks for unknown providers.
    """
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "provider": "gloogle",
                "entity_id": 1,
                "entity_type": "accommodation",
                "address": {
                    "street": "11 Candycane",
                    "region": "Chocolate quarter",
                    "country_code": "DE"
                }
            },
            main.SCHEMA
        )


def test_hotel_validation_length_country_code():
    """
    Tests invalidation of hotel geocoding tasks supplying a non valid ISO 3166-1 alpha-2 country
    code.
    """
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "provider": "google",
                "entity_id": 1,
                "entity_type": "accommodation",
                "address": {
                    "street": "11 Candycane",
                    "region": "Chocolate quarter",
                    "country_code": "DEF",
                }
            },
            main.SCHEMA
        )

    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(
            {
                "provider": "google",
                "entity_id": 1,
                "entity_type": "accommodation",
                "address": {
                    "street": "11 Candycane",
                    "region": "Chocolate quarter",
                    "country_code": "0D"
                }
            },
            main.SCHEMA
        )


def test_hotel_validation_guess_coordinate(setup_task_with_guess):
    """
    Tests validation of hotel geocoding tasks with a guess coordinate.
    """
    jsonschema.validate(setup_task_with_guess, main.SCHEMA)


def test_hotel_load(setup_task):
    hotel = main.load_entity(
        setup_task['entity_id'],
        setup_task['entity_type'],
        setup_task['address']
    )

    assert hotel.entity_id == 1
    assert hotel.entity_type == 'accommodation'
    assert hotel.street == setup_task['address']['street']
    assert hotel.country_code == setup_task['address']['country_code']
    assert hotel.name == setup_task['address']['name']
    assert hotel.district == setup_task['address']['district']
    assert hotel.city == setup_task['address']['city']
    assert hotel.region == setup_task['address']['region']
    assert hotel.country == setup_task['address']['country']
    assert hotel.postal_code == setup_task['address']['postal_code']


def test_reference_accommodation_load(setup_task):
    setup_task['entity_type'] = 'reference_accommodation'
    hotel = main.load_entity(
        setup_task['entity_id'],
        setup_task['entity_type'],
        setup_task['address']
    )

    assert hotel.entity_id == 1
    assert hotel.entity_type == 'reference_accommodation'
    assert hotel.street == setup_task['address']['street']
    assert hotel.country_code == setup_task['address']['country_code']
    assert hotel.name == setup_task['address']['name']
    assert hotel.district == setup_task['address']['district']
    assert hotel.city == setup_task['address']['city']
    assert hotel.region == setup_task['address']['region']
    assert hotel.country == setup_task['address']['country']
    assert hotel.postal_code == setup_task['address']['postal_code']


def test_candidate_accommodation_load(setup_task):
    setup_task['entity_type'] = 'candidate_accommodation'
    hotel = main.load_entity(
        setup_task['entity_id'],
        setup_task['entity_type'],
        setup_task['address']
    )

    assert hotel.entity_id == 1
    assert hotel.entity_type == 'candidate_accommodation'
    assert hotel.street == setup_task['address']['street']
    assert hotel.country_code == setup_task['address']['country_code']
    assert hotel.name == setup_task['address']['name']
    assert hotel.district == setup_task['address']['district']
    assert hotel.city == setup_task['address']['city']
    assert hotel.region == setup_task['address']['region']
    assert hotel.country == setup_task['address']['country']
    assert hotel.postal_code == setup_task['address']['postal_code']


def test_hotel_address(setup_task):
    hotel = main.load_entity(
        setup_task['entity_id'],
        setup_task['entity_type'],
        setup_task['address']
    )
    
    assert type(hotel.address) == dict


def test_hotel_address_fields(setup_task):
    hotel = main.load_entity(
        setup_task['entity_id'],
        setup_task['entity_type'],
        setup_task['address']
    )
    address = hotel.address
    
    assert 'entity_id' not in address
    assert 'entity_type' not in address
    assert address['street'] == setup_task['address']['street']
    assert address['country_code'] == setup_task['address']['country_code']
    assert address['name'] == setup_task['address']['name']
    assert address['district'] == setup_task['address']['district']
    assert address['city'] == setup_task['address']['city']
    assert address['region'] == setup_task['address']['region']
    assert address['country'] == setup_task['address']['country']
    assert address['postal_code'] == setup_task['address']['postal_code']

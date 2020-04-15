import pytest

from geocode import entity, credentials


@pytest.fixture(scope='module')
def setup_accommodation():
    return entity.Accommodation(1, **{
        "name": "Accommodation Beatles",
        "street": "30 Abbey Road",
        "district": "Camden",
        "city": "London",
        "region": "Greater London",
        "country": "United Kingdom",
        "country_code": "UK",
        "postal_code": "SW1A"
    })


@pytest.fixture(scope='module')
def setup_accommodation_incomplete():
    return entity.Accommodation(1, **{
        "name": "Accommodation Beatles",
        "street": "30 Abbey Road",
        "city": "London",
        "country_code": "UK"
    })


@pytest.fixture(scope='module')
def setup_accommodation_with_guess():
    return entity.Accommodation(1, **{
        "name": "Accommodation Beatles",
        "street": "30 Abbey Road",
        "district": "Camden",
        "city": "London",
        "region": "Greater London",
        "country": "United Kingdom",
        "country_code": "UK",
        "postal_code": "SW1A",
        "guess": {
            "longitude": 30.0,
            "latitude": -10.0
        }
    })


@pytest.fixture(scope='module')
def setup_destination():
    return entity.Destination(1, **{
        "city": "London",
        "country_code": "UK"
    })


@pytest.fixture(scope='module')
def setup_destination_with_guess():
    return entity.Destination(1, **{
        "city": "London",
        "country_code": "UK",
        "guess": {
            "longitude": 30.0,
            "latitude": -10.0
        }
    })


@pytest.fixture(scope='module')
def ssm_parameter():
    """
    Mock keys for tests.
    """
    payload = {
        'google': [
            {
                'client': 'google1',
                'client_secret': 'secret1'
            },
            {
                'client': 'google2',
                'client_secret': 'secret2'
            }
        ],
        'baidu': [
            {
                'key': 'baidu1',
                'sk': 'sk1'
            }
        ]
    }

    return payload


@pytest.fixture(autouse=True)
def reset_singletons():
    """
    Resets the KeyHandler singleton instance in case we want to mock keys differently.
    """
    credentials.Singleton._instances = {}

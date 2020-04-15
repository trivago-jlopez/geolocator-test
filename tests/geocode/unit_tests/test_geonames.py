"""
Tests the geonames geocoding services.
"""
import geocoder
import pytest

from geocode import providers, location


@pytest.fixture
def setup_key():
    return 'geonames_key'


def test_geonames_service():
    providers.Geonames()


@pytest.fixture
def setup_response(mocker):
    return [
        mocker.Mock(json={
            'lng': 34.0,
            'lat': -11.0,
            'raw': {},
            'status': 'ok'
        })
    ]


def test_geonames_call(setup_destination, setup_key, setup_response, mocker):
    service = providers.Geonames()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.geonames', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_destination)

    assert geocoder.geonames.call_count == 1
    geocoder.geonames.assert_called_with(
        location=setup_destination.city,
        country=setup_destination.country_code,
        key=setup_key
    )
    

def test_geonames_call_with_guess(setup_destination_with_guess, setup_key, setup_response, mocker):
    service = providers.Geonames()
    bbox = location.bounding_box(
        setup_destination_with_guess.guess,
        100000
    )

    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.geonames', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_destination_with_guess)

    assert geocoder.geonames.call_count == 1
    geocoder.geonames.assert_called_with(
        location=setup_destination_with_guess.city,
        country=setup_destination_with_guess.country_code,
        key=setup_key,
        north=bbox['north'],
        south=bbox['south'],
        east=bbox['east'],
        west=bbox['west']
    )
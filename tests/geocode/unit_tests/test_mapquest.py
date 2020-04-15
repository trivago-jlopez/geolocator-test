"""
Tests the tomtom geocoding services.
"""
import geocoder
import pytest

from geocode import providers, helpers, location


@pytest.fixture
def setup_key():
    return {
        'key': 'mapquest_key'
    }


@pytest.fixture
def setup_response(mocker):
    return [
        mocker.Mock(json={
            'lng': 34.0,
            'lat': -11.0,
            'raw': {},
            'status': 'ok'
        }),
        mocker.Mock(json={
            'lng': 30.0,
            'lat': -12.0,
            'raw': {},
            'status': 'ok'
        }),
        mocker.Mock(json={
            'lng': 30.0,
            'lat': -10.0,
            'raw': {},
            'status': 'ok'
        }),
        mocker.Mock(json={
            'lng': 29.0,
            'lat': -9.0,
            'raw': {},
            'status': 'ok'
        }),
        mocker.Mock(json={
            'lng': 27.0,
            'lat': -13.0,
            'raw': {},
            'status': 'ok'
        }),
    ]


def test_mapquest_service():
    providers.Mapquest()


def test_mapquest_call(setup_accommodation, setup_key, setup_response, mocker):
    service = providers.Mapquest()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.mapquest', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation)

    assert geocoder.mapquest.call_count == 1
    geocoder.mapquest.assert_called_with(
        ', '.join([
            setup_accommodation.street,
            setup_accommodation.district,
            setup_accommodation.postal_code,
            setup_accommodation.city,
            setup_accommodation.region,
            setup_accommodation.country_code
        ]),
        maxRows=100,
        key=setup_key['key']
    )


def test_mapbox_call_with_guess(setup_accommodation_with_guess, setup_key, setup_response, mocker):
    service = providers.Mapquest()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.mapquest', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation_with_guess)

    bounds = location.bounding_box(
        setup_accommodation_with_guess.guess,
        100000
    )

    bbox = [
        bounds['west'],
        bounds['south'],
        bounds['east'],
        bounds['north']
    ]

    assert geocoder.mapquest.call_count == 1
    geocoder.mapquest.assert_called_with(
        ', '.join([
            setup_accommodation_with_guess.street,
            setup_accommodation_with_guess.district,
            setup_accommodation_with_guess.postal_code,
            setup_accommodation_with_guess.city,
            setup_accommodation_with_guess.region,
            setup_accommodation_with_guess.country_code
        ]),
        bbox=bbox,
        maxRows=100,
        key=setup_key['key']
    )


def test_mapquest_iterative_addresses(setup_accommodation, setup_key, mocker):
    service = providers.Mapquest()

    # make the call fail on all address iterations
    mocker.patch('geocoder.mapquest', return_value=mocker.Mock(ok=False))
    mocker.patch.object(service, '_request_key', return_value=setup_key)

    with pytest.raises(helpers.NoResultsFoundError):
        service.geocode(setup_accommodation)

    calls = [
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.district,
                setup_accommodation.postal_code,
                setup_accommodation.city,
                setup_accommodation.region,
                setup_accommodation.country_code
            ]),
            maxRows=100,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.postal_code,
                setup_accommodation.city,
                setup_accommodation.region,
                setup_accommodation.country_code
            ]),
            maxRows=100,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.city,
                setup_accommodation.region,
                setup_accommodation.country_code
            ]),
            maxRows=100,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.city,
                setup_accommodation.country_code
            ]),
            maxRows=100,
            key=setup_key['key']
        )
    ]

    geocoder.mapquest.assert_has_calls(calls)
    assert geocoder.mapquest.call_count == len(calls)

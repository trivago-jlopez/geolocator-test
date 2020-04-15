"""
Tests the tomtom geocoding services.
"""
import geocoder
import pytest

from geocode import providers, helpers, credentials, location


@pytest.fixture
def setup_key():
    return {
        'key': 'mapbox_key'
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


def test_mapbox_service():
    providers.Mapbox()


def test_mapbox_call(setup_accommodation, setup_key, setup_response, mocker):
    service = providers.Mapbox()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.mapbox', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation)

    assert geocoder.mapbox.call_count == 1
    geocoder.mapbox.assert_called_with(
        ', '.join([
            setup_accommodation.street,
            setup_accommodation.district,
            setup_accommodation.postal_code,
            setup_accommodation.city,
            setup_accommodation.region
        ]),
        country=setup_accommodation.country_code,
        key=setup_key['key']
    )


def test_mapbox_call_with_guess(setup_accommodation_with_guess, setup_key, setup_response, mocker):
    service = providers.Mapbox()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.mapbox', return_value=m)
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

    assert geocoder.mapbox.call_count == 1
    geocoder.mapbox.assert_called_with(
        ', '.join([
            setup_accommodation_with_guess.street,
            setup_accommodation_with_guess.district,
            setup_accommodation_with_guess.postal_code,
            setup_accommodation_with_guess.city,
            setup_accommodation_with_guess.region
        ]),
        country=setup_accommodation_with_guess.country_code,
        bbox=bbox,
        key=setup_key['key']
    )


def test_mapbox_iterative_addresses(setup_accommodation, setup_key, mocker):
    service = providers.Mapbox()

    # make the call fail on all address iterations
    mocker.patch('geocoder.mapbox', return_value=mocker.Mock(ok=False))
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
                setup_accommodation.region
            ]),
            country=setup_accommodation.country_code,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.postal_code,
                setup_accommodation.city,
                setup_accommodation.region
            ]),
            country=setup_accommodation.country_code,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.city,
                setup_accommodation.region
            ]),
            country=setup_accommodation.country_code,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.city,
            ]),
            country=setup_accommodation.country_code,
            key=setup_key['key']
        )
    ]

    geocoder.mapbox.assert_has_calls(calls)
    assert geocoder.mapbox.call_count == len(calls)

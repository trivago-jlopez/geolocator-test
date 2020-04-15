"""
Tests the OpenStreetMap geocoding services.
"""
import geocoder
import pytest

from geocode import providers, helpers, location


@pytest.fixture
def setup_key():
    return {
        'key': 'osm_key'
    }


@pytest.fixture
def setup_url():
    return {
        'url': 'https://geocoding.geofabrik.de/c6d3f7c0d768419090eb35788e821a30/search'
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


def test_osm_service():
    providers.Osm()


def test_osm_call(setup_accommodation, setup_url, setup_response, mocker):
    service = providers.Osm()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.osm', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation)

    assert geocoder.osm.call_count == 1
    geocoder.osm.assert_called_with(
        None,
        street=setup_accommodation.street,
        city=setup_accommodation.city,
        postalcode=setup_accommodation.postal_code,
        state=setup_accommodation.region,
        country=setup_accommodation.country,
        countrycodes=setup_accommodation.country_code,
        method='details',
        url=setup_url['url']
    )


def test_osm_call_with_guess(setup_accommodation_with_guess, setup_url, setup_response, mocker):
    service = providers.Osm()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.osm', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation_with_guess)

    bounds = location.bounding_box(
        setup_accommodation_with_guess.guess,
        100000
    )

    bbox = '{west},{south},{east},{north}'.format(**bounds)

    assert geocoder.osm.call_count == 1
    geocoder.osm.assert_called_with(
        None,
        street=setup_accommodation_with_guess.street,
        city=setup_accommodation_with_guess.city,
        postalcode=setup_accommodation_with_guess.postal_code,
        state=setup_accommodation_with_guess.region,
        country=setup_accommodation_with_guess.country,
        countrycodes=setup_accommodation_with_guess.country_code,
        method='details',
        viewbox=bbox,
        bounded='1',
        url=setup_url['url']
    )


def test_osm_iterative_addresses(setup_accommodation, setup_url, mocker):
    service = providers.Osm()

    # make the call fail on all address iterations
    mocker.patch('geocoder.osm', return_value=mocker.Mock(ok=False))
    mocker.patch.object(service, '_request_key', return_value=setup_key)

    with pytest.raises(helpers.NoResultsFoundError):
        service.geocode(setup_accommodation)

    calls = [
        mocker.call(
            None,
            street=setup_accommodation.street,
            city=setup_accommodation.city,
            postalcode=setup_accommodation.postal_code,
            state=setup_accommodation.region,
            country=setup_accommodation.country,
            countrycodes=setup_accommodation.country_code,
            method='details',
            url=setup_url['url']
        ),
        mocker.call(
            None,
            street=setup_accommodation.street,
            city=setup_accommodation.city,
            postalcode=setup_accommodation.postal_code,
            state=setup_accommodation.region,
            countrycodes=setup_accommodation.country_code,
            method='details',
            url=setup_url['url']
        ),
        mocker.call(
            None,
            street=setup_accommodation.street,
            city=setup_accommodation.city,
            state=setup_accommodation.region,
            countrycodes=setup_accommodation.country_code,
            method='details',
            url=setup_url['url']
        ),
        mocker.call(
            None,
            street=setup_accommodation.street,
            city=setup_accommodation.city,
            countrycodes=setup_accommodation.country_code,
            method='details',
            url=setup_url['url']
        )
    ]

    geocoder.osm.assert_has_calls(calls)
    assert geocoder.osm.call_count == len(calls)

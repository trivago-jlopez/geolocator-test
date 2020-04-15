"""
Tests the tomtom geocoding services.
"""
import geocoder
import pytest

from geocode import providers, helpers


@pytest.fixture
def setup_key():
    return {
        'key': 'tomtom_key'
    }


def test_tomtom_service():
    providers.Tomtom()


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


def test_tomtom_call(setup_accommodation, setup_key, setup_response, mocker):
    service = providers.Tomtom()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.tomtom', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation)

    assert geocoder.tomtom.call_count == 1
    geocoder.tomtom.assert_called_with(
        ', '.join([
            setup_accommodation.street,
            setup_accommodation.district,
            setup_accommodation.postal_code,
            setup_accommodation.city,
            setup_accommodation.region
        ]),
        maxRows=100,
        countrySet=setup_accommodation.country_code,
        key=setup_key['key']
    )


def test_tomtom_iterative_addresses(setup_accommodation, setup_key, mocker):
    service = providers.Tomtom()

    # make the call fail on all address iterations
    mocker.patch('geocoder.tomtom', return_value=mocker.Mock(ok=False))
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
            maxRows=100,
            countrySet=setup_accommodation.country_code,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.postal_code,
                setup_accommodation.city,
                setup_accommodation.region
            ]),
            maxRows=100,
            countrySet=setup_accommodation.country_code,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.city,
                setup_accommodation.region
            ]),
            maxRows=100,
            countrySet=setup_accommodation.country_code,
            key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.city,
            ]),
            maxRows=100,
            countrySet=setup_accommodation.country_code,
            key=setup_key['key']
        )
    ]

    geocoder.tomtom.assert_has_calls(calls)
    assert geocoder.tomtom.call_count == len(calls)

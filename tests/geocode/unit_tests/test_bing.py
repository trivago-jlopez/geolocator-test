"""
Tests the tomtom geocoding services.
"""
import geocoder
import pytest

from geocode import providers, helpers, credentials


@pytest.fixture
def setup_key():
    return {
        'key': 'bing_key'
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


def test_bing_service():
    providers.Bing()


def test_bing_call(setup_accommodation, setup_key, setup_response, mocker):
    service = providers.Bing()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.bing', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation)

    assert geocoder.bing.call_count == 1
    geocoder.bing.assert_called_with(
        None,
        addressLine=setup_accommodation.street,
        adminDistrict=setup_accommodation.district,
        postalCode=setup_accommodation.postal_code,
        locality=setup_accommodation.city,
        countryRegion=setup_accommodation.country_code,
        method='details',
        maxRows=100,
        **setup_key
    )


def test_bing_iterative_addresses(setup_accommodation, setup_key, mocker):
    service = providers.Bing()

    # make the call fail on all address iterations
    mocker.patch('geocoder.bing', return_value=mocker.Mock(ok=False))
    mocker.patch.object(service, '_request_key', return_value=setup_key)

    with pytest.raises(helpers.NoResultsFoundError):
        service.geocode(setup_accommodation)

    calls = [
        mocker.call(
            None,
            addressLine=setup_accommodation.street,
            adminDistrict=setup_accommodation.district,
            postalCode=setup_accommodation.postal_code,
            locality=setup_accommodation.city,
            countryRegion=setup_accommodation.country_code,
            method='details',
            maxRows=100,
            key=setup_key['key']
        ),
        mocker.call(
            None,
            addressLine=setup_accommodation.street,
            postalCode=setup_accommodation.postal_code,
            locality=setup_accommodation.city,
            countryRegion=setup_accommodation.country_code,
            method='details',
            maxRows=100,
            key=setup_key['key']
        ),
        mocker.call(
            None,
            addressLine=setup_accommodation.street,
            locality=setup_accommodation.city,
            countryRegion=setup_accommodation.country_code,
            method='details',
            maxRows=100,
            key=setup_key['key']
        )
    ]

    geocoder.bing.assert_has_calls(calls)
    assert geocoder.bing.call_count == len(calls)

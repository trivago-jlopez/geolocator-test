"""
Tests the tomtom geocoding services.
"""
import geocoder
import pytest

from geocode import providers, helpers, credentials

@pytest.fixture
def setup_key():
    return {
        'key': 'arcgis_key'
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


def test_arcgis_service():
    providers.Arcgis()


def test_arcgis_call(setup_accommodation, setup_key, setup_response, mocker):
    service = providers.Arcgis()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.arcgis', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation)

    assert geocoder.arcgis.call_count == 1
    geocoder.arcgis.assert_called_with(
        ', '.join([
            setup_accommodation.street,
            setup_accommodation.district,
            setup_accommodation.postal_code,
            setup_accommodation.city,
            setup_accommodation.region,
            setup_accommodation.country_code
        ]),
        maxRows=100,
        #key=setup_key['key']
    )


def test_arcgis_iterative_addresses(setup_accommodation, setup_key, mocker):
    service = providers.Arcgis()

    # make the call fail on all address iterations
    mocker.patch('geocoder.arcgis', return_value=mocker.Mock(ok=False))
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
            #key=setup_key['key']
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
            #key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.city,
                setup_accommodation.region,
                setup_accommodation.country_code
            ]),
            maxRows=100,
            #key=setup_key['key']
        ),
        mocker.call(
            ', '.join([
                setup_accommodation.street,
                setup_accommodation.city,
                setup_accommodation.country_code
            ]),
            maxRows=100,
            #key=setup_key['key']
        )
    ]

    geocoder.arcgis.assert_has_calls(calls)
    assert geocoder.arcgis.call_count == len(calls)


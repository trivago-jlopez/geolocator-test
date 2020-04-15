"""
Tests the tomtom geocoding services.
"""
import geocoder
import pytest

from geocode import providers, helpers, credentials


@pytest.fixture
def setup_key():
    return {
        'app_id': 'here_id',
        'app_code': 'here_code'
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


def test_here_service():
    providers.Here()


def test_here_call(setup_accommodation, setup_key, setup_response, mocker):
    service = providers.Here()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.here', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation)

    assert geocoder.here.call_count == 1
    geocoder.here.assert_called_with(
        None,
        street=setup_accommodation.street,
        district=setup_accommodation.district,
        postalcode=setup_accommodation.postal_code,
        city=setup_accommodation.city,
        state=setup_accommodation.region,
        country=setup_accommodation.country_code,
        maxRows=100,
        app_id=setup_key['app_id'],
        app_code=setup_key['app_code']
    )


def test_here_call_with_guess(setup_accommodation_with_guess, setup_key, setup_response, mocker):
    service = providers.Here()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.here', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation_with_guess)

    assert geocoder.here.call_count == 1
    geocoder.here.assert_called_with(
        None,
        street=setup_accommodation_with_guess.street,
        district=setup_accommodation_with_guess.district,
        postalcode=setup_accommodation_with_guess.postal_code,
        city=setup_accommodation_with_guess.city,
        state=setup_accommodation_with_guess.region,
        country=setup_accommodation_with_guess.country_code,
        prox='{latitude},{longitude},100000'.format(**setup_accommodation_with_guess.guess),
        maxRows=100,
        app_id=setup_key['app_id'],
        app_code=setup_key['app_code']
    )


def test_here_iterative_addresses(setup_accommodation, setup_key, mocker):
    service = providers.Here()

    # make the call fail on all address iterations
    mocker.patch('geocoder.here', return_value=mocker.Mock(ok=False))
    mocker.patch.object(service, '_request_key', return_value=setup_key)

    with pytest.raises(helpers.NoResultsFoundError):
        service.geocode(setup_accommodation)

    calls = [
        mocker.call(
            None,
            street=setup_accommodation.street,
            district=setup_accommodation.district,
            postalcode=setup_accommodation.postal_code,
            city=setup_accommodation.city,
            state=setup_accommodation.region,
            country=setup_accommodation.country_code,
            maxRows=100,
            **setup_key
        ),
        mocker.call(
            None,
            street=setup_accommodation.street,
            postalcode=setup_accommodation.postal_code,
            city=setup_accommodation.city,
            state=setup_accommodation.region,
            country=setup_accommodation.country_code,
            maxRows=100,
            **setup_key
        ),
        mocker.call(
            None,
            street=setup_accommodation.street,
            city=setup_accommodation.city,
            state=setup_accommodation.region,
            country=setup_accommodation.country_code,
            maxRows=100,
            **setup_key
        ),
        mocker.call(
            None,
            street=setup_accommodation.street,
            city=setup_accommodation.city,
            country=setup_accommodation.country_code,
            maxRows=100,
            **setup_key
        )
    ]

    geocoder.here.assert_has_calls(calls)
    assert geocoder.here.call_count == len(calls)

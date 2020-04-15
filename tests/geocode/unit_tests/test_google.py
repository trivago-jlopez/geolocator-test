"""
Tests the Google geocoding services.
"""
import geocoder
import pytest

from geocode import providers, helpers, credentials, location


@pytest.fixture
def setup_key():
    return {
        'client': 'mock_key',
        'client_secret': 'mock_secret'
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


def test_google_service():
    providers.Google()


def test_google_call(setup_accommodation, setup_key, setup_response, mocker):
    service = providers.Google()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.google', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation)

    assert geocoder.google.call_count == 1
    geocoder.google.assert_called_with(
        setup_accommodation.street,
        components='administrative_area:{administrative_area}|country:{country_code}|locality:{city}|postal_code:{postal_code}'.format(
            city=setup_accommodation.city,
            postal_code=setup_accommodation.postal_code,
            administrative_area=setup_accommodation.region,
            country_code=setup_accommodation.country_code
        ),
        client=setup_key['client'],
        client_secret=setup_key['client_secret']
    )


def test_google_call_with_guess(setup_accommodation_with_guess, setup_key, setup_response, mocker):
    service = providers.Google()

    # make the call succeed on the first try
    m = mocker.MagicMock()
    m.ok = True
    m.__iter__.return_value = setup_response
    mocker.patch('geocoder.google', return_value=m)
    mocker.patch.object(service, '_request_key', return_value=setup_key)
    service.geocode(setup_accommodation_with_guess)

    bbox = location.bounding_box(
        setup_accommodation_with_guess.guess,
        100000
    )

    bounds = '{south},{west}|{north},{east}'.format(**bbox)

    assert geocoder.google.call_count == 1
    geocoder.google.assert_called_with(
        setup_accommodation_with_guess.street,
        components='administrative_area:{administrative_area}|country:{country_code}|locality:{city}|postal_code:{postal_code}'.format(
            city=setup_accommodation_with_guess.city,
            postal_code=setup_accommodation_with_guess.postal_code,
            administrative_area=setup_accommodation_with_guess.region,
            country_code=setup_accommodation_with_guess.country_code
        ),
        bounds=bounds,
        client=setup_key['client'],
        client_secret=setup_key['client_secret']
    )


def test_google_iterative_addresses(setup_accommodation, setup_key, mocker):
    """
    Test successive Google API calls. Check that no duplicates calls are made and that at the end a
    error is thrown indicating no results.
    """
    service = providers.Google()

    # make the call fail on all address iterations
    mocker.patch('geocoder.google', return_value=mocker.Mock(ok=False))
    mocker.patch.object(service, '_request_key', return_value=setup_key)

    with pytest.raises(helpers.NoResultsFoundError):
        service.geocode(setup_accommodation)

    calls = [
        mocker.call(
            setup_accommodation.street,
            components='administrative_area:{administrative_area}|country:{country_code}|locality:{city}|postal_code:{postal_code}'.format(
                city=setup_accommodation.city,
                postal_code=setup_accommodation.postal_code,
                administrative_area=setup_accommodation.region,
                country_code=setup_accommodation.country_code
            ),
            client=setup_key['client'],
            client_secret=setup_key['client_secret']
        ),
        mocker.call(
            setup_accommodation.street,
            components='administrative_area:{administrative_area}|country:{country_code}|locality:{city}'.format(
                city=setup_accommodation.city,
                administrative_area=setup_accommodation.region,
                country_code=setup_accommodation.country_code
            ),
            client=setup_key['client'],
            client_secret=setup_key['client_secret']
        ),
        mocker.call(
            setup_accommodation.street,
            components='country:{country_code}|locality:{city}'.format(
                city=setup_accommodation.city,
                country_code=setup_accommodation.country_code
            ),
            client=setup_key['client'],
            client_secret=setup_key['client_secret']
        )
    ]

    geocoder.google.assert_has_calls(calls)
    assert geocoder.google.call_count == len(calls)


def test_google_incomplete_iterative_addresses(setup_accommodation_incomplete, setup_key, mocker):
    """
    Test successive Google API calls. Check that no duplicates calls are made and that at the end a
    error is thrown indicating no results.
    """
    service = providers.Google()

    # make the call fail on all address iterations
    mocker.patch('geocoder.google', return_value=mocker.Mock(ok=False))
    mocker.patch.object(service, '_request_key', return_value=setup_key)

    with pytest.raises(helpers.NoResultsFoundError):
        service.geocode(setup_accommodation_incomplete)

    calls = [
        mocker.call(
            setup_accommodation_incomplete.street,
            components='country:{country_code}|locality:{city}'.format(
                city=setup_accommodation_incomplete.city,
                country_code=setup_accommodation_incomplete.country_code
            ),
            client=setup_key['client'],
            client_secret=setup_key['client_secret']
        )
    ]

    geocoder.google.assert_has_calls(calls)
    assert geocoder.google.call_count == len(calls)


@pytest.fixture
def mocked_key_handler(ssm_parameter, mocker):
    mocker.patch.object(credentials.KeyHandler, '_retrieve_parameter', return_value=ssm_parameter) 


def test_google_rate_limiting(setup_accommodation, mocked_key_handler, mocker):
    service = providers.Google()

    # make the call fail due to rate limiting
    mocker.patch('geocoder.google', return_value=mocker.Mock(
        ok=False,
        error='OVER_QUERY_LIMIT',
        status='OVER_QUERY_LIMIT'
    ))

    with pytest.raises(helpers.QuotaExhaustedError):
        service.geocode(setup_accommodation)

    geocoder.google.call_count == 2


def test_google_failure(setup_accommodation, mocked_key_handler, mocker):
    service = providers.Google()

    # make the call fail due to rate limiting
    mocker.patch('geocoder.google', return_value=mocker.Mock(
        ok=False,
        error='UNKNOWN_ERROR',
        status='UNKNOWN_ERROR'
    ))

    with pytest.raises(helpers.FailedRequestError):
        service.geocode(setup_accommodation)

    geocoder.google.call_count == 1

    mocker.patch('geocoder.google', return_value=mocker.Mock(
        ok=False,
        error='REQUEST_DENIED',
        status='REQUEST_DENIED'
    ))

    with pytest.raises(helpers.FailedRequestError):
        service.geocode(setup_accommodation)

    geocoder.google.call_count == 1


def test_google_invalid_request(setup_accommodation, mocked_key_handler, mocker):
    service = providers.Google()

    # make the call fail due to rate limiting
    mocker.patch('geocoder.google', return_value=mocker.Mock(
        ok=False,
        error='INVALID_REQUEST',
        status='INVALID_REQUEST'
    ))

    with pytest.raises(helpers.InvalidRequestError):
        service.geocode(setup_accommodation)

    geocoder.google.call_count == 1

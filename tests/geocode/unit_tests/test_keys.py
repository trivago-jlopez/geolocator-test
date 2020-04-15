"""
Tests setup and cycling through API keys to simulate switching keys in a cyclical manner when one
key for a provider reaches its quota.
"""
import pytest

from geocode import credentials


@pytest.fixture
def mocked_key_handler(ssm_parameter, mocker):
    mocker.patch.object(credentials.KeyHandler, '_retrieve_parameter', return_value=ssm_parameter) 


def test_keys_initialize(mocked_key_handler):
    """
    Tests the initialization of active keys, which should be set to the first key per provider.
    """
    key_handler = credentials.KeyHandler("/mysterious/key", "/some/id")
    import logging
    logging.warning(type(key_handler))

    assert key_handler.get_key('google') == {
        'client': 'google1',
        'client_secret': 'secret1'
    }

    assert key_handler.get_key('baidu') == {
        'key': 'baidu1',
        'sk': 'sk1'
    }

    with pytest.raises(KeyError):
        key_handler.get_key('here')


def test_keys_cycle(mocked_key_handler):
    """
    Tests key iteration, which should be cyclical.
    """
    key_handler = credentials.KeyHandler("/mysterious/key", "/some/id")

    key_handler.cycle_key('google')
    assert key_handler.get_key('google') == {
        'client': 'google2',
        'client_secret': 'secret2'
    }

    # rotation, back to first key
    key_handler.cycle_key('google')
    assert key_handler.get_key('google') == {
        'client': 'google1',
        'client_secret': 'secret1'
    }

    key_handler.cycle_key('baidu')
    assert key_handler.get_key('baidu') == {
        'key': 'baidu1',
        'sk': 'sk1'
    }

    with pytest.raises(KeyError):
        key_handler.cycle_key('here')
    with pytest.raises(KeyError):
        key_handler.get_key('here')

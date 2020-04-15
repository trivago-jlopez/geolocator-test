from unittest import mock
import pytest

from consolidator import candidate, entity
from consolidator.utils import fetcher


class TestEntity:
    @pytest.fixture
    def fetcher_stub(self):
        stub = mock.Mock(spec_set=fetcher.Fetcher)
        stub.fetch_candidates.return_value = [
            dict(
                provider='google',
                longitude=34.4532,
                latitude=-71.9925
            ),
            dict(
                provider='tomtom',
                longitude=34.4532,
                latitude=-71.9925
            ),
        ]

        return stub

    def test_initialize(self):
        entity.Entity(1, 'accommodation')

    def test_key(self):
        key = entity.Entity(1, 'accommodation').key
        assert key == 'accommodation:1'

    def test_to_dict(self):
        entity_dict = entity.Entity(1, 'accommodation').to_dict()
        assert isinstance(entity_dict, dict)
        assert len(entity_dict) == 2

    def test_get_candidates(self, fetcher_stub):
        entity_obj = entity.Accommodation(1, fetcher_stub)
        candidates = entity_obj.candidates

        assert len(candidates) == 2
        for i in candidates:
            assert isinstance(i, candidate.AccommodationCandidate)

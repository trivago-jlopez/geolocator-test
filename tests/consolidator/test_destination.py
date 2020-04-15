import os

from unittest import mock
import pytest

from consolidator import entity
from consolidator.utils import fetcher


@pytest.mark.skip(reason="Not relevant to Source")
class TestDestinationConsolidation:
    @pytest.fixture
    def fetcher_stub(self):
        stub = mock.Mock(spec_set=fetcher.Fetcher)

        return stub

    @pytest.fixture
    def candidates_geocoders(self):
        return [
            dict(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="APPROXIMATE",
                confidence="7.0",
                quality="locality",
                country_code="US"
            ),
            dict(
                provider="geonames",
                longitude=45.1192,
                latitude=-23.4723,
                country_code="US"
            ),
            dict(
                provider="osm",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy=0.1988285649,
                confidence="1",
                quality= "city",
                country_code="US"
            )
        ]

    def test_consolidate_destination(self, fetcher_stub, candidates_geocoders, monkeypatch):
        with monkeypatch.context() as m:
            m.setitem(os.environ, 'ENVIRONMENT', 'test')

            fetcher_stub.fetch_candidates.return_value = [*candidates_geocoders,
                dict(
                    provider="consolidator_" + os.environ['ENVIRONMENT'],
                    longitude=45.2202,
                    latitude=23.0091,
                    score=0.5,
                    city="Amsterdam",
                    country_code="US"
                )
            ]

            entity_obj = entity.Destination(1, fetcher_stub)
            winner = entity_obj.consolidated

            assert not winner

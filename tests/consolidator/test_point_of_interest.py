import os

from unittest import mock
import pytest

from consolidator import entity
from consolidator.utils import fetcher


@pytest.mark.skip(reason="Not relevant for Source")
class TestPointOfInterestConsolidation:
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
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political",
                country_code="US"
            ),
            dict(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="10.0",
                quality= "Point Address",
                country_code="US"
            ),
            dict(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality= "0.9",
                country_code="US"
            )
        ]

    def test_consolidate_point_of_interest(self, fetcher_stub, candidates_geocoders, monkeypatch):
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

            entity_obj = entity.PointOfInterest(1, fetcher_stub)
            winner = entity_obj.consolidated

            assert not winner

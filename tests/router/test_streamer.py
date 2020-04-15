import importlib

from unittest import mock
import pytest

from router import streamer
from router.utils import Stasher


class TestStreamer:
    @pytest.fixture
    def stasher_stub(self):
        stub = mock.Mock(spec=Stasher)

        return stub

    def test_initialize(self, stasher_stub):
        streamer.Streamer(stasher_stub)

    def test_initialize_candidate_geo_data(self):
        result = streamer.CandidateGeoData(
            candidate_id=1,
            longitude=0.1,
            latitude=0.2,
            locality_id=123,
            country_id=56,
            valid_geo_point=False
        )

        assert result.candidate_id == 1
        assert result.longitude == 0.1
        assert result.latitude == 0.2
        assert result.locality_id == 123
        assert result.locality_ns == 200
        assert result.administrative_division_id == None
        assert result.administrative_division_ns == None
        assert result.country_id == 56
        assert result.country_ns == 200
        assert result.valid_geo_point is False

    def test_parse_value(self):
        result = streamer.CandidateGeoData(
            candidate_id=1,
            longitude=0.1,
            latitude=0.2,
            locality_id=123,
            country_id=56,
            valid_geo_point=False
        )

        msg = getattr(
            importlib.import_module(result.definition + '_pb2'),
            result.definition.split('.')[-1]
        )()

        result.parse_value(msg, 'longitude')

        assert msg.longitude == 0.1

    def test_parse_dict(self):
        result = streamer.CandidateGeoData(
            candidate_id=1,
            longitude=0.1,
            latitude=0.2,
            locality_id=123,
            country_id=56,
            valid_geo_point=False
        )

        msg = getattr(
            importlib.import_module(result.definition + '_pb2'),
            result.definition.split('.')[-1]
        )()

        result.parse_dict(msg)

        assert msg.key.candidate_id == 1
        assert msg.longitude == 0.1


    def test_serialize(self):
        result = streamer.CandidateGeoData(
            candidate_id=1,
            longitude=0.1,
            latitude=0.2,
            locality_id=123,
            country_id=56,
            valid_geo_point=False
        )

        protobuf = result.serialize()
        assert isinstance(protobuf, bytes)

    def test_put_record(self, stasher_stub):
        record = dict(
            entity='candidate_accommodation:1',
            longitude=0.1,
            latitude=0.2,
            locality_id=123,
            country_id=56,
            valid_geo_point=False
        )

        streamer_obj = streamer.Streamer(stasher_stub)
        streamer_obj.put_record(record)

        assert len(streamer_obj.candidates) == 1

    def test_stream(self):
        pass

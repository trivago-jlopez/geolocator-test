from unittest import mock
import pytest

from router import entity
from router.utils import country_mapper


class TestEntity:
    @pytest.fixture
    def clear_singleton(self):
        country_mapper.Singleton._instances = {}

    @pytest.fixture
    def country_mapper_stub(self):
        stub = mock.Mock(spec=country_mapper.CountryMapper)
        stub.is_valid_country_code.return_value = False
        stub.map_destination_id.return_value = 'GB'
        stub.map_name.return_value = 'GB'
        stub.map_iso_3166_3.return_value = 'GB'

        return stub

    def test_candidate_accommodation_initialize(self):
        obj = entity.CandidateAccommodation(candidate_id=1)
        obj.entity_type == 'candidate_accommodation'

    def test_candidate_accommodation_as_address(self):
        obj = entity.CandidateAccommodation(
            candidate_id=1,
            name='Hotel Hell',
            street='Abbey Road 32',
            postal_code='NW8',
            city='London',
            region='Greater London',
            country='England',
            longitude=0.1,
            latitude=0.2,
            flag={
                'is_valid_geocode': False
            }
        )

        skeleton = obj.as_address()

        assert isinstance(skeleton, dict)
        assert skeleton['entity_id'] == 1
        assert skeleton['entity_type'] == 'candidate_accommodation'
        assert skeleton['address'] == obj.address

    def test_candidate_accommodation_as_consolidation(self, country_mapper_stub):
        obj = entity.CandidateAccommodation(
            candidate_id=1,
            name='Hotel Hell',
            street='Abbey Road 32',
            postal_code='NW8',
            district='Lava District',
            city='London',
            region='Greater London',
            country='England',
            longitude=0.1,
            latitude=0.2,
            flag={
                'is_valid_geocode': False
            },
            country_mapper=country_mapper_stub
        )

        assert obj.as_consolidation() == {
            'entity': 'candidate_accommodation:1',
            'entity_id': 1,
            'entity_type': 'candidate_accommodation',
            'longitude': 0.1,
            'latitude': 0.2,
            'score': 1.0,
            'meta': {
                'city': 'London',
                'country_code': 'GB'
            }
        }


    def test_candidate_accommodation_to_dict(self):
        obj = entity.CandidateAccommodation(
            candidate_id=1,
            name='Hotel Hell',
            street='Abbey Road 32',
            postal_code='NW8',
            district='Lava District',
            city='London',
            region='Greater London',
            country='England',
            longitude=0.1,
            latitude=0.2,
            flag={
                'is_valid_geocode': False
            }
        )

        assert obj.to_dict() == {
            'entity_id': 1,
            'entity_type': 'candidate_accommodation',
            'name': 'Hotel Hell',
            'longitude': 0.1,
            'latitude': 0.2
        }

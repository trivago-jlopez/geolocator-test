from consolidator import candidate


class TestCandidate:
    def test_initialize(self):
        candidate.AccommodationCandidate('google', longitude=0.0, latitude=0.0)

    def test_initialize_from_dict(self):
        data = dict(
            provider='google',
            longitude=10.5326,
            latitude=-50.9551,
            accuracy=5,
            confidence='9.0',
            quality='roofTop',
            score=10.0,
            city='Boston',
            country_code='US'
        )

        candidate_obj = candidate.AccommodationCandidate(**data)

        assert candidate_obj.provider == 'google'
        assert candidate_obj.longitude == 10.5326
        assert candidate_obj.latitude == -50.9551
        assert candidate_obj.accuracy == 5
        assert candidate_obj.confidence == '9.0'
        assert candidate_obj.quality == 'roofTop'
        assert candidate_obj.score == 10.0
        assert candidate_obj.city == 'Boston'
        assert candidate_obj.country_code == 'US'

    def test_to_dict(self):
        candidate_obj = candidate.AccommodationCandidate(
            provider='google',
            longitude=10.5326,
            latitude=-50.9551,
            accuracy=5,
            confidence='9.0',
            quality='roofTop',
            score=10.0,
            city='Boston',
            country_code='US'
        )

        candidate_dict = candidate_obj.to_dict()

        assert isinstance(candidate_dict, dict)
        assert len(candidate_dict) == 5
        assert candidate_dict['provider'] == 'google'
        assert candidate_dict['longitude'] == 10.5326
        assert candidate_dict['latitude'] == -50.9551
        assert candidate_dict['city'] == 'Boston'
        assert candidate_dict['country_code'] == 'US'
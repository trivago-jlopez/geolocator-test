import decimal

import pytest

from consolidator import candidate
from consolidator.strategy import ruleset


class TestRuleset:
    @pytest.fixture
    def ruleset_definition_no_filter(self):
        return {
            "schema": {
                "fields": [
                    "provider",
                    "accuracy",
                    "confidence",
                    "quality",
                    "score"
                ],
                "required": [
                    "provider"
                ]
            },
            "rules": [
                {
                    "provider": "google",
                    "accuracy": "ROOFTOP",
                    "confidence": "9.0",
                    "quality" : "political"
                },
                {
                    "provider": "tomtom",
                    "confidence": "10.0",
                    "quality" : "Point Address"
                },
                {
                    "provider": "google",
                    "accuracy": "ROOFTOP",
                    "confidence": "8.0",
                    "quality" : "political"
                }
            ]
        } 

    @pytest.fixture
    def ruleset_definition_with_filter(self):
        return {
            "schema": {
                "fields": [
                    "provider",
                    "accuracy",
                    "confidence",
                    "quality",
                    "score",
                    "country_code"
                ],
                "required": [
                    "provider"
                ],
                "filter": [
                    "country_code"
                ]
            },
            "rules": [
                {
                    "provider": "google",
                    "accuracy": "ROOFTOP",
                    "confidence": "9.0",
                    "quality" : "political"
                },
                {
                    "provider": "tomtom",
                    "confidence": "10.0",
                    "quality" : "Point Address"
                },
                {
                    "provider": "google",
                    "accuracy": "ROOFTOP",
                    "confidence": "8.0",
                    "quality" : "political"
                },
                {
                    "provider": "mapbox",
                    "accuracy": "interpolated",
                    "quality" : "0.9",
                    "country_code": "US"
                },
                {
                    "provider": "tomtom",
                    "confidence": "10.0",
                    "quality" : "Point Address",
                    "country_code": "US"
                }
            ]
        }

    def test_initialization(self):
        ruleset.Ruleset(None)

    def test_initialization_no_filter(self, ruleset_definition_no_filter):
        ruleset.Ruleset(ruleset_definition_no_filter)

    def test_initialization_with_filter(self, ruleset_definition_with_filter):
        ruleset.Ruleset(ruleset_definition_with_filter)

    @pytest.fixture
    def candidate_no_country(self):
        return candidate.AccommodationCandidate(
            provider='google',
            longitude=0.0,
            latitude=0.0,
            accuracy='ROOFTOP',
            quality=decimal.Decimal('9.0')
        )

    @pytest.fixture
    def candidate_with_country(self):
        return candidate.AccommodationCandidate(
            provider='google',
            longitude=0.0,
            latitude=0.0,
            accuracy='ROOFTOP',
            quality=decimal.Decimal('9.0'),
            country_code='US'
        )

    def test_is_match(self, ruleset_definition_no_filter, candidate_no_country):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_no_filter)

        rule = {
            'provider': 'google',
            'quality': 9.0,
            'accuracy': 'ROOFTOP'
        }

        assert ruleset_obj.is_match(rule, candidate_no_country)

    def test_is_match_filter(self, ruleset_definition_with_filter, candidate_no_country):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        rule = {
            'provider': 'google',
            'quality': 9.0,
            'accuracy': 'ROOFTOP',
            'country_code': 'US'
        }

        assert not ruleset_obj.is_match(rule, candidate_no_country)

    def test_is_match_filter_matching_values(self, ruleset_definition_with_filter, candidate_with_country):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        rule = {
            'provider': 'google',
            'quality': 9.0,
            'accuracy': 'ROOFTOP',
            'country_code': 'US'
        }

        assert ruleset_obj.is_match(rule, candidate_with_country)

    def test_is_match_filter_mismatching_values(self, ruleset_definition_with_filter, candidate_with_country):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        rule = {
            'provider': 'google',
            'quality': 9.0,
            'accuracy': 'ROOFTOP',
            'country_code': 'BE'
        }

        assert not ruleset_obj.is_match(rule, candidate_with_country)

    def test_is_match_type_conversion(self, candidate_no_country):
        ruleset_obj = ruleset.Ruleset(None)

        rule = {
            'provider': 'google',
            'quality': '9',
            'accuracy': 'ROOFTOP'
        }

        assert ruleset_obj.is_match(rule, candidate_no_country)

    def test_is_match_type_conversion_integer_lte(self, candidate_no_country):
        ruleset_obj = ruleset.Ruleset(None)

        rule = {
            'provider': 'google',
            'quality': '8.9',
            'accuracy': 'ROOFTOP'
        }

        assert ruleset_obj.is_match(rule, candidate_no_country)

    def test_is_match_mismatch_provider(self, candidate_no_country):
        ruleset_obj = ruleset.Ruleset(None)

        rule = {
            'provider': 'google_places',
            'quality': 9.0,
            'accuracy': 'ROOFTOP'
        }

        assert not ruleset_obj.is_match(rule, candidate_no_country)
        
    def test_is_match_mismatch_quality_criteria(self, candidate_no_country):
        ruleset_obj = ruleset.Ruleset(None)

        rule = {
            'provider': 'google',
            'quality': 8.0,
            'accuracy': 'ROOFTOP'
        }

        assert ruleset_obj.is_match(rule, candidate_no_country)

        rule = {
            'provider': 'google',
            'quality': 9.2,
            'accuracy': 'ROOFTOP'
        }

        assert not ruleset_obj.is_match(rule, candidate_no_country)

    def test_is_match_missing_quality_criteria(self, candidate_no_country):
        ruleset_obj = ruleset.Ruleset(None)

        rule = {
            'provider': 'google',
            'quality': 9.0,
            'accuracy': 'ROOFTOP',
            'score': 100
        }

        assert not ruleset_obj.is_match(rule, candidate_no_country)

    def test_is_match_null_value(self, candidate_no_country):
        ruleset_obj = ruleset.Ruleset(None)

        rule = {
            'provider': 'google',
            'quality': 9.0,
            'accuracy': 'ROOFTOP',
            'score': None
        }

        assert ruleset_obj.is_match(rule, candidate_no_country)

        assert ruleset_obj.is_match(rule, candidate.AccommodationCandidate(
            provider='google',
            longitude=0.0,
            latitude=0.0,
            accuracy='ROOFTOP',
            quality=9.0,
            score=100
        ))

    @pytest.fixture
    def candidates_unanimous(self):
        return [
            candidate.AccommodationCandidate(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political",
                country_code="US"
            ),
            candidate.AccommodationCandidate(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="10.0",
                quality= "Point Address",
                country_code="US"
            ),
            candidate.AccommodationCandidate(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality= "0.9",
                country_code="US"
            )
        ]

    @pytest.fixture
    def candidates_nulls(self):
        return [
            candidate.AccommodationCandidate(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political"
            ),
            candidate.AccommodationCandidate(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="10.0",
                quality="Point Address",
                country_code="US"
            ),
            candidate.AccommodationCandidate(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality="0.9",
                country_code="US"
            )
        ]

    @pytest.fixture
    def candidates_dissenting(self):
        return [
            candidate.AccommodationCandidate(
                provider="google",
                longitude=45.8941,
                latitude=-23.9191,
                accuracy="ROOFTOP",
                confidence="8.0",
                quality="political",
                country_code="BE"
            ),
            candidate.AccommodationCandidate(
                provider="tomtom",
                longitude=45.1192,
                latitude=-23.4723,
                confidence="10.0",
                quality="Point Address",
                country_code="US"
            ),
            candidate.AccommodationCandidate(
                provider="mapbox",
                longitude=45.5912,
                latitude=-23.9220,
                accuracy="interpolated",
                quality="0.9",
                country_code="BE"
            )
        ]

    def test_unify_fields_empty(self, ruleset_definition_no_filter, candidates_unanimous):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_no_filter)

        assert len(ruleset_obj._filter_fields) == 0

        filter_dict = ruleset_obj.unify_fields(
            ruleset_obj._filter_fields,
            candidates_unanimous
        )
        assert isinstance(filter_dict, dict)
        assert len(filter_dict) == 0

    def test_unify_fields_unanimous(self, ruleset_definition_with_filter, candidates_unanimous):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        assert len(ruleset_obj._filter_fields) == 1

        filter_dict = ruleset_obj.unify_fields(
            ruleset_obj._filter_fields,
            candidates_unanimous
        )
        assert len(filter_dict) == 1
        assert filter_dict['country_code'] == 'US'

    def test_unify_fields_nulls(self, ruleset_definition_with_filter, candidates_nulls):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        assert len(ruleset_obj._filter_fields) == 1

        filter_dict = ruleset_obj.unify_fields(
            ruleset_obj._filter_fields,
            candidates_nulls
        )
        assert len(filter_dict) == 1
        assert filter_dict['country_code'] == 'US'

    def test_unify_fields_dissenting(self, ruleset_definition_with_filter, candidates_dissenting):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        assert len(ruleset_obj._filter_fields) == 1

        filter_dict = ruleset_obj.unify_fields(
            ruleset_obj._filter_fields,
            candidates_dissenting
        )
        assert len(filter_dict) == 1
        assert filter_dict['country_code'] is None

    def test_obtain_rules_filter_default(self, ruleset_definition_with_filter):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        rules = ruleset_obj.obtain_rules({ 'country_code': None })
        assert rules
        assert len(rules) == 3

    def test_obtain_rules_filter(self, ruleset_definition_with_filter):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        rules = ruleset_obj.obtain_rules({ 'country_code': 'US' })
        assert rules
        assert len(rules) == 2

    def test_obtain_default_rules(self, ruleset_definition_with_filter):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        rules = ruleset_obj.obtain_default_rules()
        assert rules
        assert len(rules) == 3

    def test_rank_candidate(self, ruleset_definition_with_filter, candidates_unanimous):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        rules = ruleset_obj.obtain_default_rules()

        assert ruleset_obj.rank_candidate(candidates_unanimous[0], rules) == 3
        assert ruleset_obj.rank_candidate(candidates_unanimous[1], rules) == 2
        assert ruleset_obj.rank_candidate(candidates_unanimous[2], rules) is None

        rules = ruleset_obj.obtain_rules({ 'country_code': 'US' })

        assert ruleset_obj.rank_candidate(candidates_unanimous[0], rules) is None
        assert ruleset_obj.rank_candidate(candidates_unanimous[1], rules) == 2
        assert ruleset_obj.rank_candidate(candidates_unanimous[2], rules) == 1

    def test_rank_candidate_filter(self, ruleset_definition_with_filter, candidates_dissenting):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        rules = ruleset_obj.obtain_default_rules()

        assert ruleset_obj.rank_candidate(candidates_dissenting[0], rules) == 3
        assert ruleset_obj.rank_candidate(candidates_dissenting[1], rules) == 2
        assert ruleset_obj.rank_candidate(candidates_dissenting[2], rules) is None

        rules = ruleset_obj.obtain_rules({ 'country_code': 'US' })

        assert ruleset_obj.rank_candidate(candidates_dissenting[0], rules) is None
        assert ruleset_obj.rank_candidate(candidates_dissenting[1], rules) == 2
        assert ruleset_obj.rank_candidate(candidates_dissenting[2], rules) is None

        # there are no rules specific to BE, so default rules are used
        rules = ruleset_obj.obtain_rules({ 'country_code': 'BE' })

        assert ruleset_obj.rank_candidate(candidates_dissenting[0], rules) == 3
        assert ruleset_obj.rank_candidate(candidates_dissenting[1], rules) == 2
        assert ruleset_obj.rank_candidate(candidates_dissenting[2], rules) is None

    def test_rank_empty(self, candidates_unanimous):
        ruleset_obj = ruleset.Ruleset(None)

        finalists = ruleset_obj.rank(candidates_unanimous)

        assert isinstance(finalists, list)
        assert len(finalists) == 0

    def test_rank_default(self, ruleset_definition_with_filter, candidates_dissenting):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        # candidates have dissenting opinions, default rules are used
        finalists = ruleset_obj.rank(candidates_dissenting)

        assert isinstance(finalists, list)
        assert len(finalists) == 2

        for finalist in finalists:
            assert isinstance(finalist, dict)
            assert 'rank' in finalist and isinstance(finalist['rank'], int)
            assert 'finalist' in finalist
            assert finalist['finalist'].provider in ('google', 'tomtom')

    def test_rank_filter(self, ruleset_definition_with_filter, candidates_unanimous):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        # rules for US are used
        finalists = ruleset_obj.rank(candidates_unanimous)

        assert isinstance(finalists, list)
        assert len(finalists) == 2

        for finalist in finalists:
            assert isinstance(finalist, dict)
            assert 'rank' in finalist and isinstance(finalist['rank'], int)
            assert 'finalist' in finalist
            assert finalist['finalist'].provider in ('mapbox', 'tomtom')

    def test_rank_filter_with_nulls(self, ruleset_definition_with_filter, candidates_nulls):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        # rules for US are used
        finalists = ruleset_obj.rank(candidates_nulls)

        assert isinstance(finalists, list)
        assert len(finalists) == 2

        for finalist in finalists:
            assert isinstance(finalist, dict)
            assert 'rank' in finalist and isinstance(finalist['rank'], int)
            assert 'finalist' in finalist
            assert finalist['finalist'].provider in ('mapbox', 'tomtom')

    def test_get_top_ranked(self, ruleset_definition_with_filter, candidates_unanimous):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        top_ranked = ruleset_obj.get_top_ranked(candidates_unanimous)

        assert isinstance(top_ranked, candidate.AccommodationCandidate)
        assert top_ranked.provider == 'mapbox'

    def test_get_top_ranked_filter(self, ruleset_definition_with_filter, candidates_dissenting):
        ruleset_obj = ruleset.Ruleset(ruleset_definition_with_filter)

        top_ranked = ruleset_obj.get_top_ranked(candidates_dissenting)

        assert isinstance(top_ranked, candidate.AccommodationCandidate)
        assert top_ranked.provider == 'tomtom'

"""
Accommodation consolidation
"""
import logging
import os

from consolidator.candidate import AccommodationCandidate
from consolidator.utils.fetcher import Fetcher
from consolidator.approach import base
from consolidator.strategy import fallback, ruleset


class AccommodationConsolidator(base.BaseConsolidator):
    """
    AccommodationConsolidator class tailored to consolidate candidates for an accommodation.
    """
    @classmethod
    def create_consolidation_winner(cls, winner : AccommodationCandidate, consolidation_score : int):
        return AccommodationCandidate(
            provider=winner.provider,
            longitude=winner.longitude,
            latitude=winner.latitude,
            score=consolidation_score,
            city=winner.city,
            country_code=winner.country_code
        )

    @classmethod
    def consolidate(cls, candidates, fetcher : Fetcher):
        """
        The consolidation approach is as follows, the approach stops as soon as one strategy
        delivers a result:

            - find the best ranked geocoding API response
            - find the best ranked partner match
            - (fallback) find the most similar city by name
        """
        geocoder_ruleset = ruleset.Ruleset(
            fetcher.fetch_ruleset_definition('geocoders', os.environ['GEOCODER_RULESET_VERSION'])
        )

        winner = geocoder_ruleset.get_top_ranked(candidates)
        if winner:
            return cls.create_consolidation_winner(winner, 1.0)

        partner_ruleset = ruleset.Ruleset(
            fetcher.fetch_ruleset_definition('partners', os.environ['PARTNER_RULESET_VERSION'])
        )

        winner = partner_ruleset.get_top_ranked(candidates)
        if winner:
            return cls.create_consolidation_winner(winner, 0.5)

        city_fallback = fallback.CityFallback(fetcher).get_fallback_coordinates(candidates)
        if city_fallback:
            return cls.create_consolidation_winner(city_fallback, 0.0)

        item_fallback_ruleset = ruleset.Ruleset(
            {
                'schema': {
                    'fields': [
                        'provider'
                    ],
                    'required': [
                        'provider'
                    ]
                },
                'rules': [
                    {
                        'provider': 'trivago'
                    }
                ]
            }
        )

        item_fallback = item_fallback_ruleset.get_top_ranked(candidates)
        if item_fallback:
            if item_fallback.longitude and item_fallback.latitude:
                return cls.create_consolidation_winner(item_fallback, 0.0)

        return None

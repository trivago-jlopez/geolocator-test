"""
The fallback module provides a CityFallback class to search similarly named destinations to the one
the candidates of the entity align on. Due to its complexity, it is implemented as a singleton.
"""
import collections
import os

import ngram

from consolidator import candidate
from consolidator.strategy import base
from consolidator.utils import fetcher


class Singleton(type):
    """
    Singleton pattern.
    """
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class CityFallback(base.Strategy, metaclass=Singleton):
    """
    The CityFallback class helps find cities with a high name similarity to the most common city
    name of the candidates for an entity. Country exclusion is applied to matches to avoid
    duplicates (city names are not unique).
    """
    def __init__(self, data_fetcher : fetcher.Fetcher):
        self.destinations = collections.defaultdict(list)

        for destination in data_fetcher.fetch_destinations():
            self.destinations[destination['name']].append(destination)

        self.search_layer = ngram.NGram(self.destinations.keys())

    def search_destinations(self, city, country_code):
        """
        Name similarity is tested using trigram similarity measures.
        """
        matches = self.search_layer.search(city, threshold=0.3)

        for name, _ in matches:
            for destination in self.destinations[name]:
                if destination['country_code'] == country_code or not country_code:
                    return destination

        return None

    def get_fallback_coordinates(self, candidates):
        """
        Returns a new candidate with the coordinates of the most similar city (by name) to the
        city based on already existing candidates.
        """
        unified_city = self.unify_field(candidates, 'city')

        unified_country_code = self.unify_field(candidates, 'country_code', allow_veto=True)

        if unified_city:
            result = self.search_destinations(unified_city, unified_country_code)

            if result:
                return candidate.AccommodationCandidate(
                    'city_polygons',
                    longitude=result['longitude'],
                    latitude=result['latitude'],
                    city=result['name'],
                    country_code=result['country_code']
                )

        return None

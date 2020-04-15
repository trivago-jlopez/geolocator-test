import logging

import ngram
import unidecode

from router import logger
from router.utils import Singleton


class CountryMapper(metaclass=Singleton):
    def __init__(self, data_fetcher):
        country_codes = data_fetcher.fetch_country_codes()
        self.valid_country_codes = list(map(lambda x: x['iso_3166_2'], country_codes))

        self.name_mapping = dict(
            (
                unidecode.unidecode(c['name']).lower(),
                c['iso_3166_2']
            ) for c in country_codes
        )

        self.search_layer = ngram.NGram(self.name_mapping.keys())
        self.cache = {}

        self.id_mapping = dict(
            (
                c['destination_id'],
                c['iso_3166_2']
            ) for c in country_codes
        )

        self.iso_3166_3_mapping = dict(
            (
                c['iso_3166_3'],
                c['iso_3166_2']
            ) for c in country_codes
        )

    def is_valid_country_code(self, country_code):
        if country_code in self.valid_country_codes:
            return True

    def map_name(self, country):
        if country not in self.cache:
            matches = self.search_layer.search(
                unidecode.unidecode(country).lower(),
                threshold=0.3
            )

            if matches:
                result = matches[0][0]

                self.cache[country] = result
                logger.log_message(logging.INFO, 'Name search \'%s\': %s', country, result)

        return self.name_mapping.get(self.cache.get(country))

    def map_iso_3166_3(self, iso_3166_3):
        return self.iso_3166_3_mapping.get(iso_3166_3)

    def map_destination_id(self, id):
        return self.id_mapping.get(id)

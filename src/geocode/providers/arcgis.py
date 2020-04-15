"""
Arcgis geocoder.
"""
import geocoder

from geocode import helpers
from geocode.providers.base import Geocoder, geocoder_process

class Arcgis(Geocoder):
    """
    Arcgis geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Arcgis, self).__init__('arcgis')

    def format_address(self, address):
        return ', '.join([address[i] for i in [
            'house_number',
            'street',
            'district',
            'postal_code',
            'city',
            'region',
            'country_code'
        ] if i in address])

    @geocoder_process
    def _geocode(self, address):
        """
        Error handling is based on Arcgis geocoding API documentation.

        .. _Arcgis: https://developers.arcgis.com/rest/geocode/api-reference/geocoding-service-output.htm
        """
        #key = self._request_key()

        try:
            query = self.format_address(address)
            #response = geocoder.arcgis(query, maxRows=100, **key)
            response = geocoder.arcgis(query, maxRows=100)

            if response.ok:
                return map(lambda x: x.json, response)
            else:
                if not response.get('error'):
                    raise helpers.NoResultsFoundError(self.name)
                if response.get('error') == 400:
                    raise helpers.InvalidRequestError(
                        self.name,
                        response.status
                    )
                # elif response.get('error') == 403: # Token related error -update after getting API key
                # elif response.get('error') == 499: # Token related error -update after getting API key
                elif response.get('error') == 500:
                    pass
                elif response.get('error') == 504:
                    pass

        except (KeyError, TypeError):
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

    def _parse_returned_address(self, result):
        #TODO
        return {}

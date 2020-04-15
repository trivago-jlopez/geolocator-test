"""
Baidu geocoder.
"""
import geocoder

from geocode import helpers
from geocode.providers.base import Geocoder, geocoder_process

class Baidu(Geocoder):
    """
    Baidu geocoding service.
    """
    _version = '1.0.0'

    def __init__(self):
        super(Baidu, self).__init__('baidu')

    @geocoder_process
    def _geocode(self, address):
        """
        Error handling is based on Baidu geocoding API documentation.

        .. _Baidu: http://lbsyun.baidu.com/index.php?title=lbscloud/api/appendix
        """
        key = self._request_key()

        try:
            response = geocoder.baidu(
                address.street,
                **key
            )

            if response.ok:
                return [i.json for i in response]
            elif response.status_code in (301, 302):
                raise helpers.RateLimitExceededError(self.name)
            elif response.status_code in (401, 402):
                raise helpers.QuotaExhaustedError(self.name)
            elif response.status_code == 211:
                raise helpers.InvalidRequestError(
                    self.name,
                    response.status
                )

        except KeyError:
            raise helpers.NoResultsFoundError(self.name)

        raise helpers.NoResultsFoundError(self.name)

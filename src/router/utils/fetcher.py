import gzip
import io
import json
import logging
import os

import boto3
import yaml

from router import entity, logger


class Fetcher:
    def fetch_country_codes(self):
        with open('data/country_codes.json') as f:
            return json.load(f)

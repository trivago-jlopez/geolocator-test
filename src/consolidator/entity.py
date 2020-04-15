import abc
import logging
import os

import boto3

from consolidator import approach, candidate, logger
from consolidator.utils import fetcher, helpers


class Entity:
    def __init__(self, entity_id, entity_type, data_fetcher=None):
        self.entity_id = entity_id
        self.entity_type = entity_type
        self.fetcher = data_fetcher

    @property
    def key(self):
        return '{entity_type}:{entity_id}'.format(
            entity_type=self.entity_type,
            entity_id=self.entity_id
        )

    def to_dict(self):
        return {
            'entity_id': self.entity_id,
            'entity_type': self.entity_type
        }

    @abc.abstractmethod
    def _get_candidates(self, data_fetcher : fetcher.Fetcher):
        raise NotImplementedError

    @helpers.lazyprop
    def candidates(self):
        return self._get_candidates(self.fetcher)

    @staticmethod
    def get_eligible_candidates(candidates):
        """
        Return external responses, previous consolidation results are filtered out.
        """
        return list(filter(lambda x: not x.provider.startswith('consolidator'), candidates))

    @staticmethod
    def get_previous_consolidation(candidates):
        """
        Return the previous consolidation dependent on the environment or None.
        """
        for candidate in candidates:
            if candidate.provider == 'consolidator_' + os.environ['ENVIRONMENT']:
                return candidate

        return None

    @abc.abstractmethod
    def _consolidate(self, candidates, data_fetcher : fetcher.Fetcher):
        raise NotImplementedError

    @helpers.lazyprop
    def consolidated(self):
        """
        Consolidates eligible candidates for this entity. A successful consolidation result is
        returned if:
            - there is no previous consolidation result
            - the previous consolidation result has a lower score than the new result
        """
        eligible_candidates = self.get_eligible_candidates(self.candidates)

        old_consolidation = self.get_previous_consolidation(self.candidates)
        new_consolidation = self._consolidate(eligible_candidates, self.fetcher)

        if new_consolidation:
            if not old_consolidation or old_consolidation.score < new_consolidation.score:
                return new_consolidation

        return None


class Accommodation(Entity):
    def __init__(self, entity_id, data_fetcher : fetcher.Fetcher):
        super(Accommodation, self).__init__(entity_id, 'accommodation', data_fetcher)

    def _get_candidates(self, data_fetcher : fetcher.Fetcher):
        candidates = data_fetcher.fetch_candidates(self)

        return [
            candidate.AccommodationCandidate(**i) for i in candidates
        ]

    def _consolidate(self, candidates, data_fetcher : fetcher.Fetcher) -> candidate.AccommodationCandidate:
        return approach.AccommodationConsolidator.consolidate(candidates, data_fetcher)


class CandidateAccommodation(Accommodation):
    def __init__(self, entity_id, data_fetcher : fetcher.Fetcher):
        super(CandidateAccommodation, self).__init__(entity_id, data_fetcher)
        self.entity_type = 'candidate_accommodation'


class ReferenceAccommodation(Accommodation):
    def __init__(self, entity_id, data_fetcher : fetcher.Fetcher):
        super(ReferenceAccommodation, self).__init__(entity_id, data_fetcher)
        self.entity_type = 'reference_accommodation'

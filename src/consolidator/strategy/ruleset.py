"""
Ruleset class to rank a pool of candidates for an entity.

A ruleset is an ordered list of rules against which candidates are matched. If rule A proceeds
rule B in the the ruleset, then a candidate matching rule A is ranked higher than a candidate
matching rule B. AccommodationCandidates that match some rule are called finalists. AccommodationCandidates that don't match
any rule are discarded.

Rulesets can be specialised by for example country, dependent on what information fields are present
in the geocodes DynamoDB table. You can specify what these fields are using the filter fields.

When ranking, a list of candidates is assumed to be unified (all candidates have the same filter
fields). Comparing ranks only makes sense for unified candidates since ranks obtained from
different rulesets are non comparable.
"""
import collections
import decimal

from consolidator.strategy import base


class Ruleset(base.Strategy):
    """
    The Ruleset class helps filter candidates for an entity by matching them to an ordered list of
    rules. Every matched candidate (finalist) gets a ranking. The candidate with the best (i.e. 
    lowest number) is considered the winner. If no candidates match, there are no finalists, hence
    no winner.
    """
    def __init__(self, ruleset : dict):
        #TODO: validation of ruleset using schema
        if ruleset:
            self._rules = ruleset['rules']
            self._filter_fields = ruleset['schema'].get('filter', [])
        else:
            self._rules = []
            self._filter_fields = []

    def is_match(self, rule : dict, candidate):
        """
        Checks whether a candidate satisfies a rule. Comparison is based purely on rule fields that
        are not filter fields.
        """
        for k, v in rule.items():
            if not v:
                # bypass null fields in rules
                continue

            if not getattr(candidate, k, None):
                # cannot guarantee that the candidate is of sufficient quality
                return False
            else:
                try:
                    candidate_value = getattr(candidate, k)

                    if isinstance(candidate_value, (float, int, decimal.Decimal)):
                        if candidate_value < type(candidate_value)(str(v)):
                            return False
                    else:
                        if candidate_value != type(candidate_value)(str(v)):
                            return False
                except ValueError:
                    # e.g. trying to cast a string to a decimal
                    return False
                except decimal.InvalidOperation:
                    # trying to cast a decimal (rule) to a string (candidate)
                    return False
        else:
            return True

    def filter_rules(self, filter_dict):
        """
        Filter the rules based on some filter fields.
        """
        def is_match(filter_dict, rule):
            """
            Either both candidate and rule have equal non null values or they both have null values
            for a filter field.
            """
            for k in self._filter_fields:
                if not filter_dict.get(k) == rule.get(k):
                    return False
            else:
                return True

        return list(filter(lambda x: is_match(filter_dict, x), self.get_rules()))

    def obtain_default_rules(self):
        """
        Return default rules, all filter fields are null.
        """
        default_match = dict((k, None) for k in self._filter_fields)

        return self.filter_rules(default_match)

    def obtain_rules(self, filter_dict : dict):
        """
        Filter rules based on values for the filter fields, if all rules are filtered, the default
        values for the filter fields are used instead.
        """
        candidate_rules = self.filter_rules(filter_dict)

        if candidate_rules:
            return candidate_rules

        # return the default rules
        return self.obtain_default_rules()

    def rank_candidate(self, candidate : dict, rules : list):
        """
        Returns a rank based on the depth of the rule in the ruleset to which the candidate
        matched, or None.
        """
        for i, rule in enumerate(rules):
            if self.is_match(rule, candidate):
                return i + 1

        return None

    def unify_fields(self, fields : list, candidates : list):
        """
        Unifying candidates means getting them on the same page for the filter fields. This avoids
        the scenario that candidates (same entity) disagree on what country the entity is in.
        
        This mechanism is important in for example ranking candidates, as ranking can be done
        according to a ranking that is different per country. Without unification, ranks in
        different countries cannot compare.
        """
        unified_fields = {}

        for field in fields:
            unified_fields[field] = self.unify_field(
                candidates,
                field,
                allow_null=False,
                allow_veto=True
            )

        return unified_fields

    def rank(self, candidates : list):
        """
        Filters a list of candidates and returns a list of tuples (finalist, rank) of all
        candidates that match to a rule in the ruleset. If no candidates matched, or there are no
        rules, nothing is returned.
        """
        finalists = []

        unified_fields = self.unify_fields(self._filter_fields, candidates)
        rules = self.obtain_rules(unified_fields)

        for candidate in candidates:
            rank = self.rank_candidate(candidate, rules)

            if rank:
                finalists.append({
                    'finalist': candidate,
                    'rank': rank
                })

        return finalists

    def get_top_ranked(self, candidates : list):
        """
        Ranks the supplied candidates, those that receive a rank are considered finalists, the rest
        is discarded. Return the top ranked finalist or None.
        """
        finalists = self.rank(candidates)

        if finalists:
            winner = min(finalists, key=lambda x: x['rank'])
            return winner['finalist']
        else:
            return None

    def get_rules(self):
        """
        Returns the rules.
        """
        return self._rules

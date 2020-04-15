import abc
import collections


class Strategy:
    def unify_field(self, candidates : list, field, allow_null=False, allow_veto=False):
        """
        Get candidates on the same page for the unification fields. For example, upon unifying
        candidates for the country code field, all country code values are collected. The one that
        occurs the most is the unified value.

        Null values for the field put forward by candidates can be ignored by enabling the
        allow_null vote.

        If allow_veto is enabled, the candidates must be unanimous. In combination with allow_null,
        if not enabled, one null value is enough to reject any non null values.
        """
        field_values = map(lambda x: getattr(x, field, None), candidates)

        if not allow_null:
            field_values = filter(lambda x: x is not None, field_values)

        majority_fields = collections.Counter(field_values).most_common()
        if allow_veto:
            if len(majority_fields) != 1:
                return None
        
        if majority_fields:
            return majority_fields[0][0]
        else:
            return None


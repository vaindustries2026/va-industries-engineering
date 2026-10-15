"""Deterministic rights gate.

Input is only the authority's machine-readable rights record as returned by the
adapter (never caller text, never a model judgement). Output is a rights record
with the obligations that must travel with every downstream edit. Passing this
gate means "automated rights check passed"; it does not approve the item.
"""
import re

from .errors import FailClosed

# Licence codes accepted for a monetised channel that edits footage:
# commercial use and adaptation must both be permitted (so no NC, no ND).
_ACCEPT = {
    'SRC-PD-ARCHIVE': re.compile(r'^pd$'),
    'SRC-OPEN-LICENSE': re.compile(r'^(cc0|cc-by-[0-9](\.[0-9])?|cc-by-sa-[0-9](\.[0-9])?)$'),
}
_REJECT_FRAGMENTS = ('-nc', '-nd', 'nc-', 'nd-', 'fair', 'nonfree', 'non-free', 'copyrighted')


def evaluate(source_class, authority_rights):
    """Return a rights record or raise FailClosed.

    authority_rights keys (all from the source authority):
      license_code, license_name, license_url, attribution, restrictions, copyrighted_flag
    """
    pattern = _ACCEPT.get(source_class)
    if pattern is None:
        raise FailClosed('RIGHTS_CLASS_NOT_AUTOMATABLE', source_class)
    code = (authority_rights.get('license_code') or '').strip().lower()
    if not code:
        raise FailClosed('RIGHTS_LICENSE_CODE_MISSING', 'authority published no machine-readable licence code')
    if any(f in code for f in _REJECT_FRAGMENTS):
        raise FailClosed('RIGHTS_LICENSE_REJECTED', code)
    if not pattern.match(code):
        raise FailClosed('RIGHTS_LICENSE_NOT_IN_ALLOWLIST', f'{code} for {source_class}')
    restrictions = (authority_rights.get('restrictions') or '').strip()
    if restrictions:
        # Trademark / personality / other restrictions need a human, not a pipeline.
        raise FailClosed('RIGHTS_RESTRICTIONS_PRESENT', restrictions)
    if code == 'pd' and str(authority_rights.get('copyrighted_flag', '')).strip().lower() == 'true':
        raise FailClosed('RIGHTS_CONFLICT', 'licence pd but authority marks item copyrighted')

    attribution_required = code.startswith('cc-by')
    attribution = (authority_rights.get('attribution') or '').strip()
    if attribution_required and not attribution:
        raise FailClosed('RIGHTS_ATTRIBUTION_MISSING', code)
    return {
        'source_class': source_class,
        'license_code': code,
        'license_name': authority_rights.get('license_name'),
        'license_url': authority_rights.get('license_url'),
        'obligations': {
            'attribution_required': attribution_required,
            'attribution_text': attribution or None,
            'share_alike': code.startswith('cc-by-sa'),
            'commercial_use_permitted': True,
            'adaptation_permitted': True,
        },
        'determined_by': 'AUTHORITY_MACHINE_READABLE_FIELD',
        'automated_rights_check': 'PASS',
        'human_rights_approval': 'PENDING',
    }

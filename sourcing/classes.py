"""Source-class registry and deterministic automation ranking.

Tiers:
  A  fully automatable: rights are a per-item machine-readable field published by
     the source authority, and acquisition is a sanctioned API/download.
  B  automatable delivery, human rights: a contract or signed grant establishes
     rights once; delivery and provenance can then be automated.
  C  human/legal per item: rights depend on a fact-specific judgement or on a
     platform that offers no sanctioned acquisition route. Never auto-cleared.
  X  prohibited: unlawful or in breach of platform terms. Hard-blocked.

Rank = tier order, then anime relevance (higher first), then class id.
"""
from .errors import FailClosed

TIER_ORDER = {'A': 0, 'B': 1, 'C': 2, 'X': 3}

SOURCE_CLASSES = {
    'SRC-PD-ARCHIVE': {
        'name': 'Public-domain archives with machine-readable rights',
        'tier': 'A',
        'anime_relevance': 1,
        'legal_basis': 'Copyright expired in the US and the source country (as asserted by the archive licence template)',
        'rights_evidence': 'per-item licence code from the archive API (e.g. Commons extmetadata License = pd)',
        'examples': ['Wikimedia Commons', 'Library of Congress', 'national film archives'],
        'acquisition': 'documented public API + direct file URL; authority SHA-1/size published',
        'limits': 'Anime relevance is tiny (pre-1940s Japanese animation only).',
        'adapters': ['wikimedia_commons'],
    },
    'SRC-OPEN-LICENSE': {
        'name': 'Openly licensed works (CC0 / CC BY / CC BY-SA) with per-item licence fields',
        'tier': 'A',
        'anime_relevance': 2,
        'legal_basis': 'Licence grant by the author; commercial use and adaptation permitted (no NC, no ND)',
        'rights_evidence': 'per-item licence code from the platform API; attribution string captured',
        'examples': ['Wikimedia Commons', 'Openverse', 'Blender Studio open movies', 'Vimeo CC (API licence field)'],
        'acquisition': 'documented public API + direct file URL',
        'limits': 'Few anime-style works; obligations (attribution, share-alike) travel with every edit.',
        'adapters': ['wikimedia_commons'],
    },
    'SRC-OWN-ORIGINAL': {
        'name': 'Own or commissioned original animation (incl. generated where provider terms grant commercial rights)',
        'tier': 'B',
        'anime_relevance': 2,
        'legal_basis': 'Work-for-hire / assignment contract, or provider terms verified per plan',
        'rights_evidence': 'contract id or provider-terms record; existing paid-authorisation gate for spend',
        'examples': ['commissioned animators', 'generation providers already governed for Mikko & Lumi'],
        'acquisition': 'internal pipeline output',
        'limits': 'Not clip farming of third-party IP; generation spend governed separately.',
        'adapters': [],
    },
    'SRC-RIGHTSHOLDER-LICENSE': {
        'name': 'Rights-holder clip licensing / official partner programmes',
        'tier': 'B',
        'anime_relevance': 5,
        'legal_basis': 'Written licence from the publisher, distributor or licensing agent',
        'rights_evidence': 'signed agreement id + territory/term/platform/edit scope, recorded by a human',
        'examples': ['publisher clip programmes', 'distributor licensing desks', 'licensing agencies'],
        'acquisition': 'licensor delivery (S3/SFTP/Drive/API), then automated ingest + hash',
        'limits': 'Contract negotiation is human; only delivery is automatable.',
        'adapters': [],
    },
    'SRC-CREATOR-GRANT': {
        'name': 'Creator submissions with an explicit licence grant',
        'tier': 'B',
        'anime_relevance': 3,
        'legal_basis': 'Submitter grants a licence and attests ownership under published submission terms',
        'rights_evidence': 'submission record + accepted terms version + ownership attestation',
        'examples': ['fan animators', 'indie studios', 'AMV/edit creators of their own footage'],
        'acquisition': 'submission form/upload endpoint, automated ingest + hash',
        'limits': 'Attestation can be false: human review plus takedown path required.',
        'adapters': [],
    },
    'SRC-PLATFORM-NATIVE-REMIX': {
        'name': 'Platform-native reuse tools (e.g. YouTube Shorts remix)',
        'tier': 'C',
        'anime_relevance': 4,
        'legal_basis': 'Platform licence between uploader and platform; only inside the platform tool',
        'rights_evidence': 'the platform tool itself; no exportable rights record',
        'examples': ['YouTube Shorts remix / Use this sound'],
        'acquisition': 'in-app only; no download or API route',
        'limits': 'Cannot be automated without breaching terms; rights owner can disable remix.',
        'adapters': [],
    },
    'SRC-OFFICIAL-PROMO': {
        'name': 'Official promotional material (trailers, PVs, press kits)',
        'tier': 'C',
        'anime_relevance': 5,
        'legal_basis': 'None by default; press-kit terms are usually editorial-only. Needs per-item permission',
        'rights_evidence': 'written permission, after which the item moves to SRC-RIGHTSHOLDER-LICENSE',
        'examples': ['official studio YouTube channels', 'publisher press portals'],
        'acquisition': 'downloading from YouTube is outside its terms; press portals are login-gated',
        'limits': 'Publicly viewable does not mean licensed.',
        'adapters': [],
    },
    'SRC-FAIR-USE-EXCERPT': {
        'name': 'Fair-use / quotation excerpts for commentary or criticism',
        'tier': 'C',
        'anime_relevance': 5,
        'legal_basis': 'US 17 USC 107 / Japan Art. 32 quotation: fact-specific, decided per edit',
        'rights_evidence': 'human/legal assessment of the finished edit; never a pipeline field',
        'examples': ['review/analysis shorts with substantial original commentary'],
        'acquisition': 'only from legally accessed copies without circumventing DRM',
        'limits': 'Cannot be decided before the edit exists; Content ID claims still apply.',
        'adapters': [],
    },
    'SRC-PROHIBITED': {
        'name': 'Piracy, ripped streams, DRM circumvention, terms-violating scraping, unknown re-uploads',
        'tier': 'X',
        'anime_relevance': 0,
        'legal_basis': 'None',
        'rights_evidence': 'None',
        'examples': ['fansub/pirate sites', 'stream rippers', 'yt-dlp against YouTube', 'unattributed re-uploads'],
        'acquisition': 'BLOCKED',
        'limits': 'Never acquire, never ingest, never process.',
        'adapters': [],
    },
}


def ranked():
    """Deterministic automation-viability ranking (list of (rank, class_id, record))."""
    order = sorted(SOURCE_CLASSES.items(),
                   key=lambda kv: (TIER_ORDER[kv[1]['tier']], -kv[1]['anime_relevance'], kv[0]))
    return [(i + 1, cid, rec) for i, (cid, rec) in enumerate(order)]


def require_automatable(class_id):
    """Only tier-A classes may run an unattended acquisition."""
    rec = SOURCE_CLASSES.get(class_id)
    if rec is None:
        raise FailClosed('SOURCE_CLASS_UNKNOWN', class_id)
    if rec['tier'] == 'X':
        raise FailClosed('SOURCE_CLASS_PROHIBITED', class_id)
    if rec['tier'] != 'A':
        raise FailClosed('SOURCE_CLASS_NOT_AUTOMATABLE', f'{class_id} is tier {rec["tier"]}')
    return rec

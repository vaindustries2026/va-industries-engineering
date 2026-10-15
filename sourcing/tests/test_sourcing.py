"""Source procurement tests (T-SRC-01..14). No network, no paid calls.

FakeTransport serves a Commons-shaped API response (formatversion=2) and file bytes,
so discovery -> rights -> download -> integrity -> provenance runs end to end offline.
"""
import hashlib
import io
import json
import os
import stat
import tempfile
import unittest
from pathlib import Path

from sourcing import rights
from sourcing.acquire import Ledger, run
from sourcing.adapters.base import Transport
from sourcing.classes import SOURCE_CLASSES, ranked, require_automatable
from sourcing.errors import FailClosed

PKG = Path(__file__).resolve().parents[1]
JOB = json.loads((PKG / 'jobs' / 'commons_pd_anime_proof_v1.json').read_text())
FILE_URL = 'https://upload.wikimedia.org/wikipedia/commons/a/ab/Test_film.webm'
BYTES = b'\x1aE\xdf\xa3' + b'fake-webm-payload' * 64


def _page(title='File:Test film.webm', url=FILE_URL, data=BYTES, license_code='pd', mime='video/webm',
          mediatype='VIDEO', restrictions='', copyrighted='False', artist='<a href="x">Jun&#39;ichi Kōuchi</a>',
          size=None, sha1=None):
    ext = {
        'License': {'value': license_code},
        'LicenseShortName': {'value': 'Public domain' if license_code == 'pd' else license_code.upper()},
        'LicenseUrl': {'value': ''},
        'Artist': {'value': artist},
        'Restrictions': {'value': restrictions},
        'Copyrighted': {'value': copyrighted},
    }
    return {'pageid': 1, 'ns': 6, 'title': title, 'imageinfo': [{
        'url': url, 'descriptionurl': 'https://commons.wikimedia.org/wiki/' + title.replace(' ', '_'),
        'size': len(data) if size is None else size, 'sha1': sha1 or hashlib.sha1(data).hexdigest(),
        'mime': mime, 'mediatype': mediatype, 'timestamp': '2020-01-01T00:00:00Z', 'extmetadata': ext}]}


class FakeTransport:
    def __init__(self, pages, files=None):
        self.api = json.dumps({'batchcomplete': True, 'query': {'pages': pages}}).encode()
        self.files = files if files is not None else {FILE_URL: BYTES}
        self.calls = []

    def get_bytes(self, url, max_bytes):
        self.calls.append(('GET', url))
        return self.api

    def download(self, url, dest_path, max_bytes):
        self.calls.append(('DOWNLOAD', url))
        data = self.files[url]
        if len(data) > max_bytes:
            raise FailClosed('DOWNLOAD_EXCEEDS_CAP', url)
        Path(dest_path).write_bytes(data)
        return len(data)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.job_path = self.dir / 'job.json'
        self.write_job()
        self.out = self.dir / 'out'

    def tearDown(self):
        for p in self.dir.rglob('*'):
            if p.is_file():
                os.chmod(p, 0o644)
        self.tmp.cleanup()

    def write_job(self, **over):
        self.job_path.write_text(json.dumps({**JOB, **over}))


class Classes(unittest.TestCase):
    def test_T01_ranking_deterministic_tier_order(self):
        r = ranked()
        self.assertEqual(r, ranked())
        tiers = [rec['tier'] for _, _, rec in r]
        self.assertEqual(tiers, sorted(tiers, key='ABCX'.index))
        self.assertEqual(r[-1][1], 'SRC-PROHIBITED')
        self.assertEqual(len(r), len(SOURCE_CLASSES))

    def test_T02_only_tier_A_runs_unattended(self):
        for cid, rec in SOURCE_CLASSES.items():
            if rec['tier'] == 'A':
                require_automatable(cid)
            else:
                with self.assertRaises(FailClosed):
                    require_automatable(cid)
        with self.assertRaises(FailClosed) as c:
            require_automatable('SRC-PROHIBITED')
        self.assertEqual(c.exception.code, 'SOURCE_CLASS_PROHIBITED')


class Rights(unittest.TestCase):
    def ev(self, cls, **kw):
        base = {'license_code': 'pd', 'attribution': 'Author', 'restrictions': '', 'copyrighted_flag': 'False'}
        return rights.evaluate(cls, {**base, **kw})

    def code(self, cls, **kw):
        with self.assertRaises(FailClosed) as c:
            self.ev(cls, **kw)
        return c.exception.code

    def test_T03_accepts_pd_cc0_ccby_ccbysa(self):
        self.assertEqual(self.ev('SRC-PD-ARCHIVE')['human_rights_approval'], 'PENDING')
        self.assertFalse(self.ev('SRC-OPEN-LICENSE', license_code='cc0')['obligations']['attribution_required'])
        r = self.ev('SRC-OPEN-LICENSE', license_code='cc-by-sa-4.0')
        self.assertTrue(r['obligations']['share_alike'])
        self.assertTrue(r['obligations']['attribution_required'])

    def test_T04_rejects_nc_nd_missing_unknown(self):
        self.assertEqual(self.code('SRC-OPEN-LICENSE', license_code='cc-by-nc-4.0'), 'RIGHTS_LICENSE_REJECTED')
        self.assertEqual(self.code('SRC-OPEN-LICENSE', license_code='cc-by-nd-4.0'), 'RIGHTS_LICENSE_REJECTED')
        self.assertEqual(self.code('SRC-OPEN-LICENSE', license_code=''), 'RIGHTS_LICENSE_CODE_MISSING')
        self.assertEqual(self.code('SRC-OPEN-LICENSE', license_code='gfdl'), 'RIGHTS_LICENSE_NOT_IN_ALLOWLIST')
        self.assertEqual(self.code('SRC-OPEN-LICENSE', license_code='pd'), 'RIGHTS_LICENSE_NOT_IN_ALLOWLIST')
        self.assertEqual(self.code('SRC-RIGHTSHOLDER-LICENSE'), 'RIGHTS_CLASS_NOT_AUTOMATABLE')

    def test_T05_restrictions_conflict_attribution(self):
        self.assertEqual(self.code('SRC-PD-ARCHIVE', restrictions='trademarked'), 'RIGHTS_RESTRICTIONS_PRESENT')
        self.assertEqual(self.code('SRC-PD-ARCHIVE', copyrighted_flag='True'), 'RIGHTS_CONFLICT')
        self.assertEqual(self.code('SRC-OPEN-LICENSE', license_code='cc-by-4.0', attribution=''),
                         'RIGHTS_ATTRIBUTION_MISSING')


class Acquire(Base):
    def test_T06_end_to_end_review_provenance(self):
        t = FakeTransport([_page()])
        res = run(self.job_path, self.out, transport=t)
        r = res['results'][0]
        self.assertEqual(r['status'], 'ACQUIRED_REVIEW')
        item = self.out / r['source_item_id']
        raw = item / 'raw.webm'
        self.assertEqual(raw.read_bytes(), BYTES)
        self.assertEqual(r['sha256'], hashlib.sha256(BYTES).hexdigest())
        self.assertFalse(raw.stat().st_mode & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))
        prov = json.loads((item / 'provenance.json').read_text())
        self.assertEqual(prov['status'], 'REVIEW')
        self.assertEqual(prov['rights']['determined_by'], 'AUTHORITY_MACHINE_READABLE_FIELD')
        self.assertEqual(prov['rights']['obligations']['attribution_text'], "Jun'ichi Kōuchi")
        self.assertEqual(prov['paid_calls'], 0)
        self.assertEqual(len(Ledger(self.out / 'acquisition_ledger.jsonl').rows()), 1)
        self.assertEqual([c[0] for c in t.calls], ['GET', 'DOWNLOAD'])

    def test_T07_rerun_is_idempotent(self):
        run(self.job_path, self.out, transport=FakeTransport([_page()]))
        t = FakeTransport([_page()])
        res = run(self.job_path, self.out, transport=t)
        self.assertEqual(res['results'][0]['status'], 'ALREADY_ACQUIRED')
        self.assertNotIn('DOWNLOAD', [c[0] for c in t.calls])
        self.assertEqual(len(Ledger(self.out / 'acquisition_ledger.jsonl').rows()), 1)

    def test_T08_integrity_mismatch_fails_closed_no_residue(self):
        t = FakeTransport([_page()], files={FILE_URL: BYTES + b'tampered'})
        with self.assertRaises(FailClosed) as c:
            run(self.job_path, self.out, transport=t)
        self.assertEqual(c.exception.code, 'INTEGRITY_SIZE_MISMATCH')
        t = FakeTransport([_page(size=len(BYTES) + 1)], files={FILE_URL: BYTES + b'x'})
        with self.assertRaises(FailClosed) as c:
            run(self.job_path, self.out, transport=t)
        self.assertEqual(c.exception.code, 'INTEGRITY_SHA1_MISMATCH')
        self.assertEqual(list(self.out.glob('.partial-*')), [])
        self.assertEqual(list(self.out.glob('SRCITEM-*')), [])
        self.assertEqual(Ledger(self.out / 'acquisition_ledger.jsonl').rows(), [])

    def test_T09_ineligible_candidates_screened_with_reasons(self):
        pages = [
            _page('File:A.webm', license_code='cc-by-nc-4.0'),
            _page('File:B.webm', url='https://evil.example/B.webm'),
            _page('File:C.webm', mime='video/mp4'),
            _page('File:D.jpg', mediatype='BITMAP'),
            _page('File:E.webm', size=JOB['max_bytes'] + 1),
            _page('File:F.webm', restrictions='personality'),
        ]
        t = FakeTransport(pages)
        with self.assertRaises(FailClosed) as c:
            run(self.job_path, self.out, transport=t)
        self.assertEqual(c.exception.code, 'NO_ELIGIBLE_SOURCE')
        rep = json.loads((self.out / 'discovery_report.json').read_text())
        self.assertEqual([s['reason'].split(':')[0] for s in rep['screened']], [
            'RIGHTS_LICENSE_REJECTED', 'FILE_HOST_NOT_AUTHORITY', 'MIME_NOT_ACCEPTED',
            'MEDIATYPE_NOT_ACCEPTED', 'SIZE_NOT_ACCEPTED', 'RIGHTS_RESTRICTIONS_PRESENT'])
        self.assertNotIn('DOWNLOAD', [c[0] for c in t.calls])

    def test_T10_non_automatable_class_stops_before_network(self):
        self.write_job(source_class='SRC-RIGHTSHOLDER-LICENSE')
        t = FakeTransport([_page()])
        with self.assertRaises(FailClosed) as c:
            run(self.job_path, self.out, transport=t)
        self.assertEqual(c.exception.code, 'SOURCE_CLASS_NOT_AUTOMATABLE')
        self.assertEqual(t.calls, [])

    def test_T11_job_schema_and_caps(self):
        self.write_job(max_items=50)
        with self.assertRaises(FailClosed):
            run(self.job_path, self.out, transport=FakeTransport([]))
        self.write_job(extra_field='x')
        with self.assertRaises(FailClosed) as c:
            run(self.job_path, self.out, transport=FakeTransport([]))
        self.assertEqual(c.exception.code, 'JOB_SCHEMA_INVALID')
        self.write_job(channel='MIKKO_LUMI')
        with self.assertRaises(FailClosed):
            run(self.job_path, self.out, transport=FakeTransport([]))

    def test_T12_deterministic_selection_and_max_items(self):
        other = b'second' * 50
        url2 = 'https://upload.wikimedia.org/wikipedia/commons/b/bb/Z.webm'
        t = FakeTransport([_page('File:Z.webm', url=url2, data=other), _page()],
                          files={FILE_URL: BYTES, url2: other})
        res = run(self.job_path, self.out, transport=t)
        self.assertEqual(len(res['results']), 1)
        self.assertEqual(res['results'][0]['authority_item_id'], 'File:Test film.webm')

    def test_T13_job_class_must_match_licence(self):
        self.write_job(source_class='SRC-OPEN-LICENSE')
        with self.assertRaises(FailClosed) as c:
            run(self.job_path, self.out, transport=FakeTransport([_page(license_code='pd')]))
        self.assertEqual(c.exception.code, 'NO_ELIGIBLE_SOURCE')


class TransportCaps(unittest.TestCase):
    def test_T14_https_only_and_download_cap(self):
        t = Transport()
        with self.assertRaises(FailClosed) as c:
            t.get_bytes('http://commons.wikimedia.org/', 10)
        self.assertEqual(c.exception.code, 'TRANSPORT_NOT_HTTPS')

        class R(io.BytesIO):
            def __enter__(self):
                return self

        t._open = lambda url: R(b'x' * 100)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(FailClosed) as c:
                t.download('https://upload.wikimedia.org/f', Path(d) / 'f', 10)
            self.assertEqual(c.exception.code, 'DOWNLOAD_EXCEEDS_CAP')
        with self.assertRaises(FailClosed) as c:
            t.get_bytes('https://x/', 10)
        self.assertEqual(c.exception.code, 'TRANSPORT_RESPONSE_TOO_LARGE')


if __name__ == '__main__':
    unittest.main()

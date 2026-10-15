# Source Procurement v1.0 — Anime Clip Farming

Date: 2026-10-15. Scope: Anime Clip Farming source acquisition only. Mikko & Lumi, Agent-000…008, n8n and Supabase not touched.
Human scope decisions for this task: channel = Anime Clip Farming; proof = one free real fetch of a clearly free-licensed item, verified licence + hash, evidence in the repo only (no Supabase/n8n writes, no paid calls).

## 1. Result in one paragraph

All nine legal/technical source classes are defined and ranked (`sourcing/classes.py`, `python3 -m sourcing classes`). Two classes are fully automatable: open-licence works and public-domain archives, where the source authority publishes a per-item machine-readable licence and integrity digest. An unattended acquisition path for those classes is built (`sourcing/`): Wikimedia Commons API → deterministic rights gate → host-pinned, size-capped download → authority SHA-1 + size check → SHA-256 → read-only raw file + REVIEW provenance + append-only ledger. It passes 14/14 offline tests. **The live proof run did not complete:** this cloud container's network policy denies `commons.wikimedia.org` (proxy 403). The pipeline failed closed with `TRANSPORT_UNREACHABLE` before acquiring anything. So the automated path is **built and offline-proven, not live-proven**. One environment change unblocks it (§6).

The key commercial finding: **the classes with the highest anime relevance are not automatable.** Rights-holder licences, official promotional material and fair-use excerpts need a contract or a per-edit legal judgement. The automatable classes hold almost no anime. Scaling the channel on licensed anime therefore depends on a human-negotiated licence (tier B). After that, only the delivery and ingest can be automated with this same pipeline.

## 2. Source classes, ranked by automation viability

Tier A = fully automatable (authority publishes machine-readable rights per item). B = automatable delivery after a one-time human rights step. C = human/legal decision per item; never auto-cleared. X = prohibited.
Rank = tier, then anime relevance (0–5), then id. The ranking is deterministic.

| # | Tier | Class | Anime rel. | Legal basis | Rights evidence | Why this tier |
|---|---|---|---|---|---|---|
| 1 | A | `SRC-OPEN-LICENSE` (CC0 / CC BY / CC BY-SA) | 2 | Author's licence grant permitting commercial use and adaptation | Per-item licence code from platform API + attribution | Licence is a field; API + direct file URL; Commons publishes SHA-1 |
| 2 | A | `SRC-PD-ARCHIVE` | 1 | Copyright expired (US + source country, per archive template) | Per-item licence code (`pd`) | Same mechanics; but only pre-1940s Japanese animation |
| 3 | B | `SRC-RIGHTSHOLDER-LICENSE` | 5 | Written licence from publisher/distributor/agent | Signed agreement id + territory/term/platform/edit scope | Contract is human; delivery (S3/SFTP/API) automatable |
| 4 | B | `SRC-CREATOR-GRANT` | 3 | Submitter grants licence and attests ownership | Submission record + terms version + attestation | Attestation can be false: human review + takedown path |
| 5 | B | `SRC-OWN-ORIGINAL` | 2 | Work-for-hire/assignment, or verified provider terms | Contract id / provider-terms record | Rights fixed by contract; generation spend governed separately |
| 6 | C | `SRC-FAIR-USE-EXCERPT` | 5 | 17 USC 107 / Japan Art. 32 quotation | Human/legal assessment of the finished edit | Fact-specific, decided per edit; Content ID still applies |
| 7 | C | `SRC-OFFICIAL-PROMO` | 5 | None by default; press kits usually editorial-only | Written permission, after which the item becomes class 3 | Publicly viewable ≠ licensed; YouTube download is outside its terms |
| 8 | C | `SRC-PLATFORM-NATIVE-REMIX` | 4 | Platform licence, valid only inside the platform tool | None exportable | No API/download route; owner can disable remix |
| 9 | X | `SRC-PROHIBITED` | 0 | None | None | Piracy, stream ripping, DRM circumvention, yt-dlp against YouTube, unknown re-uploads: hard-blocked |

Channel-level caveat (not a source class): YouTube's reused-content monetisation policy can apply even to lawfully licensed clips unless the edit adds substantial original value. A clean source does not make a monetisable short.

## 3. Rules enforced in code

- Only tier-A classes run unattended (`require_automatable`); B/C/X fail before any network call (T-SRC-10).
- Rights are read only from the authority's machine-readable fields. Caller text, filenames and model output are never inputs to `rights.evaluate`.
- Accepted: `pd` for PD-ARCHIVE; `cc0`, `cc-by-N`, `cc-by-sa-N` for OPEN-LICENSE. Rejected: any NC or ND licence, missing code, unknown code, class/licence mismatch, any authority `Restrictions` value (trademark/personality), `pd` marked copyrighted, and CC BY without attribution.
- Obligations (attribution text, share-alike) are stored with the item and must travel with every edit.
- File host is pinned to `upload.wikimedia.org`. HTTPS only. The job sets a size cap (≤500 MB hard limit) and max 5 items per job.
- Integrity: downloaded size and SHA-1 must equal the authority's published values before the file is kept. Partial files are deleted on failure (T-SRC-08).
- Output status is always `REVIEW`, with `human_rights_approval: PENDING`. Nothing in the package can set APPROVED.
- Append-only JSONL ledger, insert-only by SHA-256, deduplicated by authority SHA-1. A rerun returns `ALREADY_ACQUIRED` without downloading again (T-SRC-07).
- Every candidate's screening decision and reason is written to `discovery_report.json`, with the API request URL and response SHA-256.

## 4. Tests: 14/14 pass

`python3 -m unittest discover -s sourcing/tests -t .` (no network; FakeTransport serves a Commons-shaped `formatversion=2` response).
T01 deterministic ranking · T02 only tier A unattended, X prohibited · T03 accepts pd/cc0/cc-by/cc-by-sa with obligations · T04 rejects NC/ND/missing/unknown/class mismatch · T05 restrictions, pd+copyrighted conflict, missing attribution · T06 end-to-end: read-only raw, SHA-256, REVIEW provenance, HTML-stripped attribution, ledger row, exactly one GET + one DOWNLOAD · T07 idempotent rerun · T08 size and SHA-1 mismatch fail closed with no residue · T09 six ineligible candidates screened with reasons and no download · T10 non-automatable class stops before network · T11 job schema/caps/channel · T12 deterministic selection + max_items · T13 class must match licence · T14 HTTPS-only, download cap, response cap.
Agent-008 regression: 54/54 still pass.

## 5. Live proof attempt (real, this session)

```
$ python3 -m sourcing acquire --job sourcing/jobs/commons_pd_anime_proof_v1.json --out <scratchpad>/live_proof
{"status": "FAIL_CLOSED", "code": "TRANSPORT_UNREACHABLE",
 "detail": "https://commons.wikimedia.org/w/api.php?...gsrsearch=Namakura+Gatana+filetype%3Avideo...: <urlopen error Tunnel connection failed: 403 Forbidden>"}
exit=2   at 2026-10-15T01:56:31Z
```

A host probe from the container showed GitHub and package registries reachable. `commons.wikimedia.org`, `upload.wikimedia.org`, `archive.org`, `api.openverse.org`, `www.loc.gov` and `download.blender.org` were all denied. No item was acquired, no partial file was left and no ledger row was written. No result has been simulated in place of the live run.

Proof target: `Namakura Gatana` (1917), one of the earliest surviving Japanese animated films. The job selects it only if Commons itself publishes a `pd` licence code with no restrictions for a video file of it. If Commons publishes no such file, the job fails `NO_ELIGIBLE_SOURCE` and records each candidate's reason. The job does not change its target by itself. Its Japanese copyright status is reported as contested in secondary sources, so the item would stay REVIEW for a human rights check whatever the gate says.

## 6. To complete the live proof

1. Add `commons.wikimedia.org` and `upload.wikimedia.org` to the cloud environment's allowed domains (Network access in the environment settings), or run the same command on any machine with normal internet access.
2. Run `python3 -m sourcing acquire --job sourcing/jobs/commons_pd_anime_proof_v1.json --out <dir>`.
3. Commit `discovery_report.json`, `provenance.json` and the ledger row as evidence. Do not commit the binary.
4. A human reviews the provenance and rights record and approves the exact SHA-256, or rejects it.

## 7. Not done / boundaries

No Supabase or n8n reads or writes. No paid or provider calls. No billing changes. No binaries committed. No publication. No tier B/C/X automation. No registry schema, which comes later with the operational source registry (stable IDs: source item → franchise → segment → clip candidate → edit → published short). Mikko & Lumi, Agent-000…008, C1 canon: untouched.

Rollback: revert the commit. Nothing outside the repo was changed.

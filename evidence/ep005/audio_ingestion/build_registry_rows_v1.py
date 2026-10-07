#!/usr/bin/env python3
"""Build the three APPROVED asset_registry rows for the EP005 ElevenLabs audio (exact identities, NO generic aliases).
Usage: build_registry_rows_v1.py <final_measure.json> <rows out.json>   (run from the repo root)"""
import json, sys
meas = {m['production_id']: m for m in json.load(open(sys.argv[1]))}
el = {c['target_asset_id'] + ':' + c['candidate_id'][-1]: c for c in json.load(open('evidence/ep005/elevenlabs_candidates/EP005_ELEVENLABS_CANDIDATES_MANIFEST_v1.json'))['candidates']}
mast = {m['production_id']: m for m in json.load(open('evidence/ep005/audio_mastering/EP005_MASTERING_MANIFEST_v1.json'))['masters']}
SPEC = [  # production id, selected variant, name, subtype, role, storage key, original TBD requirement, loop
    ('AMB-BATHROOM-QUIET-v01', 'C', 'Bathroom quiet ambience', 'AMBIENCE', 'AMBIENCE_BED', 'audio/ambience/AMB-BATHROOM-QUIET-v01.wav', 'TBD::AUDIO::AMBIENCE', True),
    ('FOLEY-CLOTH-SOFT-v01', 'C', 'Soft microfiber cloth wipe', 'FOLEY', 'FOLEY', 'audio/foley/FOLEY-CLOTH-SOFT-v01.wav', 'TBD::AUDIO::FOLEY_CLOTH', False),
    ('SFX-COMPLETION-POP-v01', 'A', 'Soft completion pop', 'SFX', 'COMPLETION_SFX', 'audio/sfx/SFX-COMPLETION-POP-v01.wav', 'TBD::AUDIO::COMPLETION_SFX', False)]
rows = []
for pid, var, name, sub, role, key, req, loop in SPEC:
    c = el[f'{pid}:{var}']; f = meas[pid]; a = f['after_48k_final']; ms = mast[pid]
    rows.append({
        'asset_id': pid, 'asset_name': name, 'asset_type': 'AUDIO', 'asset_subtype': sub, 'version': 'v01', 'status': 'APPROVED',
        'aliases': [], 'storage_path': 'production-assets/' + key, 'source_url': None,
        'metadata_json': {
            'canon_scope': 'MIKKO_LUMI_PRODUCTION_AUDIO', 'asset_role': role, 'series_reusable': True, 'first_used_in': 'EP-CANDIDATE-005',
            'satisfies_former_requirement': req, 'purpose': f'{name} (reusable, EP005 first use)',
            'source': 'ElevenLabs', 'provider': 'ElevenLabs', 'model': 'eleven_text_to_sound_v2',
            'tool': 'ElevenLabs MCP creative_run_flow_nodes (sfx node), generations_count=1',
            'source_candidate_id': c['candidate_id'], 'source_generation_id': c['generation_id'], 'source_session_id': c['session_id'], 'source_flow_id': c['flow_id'],
            'source_generated_at_utc': c['generated_at_utc'], 'source_prompt': c['prompt'], 'source_requested_duration_seconds': c['requested_duration_seconds'],
            'source_loop_setting': c['loop'], 'source_prompt_influence': c['prompt_influence'], 'source_credits_reported': c['credits_reported'],
            'source_original_file': 'MP3 128 kbps 44.1 kHz stereo (original provider download)', 'source_original_sha256': c['sha256_original'], 'source_original_bytes': c['bytes'],
            'mastered_review_sha256': ms['master_sha256'], 'mastered_review_bytes': ms['master_bytes'],
            'mastering_summary': ms['ffmpeg_filter_chain'], 'mastering_gain_db': ms['gain_db'],
            'mastering_evidence': 'evidence/EP005_SELECTED_AUDIO_MASTERING_v1.0.md (commit 4abcd0c); recipes in evidence/ep005/audio_mastering/ and evidence/ep005/audio_ingestion/',
            'conversion': '44.1 kHz -> 48 kHz via libsoxr precision 28, 24-bit PCM, channel layout preserved' + ('; loop-aware' if loop else ''),
            'format': 'wav', 'codec': a['codec'], 'sample_rate': a['sample_rate'], 'channels': a['channels'], 'bits': a['bits'], 'duration_s': a['duration_s'],
            'sample_peak_dBFS': a['sample_peak_dBFS'], 'true_peak_dBTP': a['true_peak_dBTP'], 'rms_dBFS': a['rms_dBFS'],
            **({'integrated_LUFS': a['integrated_LUFS'], 'seamless_loop': True} if loop else ({'integrated_LUFS': a['integrated_LUFS']} if role == 'FOLEY' else {})),
            'bytes': f['final_bytes'], 'sha256': f['final_sha256'],
            'human_approved': True, 'approval_authority': 'Gilang', 'approval_date': '2026-10-07', 'approval_record': 'ENG-20261007-EP005-AUDIO-INGESTION',
            'rights_status': 'UNRECONCILED: ElevenLabs plan/commercial-use basis and whether connector workspace a2a81ab0f7fd406cb3fff9eef8e173c2 is the VA account are not yet verified (see evidence); recorded for transparency, does not affect matching'},
        'notes': f'EP005 human-approved production audio ({name}). Exact bytes governed by metadata_json.sha256; provenance back to ElevenLabs generation {c["generation_id"]}.'})
json.dump(rows, open(sys.argv[2], 'w'), indent=1, ensure_ascii=False)
for r in rows: print(r['asset_id'], '|', r['asset_name'], '|', r['asset_type'], r['asset_subtype'], '|', r['storage_path'], '| aliases', r['aliases'], '| sha', r['metadata_json']['sha256'][:16])

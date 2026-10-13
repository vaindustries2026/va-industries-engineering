'use strict';
// SYNTHETIC fixtures for local/pin-data tests only. Ids, references and scene text are invented test data, never a real observation.
const CAND = '11111111-1111-4111-8111-111111111111';
const TITLE = '22222222-2222-4222-8222-222222222222';
const OTHER_TITLE = '33333333-3333-4333-8333-333333333333';
const NOW = '2026-10-13T06:00:00.000Z';
const upstream = (o) => Object.assign({ research_candidate_id: CAND, candidate_status: 'READY', candidate_title_id: TITLE, title_id: TITLE, title_status: 'READY', display_title: 'SYNTHETIC TEST TITLE', start_year: 2000, franchise_status: 'READY' }, o || {});
const scene = (o) => Object.assign({
  start: '03:10', end: '04:05', characters_present: ['Synthetic Hero', 'Synthetic Rival'], scene_summary: 'Synthetic test scene: two rivals face each other after a long separation.',
  scene_function: 'Turning point', why_scene_matters: 'Synthetic: shows how a rivalry changes the direction of the arc.', possible_editorial_angles: ['rivalry payoff', 'then vs now'],
  context_requirement: 'Viewer should know the two characters are rivals.', spoiler_level: 'MEDIUM', visual_strength: 0.8, nostalgia_signal: 0.6, editorial_strength: 'EDITORIALLY_STRONG', timestamps_human_verified: true }, o || {});
const intake = (o) => Object.assign({
  research_candidate_id: CAND, anime_title_id: TITLE,
  episode: { season_number: 1, episode_number: 12, episode_variant: 'TV', episode_title: 'Synthetic Episode', duration_seconds: 1440 },
  source: { platform: 'HUMAN_RESEARCH_OBSERVATION', reference: 'human-observation:synthetic-0001', research_access_basis: 'HUMAN_VIEWED_LICENSED_PLATFORM', observed_at: '2026-10-13T05:00:00Z', observer: 'TEST' },
  scenes: [scene()] }, o || {});
// v0.1.1 validation mode (source outside the CF-001 batch). SYNTHETIC names: local tests only.
const vintake = (o) => Object.assign({
  validation_mode: 'CF002_VALIDATION_SOURCE_OUTSIDE_CF001_BATCH',
  catalog: { franchise: { normalised_key: 'synthetic validation franchise', display_name: 'Synthetic Validation Franchise' }, title: { normalised_title_key: 'synthetic validation title', display_title: 'Synthetic Validation Title', media_type: 'TV' } },
  episode: { season_number: 2, episode_number: 7, episode_variant: 'TV', episode_title: 'Synthetic Validation Episode' },
  source: { platform: 'OFFICIAL_SYNTHETIC_CHANNEL', reference: 'https://example.org/watch/synthetic-clip', research_access_basis: 'PUBLIC_OFFICIAL_UPLOAD', observed_at: '2026-10-13T05:00:00Z', observer: 'VA_HUMAN_RESEARCHER_01' },
  scenes: [scene({ start: '00:00', end: '02:10', timestamps_human_verified: true })] }, o || {});
module.exports = { vintake, CAND, TITLE, OTHER_TITLE, NOW, upstream, scene, intake };

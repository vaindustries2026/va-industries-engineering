# CF-002 source and research rules

## Research access is not publication permission
CF-002 records that a human observed a scene for research. It never sets, infers or implies any permission. `publication_source_status` stays UNKNOWN (fail closed). No AI, workflow or deterministic rule may certify legal permission. CF-005 owns rights.

## Crunchyroll and similar services: reference only
Allowed: a human watches through their own legitimate access and records the observation (platform, episode locator, timestamps, original summary). Forbidden for CF-002: downloading protected video, bypassing DRM, circumventing access controls, extracting auth secrets, reusing browser or session cookies in n8n, automating credential theft, or storing media or transcripts. A timestamp is never fabricated; with no authorised exact observation the run fails closed or the scene is not persisted.

## Experimental workflow WStqWRlqax7iocOx (read-only, not modified)
| Pattern | Class | Note |
|---|---|---|
| Fail-closed validation | KEEP_PATTERN | reused throughout |
| Deterministic timestamp parser | KEEP_PATTERN | basis of Normalise Boundaries |
| Mock-branch testing | KEEP_PATTERN | pinned-data tests |
| "Analysis only, no rights opinion" wording | KEEP_PATTERN | carried into rules above |
| MM:SS to integer ms, field mapping | ADAPT_PATTERN | ms integers, mapped to the new tables |
| Paid Gemini call | REJECT_PATTERN | no model call in v0.1 |
| Hard-wired YouTube URL | REJECT_PATTERN | source is a structured human observation |
| Model-owned timestamps | REJECT_PATTERN | code owns timestamps |
| No persistence or provenance | REJECT_PATTERN | everything persisted with provenance |

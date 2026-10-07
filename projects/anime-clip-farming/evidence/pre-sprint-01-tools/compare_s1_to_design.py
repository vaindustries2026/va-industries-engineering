#!/usr/bin/env python3
"""Object-level and line-level comparison of migrations/0001_cf_sprint01.sql
against the accepted Sprint 0 design (git 5190db5). Prints a Markdown report."""
import difflib, re, subprocess, sys, pathlib

REPO = pathlib.Path('/home/claude/va-industries-engineering')
PKG = 'projects/anime-clip-farming/architecture/data-contracts'
design = subprocess.run(['git', '-C', str(REPO), 'show', f'5190db5:{PKG}/migrations-draft/0001_cf_backbone.DESIGN_ONLY.sql'],
                        check=True, capture_output=True, text=True).stdout
s1 = (REPO / PKG / 'migrations/0001_cf_sprint01.sql').read_text()

def objects(sql):
    """Map object key -> exact statement text for types, tables, functions."""
    out = {}
    for m in re.finditer(r'^CREATE TYPE (cf\.\w+) AS ENUM \(.*?\);', sql, re.M | re.S):
        out['type ' + m.group(1)] = m.group(0)
    for m in re.finditer(r'^CREATE TABLE (cf\.\w+) \(\n.*?\n\);', sql, re.M | re.S):
        out['table ' + m.group(1)] = m.group(0)
    for m in re.finditer(r'^CREATE FUNCTION (cf\.\w+)\(.*?\nEND \$\$;', sql, re.M | re.S):
        out['function ' + m.group(1)] = m.group(0)
    for m in re.finditer(r"^  \('(\w+)', '(\w+)', '(\w+)', (NULL|'G\d'), (NULL|'\w+'), '(\w+)'\)[,;]", sql, re.M):
        out[f'transition {m.group(1)} {m.group(2)}->{m.group(3)}'] = m.group(0)[:-1]
    for m in re.finditer(r"^    \('(\w+)',\s+'(\w+)',\s+'(\w+)',\s+(ARRAY\[.*?\](?:::text\[\])?)\),?$", sql, re.M):
        out['trigger set cf.' + m.group(1)] = m.group(0).rstrip(',')
    for m in re.finditer(r'^COMMENT ON (SCHEMA|TABLE) ([\w.]+) IS .*?;$', sql, re.M):
        out[f'comment {m.group(1).lower()} {m.group(2)}'] = m.group(0)
    for m in re.finditer(r"^  \('(PUBLISH_ENABLED|PAID_CALLS_ENABLED|SCHEDULES_ENABLED)', false, '.*?'\)[,;]$", sql, re.M):
        out['seed system_flags ' + m.group(1)] = m.group(0)[:-1]
    return out

d, s = objects(design), objects(s1)
same = sorted(k for k in s if k in d and s[k] == d[k])
changed = sorted(k for k in s if k in d and s[k] != d[k])
new = sorted(k for k in s if k not in d)
omitted = sorted(k for k in d if k not in s)

print('### Object comparison (Sprint 1 file vs accepted Sprint 0 design)\n')
print(f'- Objects in the Sprint 1 file: **{len(s)}**; byte-identical to the design: **{len(same)}**; '
      f'changed: **{len(changed)}**; not in the design: **{len(new)}**.')
print(f'- Design objects left for later sprints: {len(omitted)}.\n')
print('| Object in 0001_cf_sprint01.sql | Versus design |')
print('|---|---|')
for k in sorted(s):
    print(f'| {k} | {"identical" if k in same else ("CHANGED" if k in changed else "NEW")} |')
if changed:
    print('\nChanged objects:')
    for k in changed:
        print('```diff'); print('\n'.join(difflib.unified_diff(d[k].split('\n'), s[k].split('\n'), lineterm='', n=1))); print('```')

# Line-level: every line of the Sprint 1 file that is not a verbatim design line
dl = design.split('\n'); sl = s1.split('\n')
sm = difflib.SequenceMatcher(a=dl, b=sl, autojunk=False)
added = []
for tag, i1, i2, j1, j2 in sm.get_opcodes():
    if tag in ('insert', 'replace'):
        for j in range(j1, j2):
            added.append((j + 1, sl[j]))
copied = sum(i2 - i1 for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag == 'equal')
non_comment_added = [(n, t) for n, t in added if t.strip() and not t.strip().startswith('--')]
print('\n### Line comparison\n')
print(f'- Sprint 1 file: {len(sl)} lines. Copied verbatim from the design, in order: {copied}. '
      f'Lines not in the design: {len(added)}, of which {len(non_comment_added)} are SQL (the rest are comments or blank).')
print('- Every SQL line that is not a verbatim copy:\n')
print('```sql')
for n, t in non_comment_added:
    print(f'{n:4d}  {t}')
print('```')
print('\nDesign objects not carried into Sprint 1 (by design, §15):\n')
print(', '.join(k.replace('transition ', '') if k.startswith('transition') else k for k in omitted if not k.startswith('transition')))
print(f'\nplus {sum(1 for k in omitted if k.startswith("transition"))} allowed_transitions rows for the later object types.')

'use strict';
// Runs the exact Code-node source (common.js inlined by the build rule) against simulated n8n globals.
const fs = require('fs');
const path = require('path');
const SRC = path.join(__dirname, '..', 'src');
// Includes only the common.js units (top-level const/function) that the stage actually references, transitively.
function units(common) {
  const out = []; let cur = null;
  common.split('\n').forEach((l) => {
    const m = /^(?:const|function)\s+([A-Za-z0-9_]+)/.exec(l);
    if (m) { cur = { name: m[1], text: l }; out.push(cur); } else if (cur && !/^\/\/ ----/.test(l)) cur.text += '\n' + l;
  });
  return out;
}
function assemble(file) {
  const body = fs.readFileSync(path.join(SRC, file), 'utf8');
  if (!/^\/\/ @include common\n/m.test(body)) return body;
  const us = units(fs.readFileSync(path.join(SRC, 'common.js'), 'utf8'));
  const used = new Set();
  let text = body;
  let grew = true;
  while (grew) {
    grew = false;
    us.forEach((u) => { if (!used.has(u.name) && new RegExp('\\b' + u.name + '\\b').test(text)) { used.add(u.name); text += '\n' + u.text; grew = true; } });
  }
  const inc = us.filter((u) => used.has(u.name)).map((u) => u.text.trim()).join('\n');
  return body.replace(/^\/\/ @include common\n/m, '// ---- CF-002 shared helpers (tree-shaken) ----\n' + inc + '\n');
}
// nodes: { 'Node Name': [json,...] }; input: [json,...]; opts: { now: ISO, executed: [names] }
function run(file, input, nodes, opts) {
  opts = opts || {};
  const code = assemble(file);
  const wrap = (arr) => (arr || []).map((j) => ({ json: j }));
  const dollar = (name) => {
    if (!nodes || !nodes[name]) throw new Error('node not available: ' + name);
    const items = wrap(nodes[name]);
    return { first: () => items[0], all: () => items, isExecuted: !!(opts.executed ? opts.executed.indexOf(name) >= 0 : true) };
  };
  const inp = wrap(input);
  const $input = { first: () => inp[0], all: () => inp };
  const $now = opts.now ? { toISO: () => opts.now } : undefined;
  const fn = new Function('$input', '$', '$now', code);
  return fn($input, dollar, $now);
}
module.exports = { run, assemble };

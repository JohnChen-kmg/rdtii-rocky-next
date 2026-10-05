/* RDTII Rocky interface. Vanilla JS, no build step. Talks to the JSON API in rdtii_ui/. */
'use strict';

const TOKEN = document.querySelector('meta[name=rdtii-token]').content;
const $ = (sel, el = document) => el.querySelector(sel);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

async function api(path, opts = {}) {
  const r = await fetch(path, { ...opts, headers: { 'Content-Type': 'application/json', 'X-RDTII-Token': TOKEN, ...(opts.headers || {}) } });
  let j = null;
  try { j = await r.json(); } catch (e) { j = { error: r.statusText }; }
  if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
  return j;
}

const S = { health: null, runs: [], run: null, rows: [], notes: {}, filters: { economy: '', indicator: '', tag: '', q: '' }, sort: { col: '', dir: 1 }, sel: null, picker: null };

/* ---------- sticky header height, so the sidebar pins just below it ---------- */
function fixTop() {
  const t = $('#topfix');
  if (t) document.documentElement.style.setProperty('--top-h', `${t.offsetHeight}px`);
}
window.addEventListener('resize', fixTop);
window.addEventListener('load', fixTop);

/* ---------- tabs ---------- */
function showTab(name) {
  const b = document.querySelector(`#tabs button[data-tab="${name}"]`);
  if (b) b.click();
}
$('#tabs').addEventListener('click', (e) => {
  const b = e.target.closest('button[data-tab]');
  if (!b) return;
  document.querySelectorAll('#tabs button').forEach((x) => x.classList.toggle('active', x === b));
  document.querySelectorAll('.tab').forEach((t) => { t.hidden = t.id !== `tab-${b.dataset.tab}`; });
  renderOutline(b.dataset.tab);
  if (b.dataset.tab === 'other') loadOther();
  if (b.dataset.tab === 'scrape' && !SC.loaded) loadScrape();
  if (b.dataset.tab === 'cn' && !CN.loaded) loadChina();
  if (b.dataset.tab === 'extract' && !EX.loaded) loadExtract();
});

/* ---------- the Overview: its buttons open a page, a block, or the example row ---------- */
function jumpToBlock(tab, title) {
  showTab(tab);
  setTimeout(() => {
    const bl = [...document.querySelectorAll(`#tab-${tab} .block h2`)].find((h) => h.textContent.includes(title));
    if (!bl) return;
    const top = bl.getBoundingClientRect().top + window.scrollY - (($('#topfix') || {}).offsetHeight || 92) - 10;
    window.scrollTo({ top, behavior: 'smooth' });
  }, 60);
}
function bindOverview() {
  document.querySelectorAll('#tab-overview [data-go]').forEach((b) => b.addEventListener('click', (e) => {
    e.stopPropagation();
    if (b.dataset.block) jumpToBlock(b.dataset.go, b.dataset.block); else { showTab(b.dataset.go); window.scrollTo({ top: 0 }); }
  }));
  document.querySelectorAll('#tab-overview [data-example-row]').forEach((b) => b.addEventListener('click', async (e) => {
    e.stopPropagation();
    S.filters = { economy: b.dataset.exampleRow, indicator: b.dataset.indicator, tag: '', q: '' };
    S.sort = { col: '', dir: 1 };
    if (S.run) await loadRows();
    jumpToBlock('map', 'Output');
  }));
}

/* ---------- the Overview's cost report ----------
   One data block in the page (#cost-data) feeds the price table, the finale's bill, the time table and the
   calculator, so no two of them can disagree. The calculator scales the finale's own bill, economy by
   economy, by the prices of that table: with the finale's models it gives the finale's bill, the careful
   reading doubled (the finale read in the batch lane at half price; a run from this tool reads live). */
const COST = (() => { try { return JSON.parse($('#cost-data').textContent); } catch (e) { return null; } })();
const CALC = { econ: new Set(['SG']), pick: null };
const costModel = (id) => COST.models.find((m) => m.id === id);
const costWorkers = (id) => (COST.providers.find((p) => p.id === costModel(id).provider) || {}).workers || 1;
const isEst = (m, key) => (m.est || []).includes(key);
const money = (x) => `$${Number(x).toFixed(2)}`;
const thousands = (x) => Number(x).toLocaleString('en-US');
/* a price per 1,000 calls: two decimals when measured, rounder and marked when estimated */
const price = (m, k) => { const v = m.usd[k]; if (!isEst(m, `usd.${k}`)) return v === 0 ? '0' : v.toFixed(2); return `≈ ${v < 10 && v % 1 ? v.toFixed(2) : Math.round(v)}`; };
/* minutes as people say them: to the minute under an hour, to five minutes under ten hours, to the half hour beyond */
function span(min) {
  if (min < 0.5) return 'under 1 min';
  if (min < 59.5) return `${Math.round(min)} min`;
  const step = min < 600 ? 5 : 30; const r = Math.round(min / step) * step;
  return r % 60 ? `${Math.floor(r / 60)} h ${r % 60} min` : `${r / 60} h`;
}

/* one economy with a model per step: dollars and minutes for every row of a run */
const PLAN_ROWS = ['scrape', 'extract', 'index', 'select', 'screen', 'read', 'recheck', 'tiebreak', 'translate', 'scores'];
const MODEL_ROWS = ['select', 'screen', 'read', 'recheck', 'tiebreak', 'translate', 'scores'];
function costPlan(e, pick) {
  const F = COST.finale.models;
  const ratio = (id, k, ref) => { const base = costModel(ref).usd[k]; return base ? costModel(id).usd[k] / base : 0; };
  const mins = (calls, id, k) => calls * costModel(id).sec[k] / costWorkers(id) / 60;
  // the finale billed the re-check and the tie-break together: split by calls times the table's price
  const d = e.calls.recheck * costModel(F.recheck).usd.recheck, tb = e.calls.tiebreak * costModel(F.tiebreak).usd.recheck;
  const share = d + tb ? d / (d + tb) : 0;
  return {
    scrape: { usd: 0, min: e.documents * e.scrape_sec / 60 + e.scrape_pause },
    extract: { usd: 0, min: e.extract_min },
    index: { usd: 0, min: e.provisions / COST.index_per_sec / 60 + 1 },   // the meaning index, plus a minute for the keyword index
    select: { usd: 0, min: 0.2 },
    screen: { calls: e.calls.screen, usd: e.usd.screen * ratio(pick.screen, 'screen', F.screen), min: mins(e.calls.screen, pick.screen, 'screen') },
    read: { calls: e.calls.read, usd: e.usd.read * COST.finale.read_live * ratio(pick.read, 'read', F.read), min: mins(e.calls.read, pick.read, 'read') },
    recheck: { calls: e.calls.recheck, usd: e.usd.verify * share * ratio(pick.recheck, 'recheck', F.recheck), min: mins(e.calls.recheck, pick.recheck, 'recheck') },
    tiebreak: { calls: e.calls.tiebreak, usd: e.usd.verify * (1 - share) * ratio(pick.tiebreak, 'recheck', F.tiebreak), min: mins(e.calls.tiebreak, pick.tiebreak, 'recheck') },
    // translation is the re-check model's work; a piece takes about as long as a reading
    translate: { calls: e.calls.translate, usd: e.usd.translate * ratio(pick.recheck, 'translate', F.translate), min: mins(e.calls.translate, pick.recheck, 'read') },
    scores: { usd: e.usd.scores * ratio(pick.read, 'read', F.read), min: 0.3 },
  };
}
const planSum = (plan, keys, f) => keys.reduce((s, k) => s + (plan[k][f] || 0), 0);
const finalePick = () => { const m = COST.finale.models; return { screen: m.screen, read: m.read, recheck: m.recheck, tiebreak: m.tiebreak }; };

function renderCost() {
  if (!COST || !$('#cost-prices')) return;
  const F = COST.finale, label = (id) => costModel(id).label;
  const used = { screen: [F.models.screen], read: [F.models.read], recheck: [F.models.recheck, F.models.tiebreak], translate: [F.models.translate] };
  const cols = [['screen', 'Quick screen'], ['read', 'Careful reading'], ['recheck', 'Re-check, tie-break'], ['translate', 'Translation']];
  /* a table with one row per model, the provider named once */
  const byProvider = (cells) => COST.providers.map((p) => {
    const ms = COST.models.filter((m) => m.provider === p.id);
    return ms.map((m, i) => `<tr class="${i ? '' : 'first'}">${i ? '' : `<td class="prov" rowspan="${ms.length}">${esc(p.name)}${p.local ? '<small>on this machine</small>' : ''}</td>`}<td>${esc(m.label)}${m.few ? ' <span class="few">8 calls</span>' : ''}</td>${cells(m, p, i, ms.length)}</tr>`).join('');
  }).join('');
  $('#cost-prices').innerHTML = `<table class="dist"><thead><tr><th>Provider</th><th>Model</th>${cols.map((c) => `<th class="num">${c[1]}</th>`).join('')}</tr></thead><tbody>${
    byProvider((m) => cols.map(([k]) => `<td class="num"><i class="${isEst(m, `usd.${k}`) ? 'est' : ''} ${used[k].includes(m.id) ? 'used' : ''}">${price(m, k)}</i></td>`).join(''))}</tbody></table>`;

  const fcols = [['screen', 'Quick screen', label(F.models.screen)], ['read', 'Careful reading', `${label(F.models.read)}, batch lane`], ['verify', 'Re-check, tie-break', `${label(F.models.recheck)}, ${label(F.models.tiebreak)}`],
    ['translate', 'Translation', label(F.models.translate)], ['scores', 'Scores', label(F.models.read)], ['total', 'Total', '']];
  const frow = (name, usd, cls) => `<tr class="${cls || ''}"><td>${name}</td>${fcols.map(([k]) => `<td class="num">${usd[k].toFixed(2)}</td>`).join('')}</tr>`;
  $('#cost-finale').innerHTML = `<table class="dist"><thead><tr><th>Economy</th>${fcols.map((c) => `<th class="num">${c[1]}${c[2] ? `<small>${esc(c[2])}</small>` : ''}</th>`).join('')}</tr></thead><tbody>${
    F.economies.map((e) => frow(esc(e.name), e.usd)).join('')}${F.other.map((o) => frow(`${esc(o.name)} <span class="muted">${esc(o.scope)}</span>`, o.usd)).join('')}${frow('<b>Whole run</b>', F.total, 'total')}</tbody></table>`;

  const fin = finalePick();
  $('#cost-hours').innerHTML = `<table class="dist"><thead><tr><th>Economy</th><th class="num">Documents</th><th class="num">Provisions</th><th class="num"><span class="st">1</span>Scraping</th><th class="num"><span class="st">2</span>Extraction</th><th class="num"><span class="st">3</span>Mapping: index</th><th class="num"><span class="st">3</span>Mapping: model steps</th><th class="num">Total</th></tr></thead><tbody>${
    F.economies.map((e) => { const pl = costPlan(e, fin);
      return `<tr><td>${esc(e.name)}</td><td class="num">${thousands(e.documents)}</td><td class="num">${thousands(e.provisions)}</td><td class="num">${span(pl.scrape.min)}</td><td class="num">${span(pl.extract.min)}</td><td class="num">${span(pl.index.min)}</td><td class="num">${span(planSum(pl, MODEL_ROWS, 'min'))}</td><td class="num"><b>${span(planSum(pl, PLAN_ROWS, 'min'))}</b></td></tr>`; }).join('')}</tbody></table>`;
  const sg = F.economies.find((e) => e.id === 'SG'), local = COST.providers.find((p) => p.local), host = COST.providers.find((p) => p.id === costModel(F.models.read).provider);
  if (sg && local && host) $('#cost-local-line').textContent = `${sg.name}’s model steps: ${span(planSum(costPlan(sg, fin), MODEL_ROWS, 'min'))} on ${host.name}, ${host.workers} calls at a time; about ${span(planSum(costPlan(sg, local.roles), MODEL_ROWS, 'min'))} on ${local.name}, one at a time.`;

  const scols = [['screen', 'Quick screen'], ['read', 'Careful reading'], ['recheck', 'Re-check, tie-break']];
  $('#cost-seconds').innerHTML = `<table class="dist"><thead><tr><th>Provider</th><th>Model</th>${scols.map((c) => `<th class="num">${c[1]}</th>`).join('')}<th class="num">Calls at a time</th></tr></thead><tbody>${
    byProvider((m, p, i, n) => scols.map(([k]) => `<td class="num"><i class="${isEst(m, `sec.${k}`) ? 'est' : ''}">${isEst(m, `sec.${k}`) ? `≈ ${m.sec[k] % 1 ? m.sec[k].toFixed(1) : m.sec[k]}` : m.sec[k].toFixed(1)}</i></td>`).join('') + (i ? '' : `<td class="num prov" rowspan="${n}">${p.workers}</td>`))}</tbody></table>`;
  buildCalc();
}

/* the calculator: tick economies, give each step a model, read dollars and hours */
function buildCalc() {
  const F = COST.finale, host = $('#calc');
  if (!CALC.pick) CALC.pick = finalePick();
  const finaleProvider = costModel(F.models.read).provider;
  const options = (key) => COST.providers.map((p) => `<optgroup label="${esc(p.name)}">${COST.models.filter((m) => m.provider === p.id).map((m) => {
    const k = key === 'tiebreak' ? 'recheck' : key;
    return `<option value="${esc(m.id)}">${esc(m.label)} · ${m.usd[k] === 0 ? '$0' : `${isEst(m, `usd.${k}`) ? '≈ ' : ''}$${price(m, k).replace('≈ ', '')}`}</option>`; }).join('')}</optgroup>`).join('');
  host.innerHTML = `
    <div class="calc-line"><span class="calc-label">Economies</span><div class="picks">${F.economies.map((e) => `<label class="radio big"><input type="checkbox" name="calc-econ" value="${e.id}"> <span class="name">${esc(e.name)}</span></label>`).join('')}</div></div>
    <div class="calc-line"><span class="calc-label">Models</span><div class="picks">${COST.providers.map((p) => `<label class="radio big"><input type="radio" name="calc-preset" value="${p.id}"> <span class="name">${esc(p.name)}</span>${p.id === finaleProvider ? ' <span class="sub">the finale</span>' : p.local ? ' <span class="sub">on this machine</span>' : ''}</label>`).join('')}</div></div>
    <div class="calc-steps">${COST.steps.map((s) => `<label class="calc-step"><span><span class="letter">${s.letter}</span><b>${esc(s.title)}</b></span><select data-step="${s.key}" aria-label="${esc(s.title)}">${options(s.key)}</select></label>`).join('')}</div>
    <div class="calc-hint">Beside each model: US dollars per 1,000 calls of that step.</div>
    <div id="calc-out"></div>`;
  host.querySelectorAll('input[name=calc-econ]').forEach((inp) => inp.addEventListener('change', () => { if (inp.checked) CALC.econ.add(inp.value); else CALC.econ.delete(inp.value); syncCalc(); }));
  host.querySelectorAll('input[name=calc-preset]').forEach((inp) => inp.addEventListener('change', () => { CALC.pick = { ...COST.providers.find((p) => p.id === inp.value).roles }; syncCalc(); }));
  host.querySelectorAll('select[data-step]').forEach((sel) => sel.addEventListener('change', () => { CALC.pick[sel.dataset.step] = sel.value; syncCalc(); }));
  syncCalc();
}

/* the controls follow CALC, then the result is drawn again; the controls themselves are never rebuilt, so a select keeps the focus */
function syncCalc() {
  const F = COST.finale, host = $('#calc'), out = $('#calc-out');
  const same = (roles) => COST.steps.every((s) => CALC.pick[s.key] === roles[s.key]);
  host.querySelectorAll('input[name=calc-econ]').forEach((inp) => { inp.checked = CALC.econ.has(inp.value); inp.parentElement.classList.toggle('on', inp.checked); });
  host.querySelectorAll('input[name=calc-preset]').forEach((inp) => { inp.checked = same(COST.providers.find((p) => p.id === inp.value).roles); inp.parentElement.classList.toggle('on', inp.checked); });
  host.querySelectorAll('select[data-step]').forEach((sel) => { sel.value = CALC.pick[sel.dataset.step]; });
  const econ = F.economies.filter((e) => CALC.econ.has(e.id));
  if (!econ.length) { out.innerHTML = '<p class="calc-empty">Tick an economy.</p>'; return; }
  const plans = econ.map((e) => costPlan(e, CALC.pick));
  const sum = (k, f) => plans.reduce((s, pl) => s + (pl[k][f] || 0), 0);
  const all = (f) => PLAN_ROWS.reduce((s, k) => s + sum(k, f), 0);
  const name = (id) => esc(costModel(id).name);
  const docs = thousands(econ.reduce((s, e) => s + e.documents, 0)), prov = thousands(econ.reduce((s, e) => s + e.provisions, 0));
  const rows = [
    ['<span class="st">1</span>Scraping', '<span class="muted">no model</span>', `${docs} documents`, 'scrape'],
    ['<span class="st">2</span>Extraction', '<span class="muted">no model</span>', `${docs} documents`, 'extract'],
    ['<span class="st">3</span>Mapping: index', '<span class="muted">on this machine</span>', `${prov} provisions`, 'index'],
    ['<span class="letter">A</span>Candidate selection', '<span class="muted">on this machine</span>', '', 'select'],
    ...COST.steps.map((s) => [`<span class="letter">${s.letter}</span>${esc(s.title)}`, name(CALC.pick[s.key]), `${thousands(sum(s.key, 'calls'))} ${s.unit}`, s.key]),
    ['Translation', name(CALC.pick.recheck), `${thousands(sum('translate', 'calls'))} pieces`, 'translate'],
    ['Scores', name(CALC.pick.read), '', 'scores'],
  ];
  const paid = econ.reduce((s, e) => s + e.usd.total, 0);
  const names = econ.map((e) => e.name); const listed = names.length > 1 ? `${names.slice(0, -1).join(', ')} and ${names[names.length - 1]}` : names[0];
  out.innerHTML = `
    <div class="calc-totals"><div class="calc-total"><small>Money</small><b>${money(all('usd'))}</b></div><div class="calc-total"><small>Time</small><b>${span(all('min'))}</b></div></div>
    <div class="cost-table"><table class="dist"><thead><tr><th>Step</th><th>Model</th><th class="num">Calls</th><th class="num">Cost</th><th class="num">Time</th></tr></thead><tbody>${
      rows.map(([step, model, calls, k]) => `<tr><td>${step}</td><td>${model}</td><td class="num">${calls}</td><td class="num">${money(sum(k, 'usd'))}</td><td class="num">${sum(k, 'calls') === 0 && k === 'translate' ? '–' : span(sum(k, 'min'))}</td></tr>`).join('')}
      <tr class="total"><td><b>Total</b></td><td></td><td></td><td class="num"><b>${money(all('usd'))}</b></td><td class="num"><b>${span(all('min'))}</b></td></tr></tbody></table></div>
    ${econ.length > 1 ? `<div class="cost-table by-econ"><table class="dist"><thead><tr><th>Economy</th><th class="num">Cost</th><th class="num">Time</th></tr></thead><tbody>${
      econ.map((e, i) => `<tr><td>${esc(e.name)}</td><td class="num">${money(planSum(plans[i], PLAN_ROWS, 'usd'))}</td><td class="num">${span(planSum(plans[i], PLAN_ROWS, 'min'))}</td></tr>`).join('')}</tbody></table></div>` : ''}
    <ul>
      <li><b>An estimate</b>, from the finale’s run of each economy: its calls and its bill, nine indicators. Another model is priced by its ratio in the Money table.</li>
      <li>The careful reading is priced <b>live</b>. The finale paid ${money(paid)} for ${esc(listed)}, its reading at half price in Claude’s batch lane.</li>
      <li>Time assumes one economy after another, and no waiting on a provider’s rate limit.</li>
    </ul>`;
}

/* ---------- the sidebar outline: the active page's blocks, click to jump ---------- */
function renderOutline(tab) {
  document.querySelectorAll('#tabs .outline').forEach((o) => { o.innerHTML = ''; });
  if (tab === 'overview') {                    // the Overview lists its sections, not its blocks: Introduction, Workflow map, Cost report, Before you start
    const list = document.querySelector('#tabs .outline[data-for="overview"]');
    const marks = [...document.querySelectorAll('#tab-overview [data-outline]')];
    if (!list) return;
    list.innerHTML = marks.map((m, i) => `<button class="jump" data-mark="${i}">${m.dataset.num ? `<span class="num">${esc(m.dataset.num)}</span>` : ''}${esc(m.dataset.outline)}</button>`).join('');
    list.querySelectorAll('button.jump').forEach((btn) => btn.addEventListener('click', (e) => {
      e.stopPropagation();
      const m = marks[Number(btn.dataset.mark)]; if (!m) return;
      const top = m.getBoundingClientRect().top + window.scrollY - (($('#topfix') || {}).offsetHeight || 92) - 10;
      window.scrollTo({ top, behavior: 'smooth' });
    }));
    return;
  }
  const page = tab === 'cn' ? 'scrape' : tab;   // the China page has no outline of its own; Scraping's stays open above it
  const host = document.querySelector(`#tabs .outline[data-for="${page}"]`);
  const section = $(`#tab-${page}`);
  if (!host || !section) return;
  const blocks = [...section.querySelectorAll(':scope > .block, :scope > details.block, :scope > #cn-body > .block, :scope > .guide-row > .block')];
  host.innerHTML = blocks.map((bl, i) => {
    const h = bl.querySelector('h2'); if (!h) return '';
    const step = h.querySelector('.step'); const title = [...h.childNodes].filter((n) => n.nodeType === 3 || (n.nodeType === 1 && n.tagName !== 'BUTTON' && !n.classList.contains('step') && !n.classList.contains('fold') && !n.classList.contains('muted'))).map((n) => n.textContent).join('').trim();
    return `<button class="jump" data-block="${i}">${step ? `<span class="num">${esc(step.textContent)}</span>` : ''}${esc(title)}</button>`;
  }).join('');
  host.querySelectorAll('button.jump').forEach((btn) => btn.addEventListener('click', (e) => {
    e.stopPropagation();
    const bl = blocks[Number(btn.dataset.block)]; if (!bl) return;
    const go = () => {
      if (bl.tagName === 'DETAILS') bl.open = true;
      const top = bl.getBoundingClientRect().top + window.scrollY - (($('#topfix') || {}).offsetHeight || 92) - 10;
      window.scrollTo({ top, behavior: 'smooth' });
    };
    if (section.hidden) { showTab(page); setTimeout(go, 30); } else go();   // from the China page: open Scraping first
  }));
}

/* ---------- header, engine banner, key fold ---------- */
async function loadHealth() {
  try { S.health = await api('/api/health'); } catch (e) { S.health = { error: e.message }; }
  renderTop();
}

/* the models an engine puts in each role, in plain words */
/* the line written at Start and carried with a run folder (notes.py): shown wherever the folder is listed */
const carried = (f) => (f && f.note ? `<span class="carried" title="${esc(f.noted ? 'written ' + f.noted : '')}">${esc(f.note)}</span>` : '');
/* an older run manifest names its engine "provider: model id"; show the model by its name */
const engineText = (s) => { const m = /^(anthropic|ollama|openai_compat): (.+)$/.exec(String(s)); return m ? (MODEL_NAMES[m[2]] || m[2]) : String(s); };
const MODEL_NAMES = { 'claude-sonnet-5': 'Claude Sonnet 5', 'claude-haiku-4-5': 'Claude Haiku 4.5', 'claude-opus-4-8': 'Claude Opus 4.8', 'qwen2.5:14b': 'Qwen 2.5 14B, local' };
const engineList = () => { const eng = (S.health || {}).engine || {}; return Array.isArray(eng.engines) ? eng.engines : []; };
const engineOf = (id) => engineList().find((e) => e.id === id) || null;
const modelOf = (e, id) => (e && (e.models || []).find((m) => m.id === id)) || null;
const heldKeys = () => (((S.health || {}).probes || {}).key || {}).names || {};
/* the engines the next mapping run calls: one per step once the steps are set, else the banner's */
function enginesInUse() {
  const eng = (S.health || {}).engine || {};
  const ids = MP.models ? Object.values(MP.models).map((x) => x.engine) : [eng.selected];
  return [...new Set(ids)].map(engineOf).filter(Boolean);
}
function roleLine(e) {
  const r = e.roles || {}; const nm = (m) => MODEL_NAMES[m] || (modelOf(e, m) ? `${e.model_prefix || ''}${modelOf(e, m).label}` : m) || '?';
  const same = r.mapper && r.mapper === r.verifier && r.mapper === r.escalation;
  if (same) return `${nm(r.mapper)} in every step: quick screen, reading, re-check and tie-break.`;
  return `screens and re-checks with ${nm(r.verifier)}, reads with ${nm(r.mapper)}, breaks ties with ${nm(r.escalation)}.`;
}

function renderTop() {
  const h = S.health || {};
  const eng = h.engine || { engines: [] };
  $('#engine').innerHTML = `<span class="muted small">Engine Selection:</span>` + eng.engines.map((e) =>
    `<label class="radio ${e.id === eng.selected ? 'on' : ''}" title="${esc(e.provider)} · mapper ${esc(e.roles?.mapper || '')}">
       <input type="radio" name="engine" value="${esc(e.id)}" ${e.id === eng.selected ? 'checked' : ''}> ${esc(e.label)}</label>`).join('')
    + (eng.engines.length ? '' : `<span class="muted small">no engines declared (stages/p3-map missing?)</span>`)
    + (eng.engines.length ? `<div class="roles">${eng.engines.filter((e) => e.id === eng.selected).map((e) => `<div class="on"><b>${esc(e.name || e.label)}</b> ${esc(roleLine(e))}${e.measured ? '' : ' <span class="chip warn">not measured</span>'}</div>`).join('')}<div>Sets every step of a run. Each step can be given another model under Run, below.</div></div>` : '');
  $('#engine').querySelectorAll('input[name=engine]').forEach((inp) => inp.addEventListener('change', async () => {
    try { await api('/api/engine', { method: 'POST', body: JSON.stringify({ id: inp.value }) }); MP.models = null; MP.checks = null; } catch (e) { alert(e.message); }
    await loadHealth(); renderMapRun();
  }));
  renderJobStrip();
  const p = h.probes || {};
  const dot = (ok) => `<span class="dot ${ok === true ? 'ok' : ok === false ? 'bad' : ''}"></span>`;
  const st = h.stages || {};
  const held = heldKeys();
  const needKeys = enginesInUse().filter((e) => e.key_env);
  $('#health').innerHTML = [
    ['Ollama', p.ollama?.ok, p.ollama?.ok ? `${p.ollama.host}, ${p.ollama.models.length} models` : (p.ollama?.error || 'not answering')],
    ['Tesseract', p.tesseract?.ok, p.tesseract?.path || p.tesseract?.hint],
    ['Chromium', p.chromium?.ok, p.chromium?.path || p.chromium?.hint],
    ['Key', needKeys.every((e) => held[e.key_env]), needKeys.length ? needKeys.map((e) => `${e.name}: ${held[e.key_env] ? 'key held in memory' : 'no key held'}`).join(', ') : 'no API key needed for the current choice'],
    ['Stages', st.p1?.present && st.p2?.present && st.p3?.present, Object.entries(st).map(([k, v]) => `${k}: ${v.present ? 'present' : 'missing'}`).join(', ')],
  ].map(([name, ok, tip]) => `<span class="item" title="${esc(tip)}">${dot(ok)}${name}</span>`).join('');
  $('#keyfold').classList.remove('folded');   // the key rows always stay in view
  // one row per hosted provider the current choice calls; with none, the first hosted engine's row, marked not needed
  const firstHosted = eng.engines.find((e) => e.key_env);
  const rows = needKeys.length ? needKeys : (firstHosted ? [firstHosted] : []);
  const aside = needKeys.length ? '' : ' <span class="small muted">(not needed for the current choice)</span>';
  const typing = [...document.querySelectorAll('#key input')].some((i) => i.value || i === document.activeElement);
  if (typing) return;   // a refresh must not wipe a key being typed
  $('#key').innerHTML = rows.map((e) => `<div class="keyrow"><span class="keylabel">${esc(e.label)} needs an API key:</span> ` + (held[e.key_env]
    ? `<span class="small muted">key held in memory for this process</span> <button class="btn small" data-key-clear="${esc(e.key_env)}">Forget</button>`
    : `<input type="password" data-key-input="${esc(e.key_env)}" placeholder="${esc(e.key_env)} (memory only, never written)" autocomplete="off"> <button class="btn" data-key-set="${esc(e.key_env)}">Hold</button>`) + `${aside}</div>`).join('');
  $('#key').querySelectorAll('[data-key-set]').forEach((btn) => btn.addEventListener('click', async () => {
    const inp = $(`#key input[data-key-input="${btn.dataset.keySet}"]`);
    try { await api('/api/key', { method: 'POST', body: JSON.stringify({ key: inp.value, name: btn.dataset.keySet }) }); } catch (e) { alert(e.message); }
    inp.value = ''; inp.blur();
    await loadHealth(); MP.checks = null; renderMapRun();
  }));
  $('#key').querySelectorAll('[data-key-clear]').forEach((btn) => btn.addEventListener('click', async () => {
    try { await api(`/api/key?name=${encodeURIComponent(btn.dataset.keyClear)}`, { method: 'DELETE' }); } catch (e) { alert(e.message); }
    await loadHealth(); MP.checks = null; renderMapRun();
  }));
}

/* ---------- Mapping · Set up ---------- */
async function loadPicker() {
  try { S.picker = await api('/api/map/indicators'); } catch (e) { $('#map-setup').innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  const pk = S.picker;
  const tc = pk.tier_counts || {};
  const flag = (i) => i.tier === 'B' ? `<span class="chip tier tier-b" title="${esc((pk.tiers || {}).B || '')}">not reviewed</span>`
    : i.tier === 'C' ? `<span class="chip tier tier-c" title="${esc((pk.tiers || {}).C || '')}">host criteria only</span>` : '';
  const practiceChip = (i) => i.practice_based ? `<span class="chip warn" title="${esc(i.practice_based)}">practice-based</span>` : '';
  $('#map-setup').innerHTML = `
    <div class="setup-row"><div class="setup-label">Indicators</div>
      <div class="stack-col">
      <details class="src-card picker"><summary><span class="sum">Indicator selection</span> <span class="muted">${pk.automated.length} of ${pk.in_scope} pre-selected; open to change</span></summary>
        <div class="pillars">${pk.pillars.map((p) => `
          <div class="pillar"><h4>${esc(p.label)}</h4>
            ${p.indicators.map((i) => `<label class="${i.automated ? '' : 'other'}">
              <input type="checkbox" value="${esc(i.id)}" ${i.automated ? 'checked' : ''}> <span class="id">${esc(i.id)}</span> ${esc(i.name)} ${flag(i)}${practiceChip(i)}</label>`).join('')}
          </div>`).join('')}
        </div>
        <div class="foot">${esc(pk.source)}</div>
      </details>
      </div>
    </div>
    <details class="notes-box" ${MP.notesOpen ? 'open' : ''}><summary>Note:</summary>
      <p>* <b>Input</b> is an Extraction output: the laws, their provisions and the reading status of each document.</p>
      <p>* <b>Economies</b> are those present in the input; the run maps only the ones ticked.</p>
      <p>* <b>Indicators</b>: the nine of pillars 6 and 7 are pre-selected; any other in-scope indicator can be ticked, and the host’s live task may fall in any pillar. A row mapped under a host-criteria-only rulebook should name that in Notes and clear a higher confidence before it is tagged NEW; the stage does not enforce this, so it is the reviewer’s rule.</p>
      <p>* <b>Practice-based</b> indicators (3.4, 5.3, 9.1) score facts from outside legislation, such as a blocked investment or company ownership; the legal dataset alone cannot settle them.</p>
      <p>* <b>How the indicators are computed, and what the tags mean:</b></p>
        <div class="tag-table plain">
      <p class="lead">Every indicator is computed the same way: one query from its name, definition and keywords; the same prompt, verification and NEW or KNOWN comparison for all ${pk.in_scope}. What differs is the rulebook the model is given.</p>
      <div class="table-wrap"><table class="rows tags"><thead><tr><th>Tag in the list</th><th>Indicators</th><th>What the rulebook carries</th></tr></thead><tbody>
        <tr><td><span class="chip tier tier-a">reviewed</span><div class="small muted">no tag shown: the pre-selected</div></td><td class="num">${tc.A ?? 9}</td><td><div class="parts"><span>Definition</span><span>Scoring tree</span><span>Coding rules</span><span>Disambiguation</span><span>Exceptions</span><span>Guide examples</span><span class="plus">Traps from real mistakes</span><span class="plus">Reviewed line by line</span></div><div class="small muted">Pillars 6 and 7, checked against the host’s methodology.</div></td></tr>
        <tr><td><span class="chip tier tier-b">not reviewed</span></td><td class="num">${tc.B ?? '?'}</td><td><div class="parts"><span>Definition</span><span>Scoring tree</span><span>Coding rules</span><span>Disambiguation</span><span>Exceptions</span><span>Guide examples</span></div><div class="small muted">Drafted from the guides, unchecked. An error repeats in every row mapped under the indicator, so its rows deserve a reviewer’s eye.</div></td></tr>
        <tr><td><span class="chip tier tier-c">host criteria only</span></td><td class="num">${tc.C ?? '?'}</td><td><div class="parts"><span>Definition</span><span>Scoring tree</span><span class="thin">Host criteria, copied by script</span></div><div class="small muted">No traps, no examples, no rules of our own. The model settles edge cases itself, so more rows need review; a row should name this in Notes and clear a higher confidence before NEW.</div></td></tr>
        <tr><td><span class="chip warn">practice-based</span></td><td class="num">3</td><td><div class="parts"><span class="ext">Facts outside legislation</span></div><div class="small muted">3.4, 5.3 and 9.1 score a blocked investment or company ownership and the like. The legal dataset shows the framework, not the practice.</div></td></tr>
      </tbody></table></div>
      <p class="small muted">Any rulebook can be raised to the reviewed level later, by review alone; the pipeline does not change.</p>
        </div>
    </details>`;
  const nb = $('#map-setup details.notes-box'); if (nb) nb.addEventListener('toggle', () => { MP.notesOpen = nb.open; });
  $('#map-setup').querySelectorAll('.pillar input').forEach((inp) => inp.addEventListener('change', () => { MP.checks = null; renderMapRun(); }));
  if ($('#mp-mode')) renderMapRun();   // the Thresholds line needs the picker
}


/* ---------- Mapping · Output ---------- */
async function loadRuns() {
  const j = await api('/api/map/runs');
  S.runs = j.runs;
  if (!S.run || !S.runs.find((r) => r.id === S.run)) S.run = S.runs[0]?.id || null;
  renderRunRow();
  if (S.run) await loadRows(); else $('#map-table').innerHTML = '<tr><td class="muted">No finished mapping run found. OUT_DIR points nowhere with rows.</td></tr>';
}

function renderRunRow() {
  const cur = S.runs.find((r) => r.id === S.run);
  $('#map-run-row').innerHTML = `<div class="setup-row"><div class="setup-label">Run</div>
    <div>
      <div class="row"><select id="run-select" class="wide-select">${S.runs.map((r) => `<option value="${esc(r.id)}" ${r.id === S.run ? 'selected' : ''}>${esc(r.name)}: ${r.rows} rows, ${r.economies.join(', ')}</option>`).join('')}</select>
        ${cur ? `<button class="btn small" data-open="${esc(cur.arm_paths[0])}">Open folder</button>
        ${cur.id.startsWith('outputs/map/') ? `<button class="btn small" data-clear="${esc(cur.arm_paths[0].replace(/[\\/]out[^\\/]*$/, ''))}" data-what="this run folder and its rows">Clear run</button>` : ''}` : ''}
      </div>
      ${cur && cur.kind === 'frozen' ? '<div class="muted small">Filed rows, read-only: review decisions are refused here.</div>' : ''}
      ${cur ? `<div class="record"><b class="record-title">Record</b><ul class="note-list">
        <li><b>What this is</b>: ${esc(cur.kind === 'fixture' ? 'a fixture slice of run_2026-09-27, shipped with the interface so the review screen works on a clean clone' : cur.kind === 'frozen' ? 'the filed rows of the submission, read-only' : 'the output of a run from this interface')}.</li>
        ${cur.note ? `<li><b>Run note</b>: ${esc(cur.note)}${cur.noted ? ` <span class="muted">(${esc(cur.noted)})</span>` : ''}</li>` : ''}
        ${cur.engine ? `<li><b>Engine</b>: ${esc(engineText(cur.engine))}.</li>` : ''}
        ${cur.cost_usd != null ? `<li><b>Recorded cost</b>: $${esc(Number(cur.cost_usd).toFixed(2))}, from the run manifest.</li>` : ''}
        ${cur.arms.length > 1 ? `<li><b>Arms</b>: ${cur.arms.length}, ${esc(cur.arms.join(', '))}; the rows of both are listed.</li>` : ''}
        ${cur.git ? `<li><b>Stage commit</b>: <code>${esc(cur.git.slice(0, 10))}</code>, the mapping stage that produced it.</li>` : ''}
        <span id="record-corpus"></span>
      </ul></div>` : ''}
    </div></div>`;
  bindClear('#map-run-row', () => { S.run = null; loadRuns(); });
  bindOpen('#map-run-row');
  $('#run-select').addEventListener('change', (e) => { S.run = e.target.value; S.sel = null; $('#map-detail').innerHTML = ''; loadRows(); renderRunRow(); });
}

async function loadRows() {
  const f = S.filters;
  const qs = new URLSearchParams({ run: S.run, economy: f.economy, indicator: f.indicator, tag: f.tag, q: f.q });
  let j;
  try { j = await api(`/api/map/rows?${qs}`); } catch (e) { $('#map-table').innerHTML = `<tr><td class="note">${esc(e.message)}</td></tr>`; return; }
  S.rows = j.rows; S.notes = j.corpus_notes || {};
  renderFilters(j);
  renderNotes();
  renderTable(j);
  loadExportSummary();
}

function renderFilters(j) {
  const f = S.filters;
  $('#map-filters').innerHTML = `<div class="setup-row"><div class="setup-label">Filter</div><div class="row">
    <label>Economy <select id="f-econ"><option value="">all</option>${j.economies.map(([c, n]) => `<option value="${c}" ${f.economy === c ? 'selected' : ''}>${esc(n)} (${c})</option>`).join('')}</select></label>
    <label>Indicator <select id="f-ind"><option value="">all</option>${j.indicators.map((i) => `<option ${f.indicator === i ? 'selected' : ''}>${esc(i)}</option>`).join('')}</select></label>
    <label>Tag <select id="f-tag"><option value="">all</option><option value="NEW" ${f.tag === 'NEW' ? 'selected' : ''}>NEW</option><option value="KNOWN" ${f.tag === 'KNOWN' ? 'selected' : ''}>KNOWN</option><option value="none" ${f.tag === 'none' ? 'selected' : ''}>no provision (blank)</option></select></label>
    <input type="search" id="f-q" placeholder="search law, quote, English…" value="${esc(f.q)}">
    <span class="muted">${j.shown} of ${j.total} rows</span></div></div>`;
  $('#f-econ').onchange = (e) => { f.economy = e.target.value; loadRows(); };
  $('#f-ind').onchange = (e) => { f.indicator = e.target.value; loadRows(); };
  $('#f-tag').onchange = (e) => { f.tag = e.target.value; loadRows(); };
  let t; $('#f-q').oninput = (e) => { clearTimeout(t); t = setTimeout(() => { f.q = e.target.value; loadRows(); }, 250); };
}

function renderNotes() {
  // the machine translations, one bullet per economy: how many provision texts the glosser flagged "not literal"
  const host = $('#record-corpus'); if (!host) return;
  const notes = Object.values(S.notes).sort((a, b) => a.economy.localeCompare(b.economy));
  const eng = [...new Set(S.rows.filter((r) => r['Language of Source'] === 'English').map((r) => r.Economy))].sort();
  if (!notes.length && !eng.length) { host.innerHTML = ''; return; }
  const line = (n) => `<li>${esc(n.economy)}: ${n.not_literal} of ${n.total} provision texts flagged “not literal”${n.rate > 0.5 ? ', the corpus OCR is rough' : ''}</li>`;
  host.innerHTML = `<li><b>Translations</b>: machine English, for review only. A “not literal” flag is a property of the corpus, not of any one row.
    <ul>${notes.map(line).join('')}${eng.length ? `<li>${eng.map(esc).join(', ')}: English, no translation needed</li>` : ''}</ul></li>`;
}

const tagChip = (t) => t === 'NEW' ? '<span class="chip new">NEW</span>' : t === 'KNOWN' ? '<span class="chip known">KNOWN</span>' : '<span class="chip none" title="Deliberately blank: neither a discovery nor a baseline reproduction">no provision</span>';
const verChip = (v) => !v ? '' : v === 'agree' ? '<span class="chip ok">agreed</span>' : v === 'error' ? '<span class="chip bad">error</span>' : `<span class="chip warn">${esc(v)}</span>`;
const scoreText = (r) => r._score == null ? '' : `${r._score}${r._score_inverted ? ' <span class="muted small" title="7.1 and 7.2 are inverted: 0 means the economy has a framework">(inv.)</span>' : ''}`;

/* the sort keys of the results table, one per column; blanks sort last either way */
const SORT_KEYS = {
  economy: (r) => r.Economy, law: (r) => r['Law Name'], article: (r) => r['Article / Section'],
  indicator: (r) => String(r['Indicator ID'] || '').split('.').map((x) => Number(x) || 0),
  tag: (r) => r['Discovery Tag'] || '', conf: (r) => numOrNull(r.Confidence), verified: (r) => r._verification || '',
  score: (r) => numOrNull(r._score), review: (r) => decisionText(r._decision),
  quote: (r) => r._kind === 'no_provision' ? '' : (r['Verbatim Snippet'] || ''), arm: (r) => r._arm || '',
};
const numOrNull = (v) => { const n = Number(v); return v === '' || v == null || Number.isNaN(n) ? null : n; };
const decisionText = (d) => !d ? '' : typeof d === 'string' ? d : (d.verdict || d.decision || '');
const blankKey = (v) => v == null || v === '' || (Array.isArray(v) && !v.length);
function compareKeys(a, b) {
  if (Array.isArray(a)) { for (let i = 0; i < Math.max(a.length, b.length); i++) { const d = (a[i] || 0) - (b[i] || 0); if (d) return d; } return 0; }
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b), undefined, { numeric: true, sensitivity: 'base' });
}
function sortedRows() {
  const { col, dir } = S.sort; const key = SORT_KEYS[col];
  if (!key) return S.rows;
  return S.rows.map((r, i) => [r, i]).sort((x, y) => {
    const a = key(x[0]), b = key(y[0]);
    if (blankKey(a) || blankKey(b)) return blankKey(a) && blankKey(b) ? x[1] - y[1] : blankKey(a) ? 1 : -1;   // blanks last, whichever way
    const c = compareKeys(a, b); return c ? (c > 0 ? 1 : -1) * dir : x[1] - y[1];
  }).map((p) => p[0]);
}
const th = (col, label) => `<th class="sortable ${S.sort.col === col ? 'on' : ''}" data-col="${col}" title="sort by ${esc(label)}; click again to reverse">${label} <span class="arrow">${S.sort.col === col ? (S.sort.dir > 0 ? '\u25b2' : '\u25bc') : '\u25b4'}</span></th>`;

function renderTable(j) {
  const rows = sortedRows();
  if (!rows.length) { $('#map-table').innerHTML = '<tr><td class="muted">No rows match.</td></tr>'; return; }
  const showArm = rows.some((r) => r._arm);
  $('#map-table').innerHTML = `<thead><tr>
      ${th('economy', 'Economy')}${th('law', 'Law')}${th('article', 'Article')}${th('indicator', 'Indicator')}${th('tag', 'Tag')}${th('conf', 'Conf.')}${th('verified', 'Verified')}${th('score', 'Score')}${th('review', 'Review')}${th('quote', 'Quote \u2192 English')}${showArm ? th('arm', 'Arm') : ''}
    </tr></thead><tbody>${rows.map((r) => `<tr class="r ${S.sel === r._i ? 'sel' : ''}" data-i="${r._i}">
      <td>${esc(r.Economy)}</td>
      <td>${esc(r['Law Name'])}</td>
      <td>${esc(r['Article / Section'])}</td>
      <td class="num">${esc(r['Indicator ID'])}</td>
      <td>${tagChip(r['Discovery Tag'])}</td>
      <td class="num">${esc(r.Confidence)}</td>
      <td>${verChip(r._verification)}</td>
      <td class="num">${scoreText(r)}</td>
      <td>${decisionChip(r._decision)}</td>
      <td class="snip">${r._kind === 'no_provision' ? '<span class="muted">No provision found</span>' : esc(short(r['Verbatim Snippet'], 90))}${r._gloss ? `<br><span title="machine translation, ${esc(r._gloss.model)}">→ ${esc(short(r._gloss.english, 110))}</span>` : (r['Language of Source'] !== 'English' && r._kind !== 'no_provision' ? '<br><span class="muted small">no English gloss for this row</span>' : '')}</td>
      ${showArm ? `<td class="small muted">${esc(r._arm)}</td>` : ''}
    </tr>`).join('')}</tbody>`;
  $('#map-table').querySelectorAll('tr.r').forEach((tr) => tr.addEventListener('click', () => openRow(+tr.dataset.i)));
  $('#map-table').querySelectorAll('th.sortable').forEach((h) => h.addEventListener('click', () => {
    const col = h.dataset.col;
    if (S.sort.col === col) { if (S.sort.dir > 0) S.sort.dir = -1; else S.sort = { col: '', dir: 1 }; }   // asc, desc, then back to the file order
    else S.sort = { col, dir: 1 };
    renderTable(j);
  }));
}

const short = (s, n) => { s = String(s ?? ''); return s.length > n ? s.slice(0, n - 1) + '…' : s; };

async function openRow(i) {
  S.sel = i;
  $('#map-table').querySelectorAll('tr.r').forEach((tr) => tr.classList.toggle('sel', +tr.dataset.i === i));
  let d;
  try { d = await api(`/api/map/row?${new URLSearchParams({ run: S.run, i })}`); } catch (e) { $('#map-detail').innerHTML = `<div class="note">${esc(e.message)}</div>`; return; }
  renderDetail(d);
  $('#map-detail').scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function renderDetail(d) {
  const g = d._gloss, sg = d._section_gloss, v = d._verify, sd = d._score_detail;
  const isEnglish = d['Language of Source'] === 'English';
  const noProv = d._kind === 'no_provision';
  const literalWarn = (x) => x && x.is_literal === false ? `<div class="note">The glosser marked this “not literal”: the source text is garbled (OCR) and the English is an approximation.</div>` : '';
  const url = d['Source URL'] || '';
  const isUrl = /^https?:\/\//i.test(url);
  $('#map-detail').innerHTML = `<div class="detail">
    <h3>${esc(d._econ_name)} · ${esc(d['Law Name'])} · ${esc(d['Article / Section'])} · indicator <span class="num">${esc(d['Indicator ID'])}</span></h3>
    <div>${tagChip(d['Discovery Tag'])} ${verChip(d._verification)} <span class="chip">${esc(d['Language of Source'])}</span> ${d._arm ? `<span class="chip">${esc(d._arm)}</span>` : ''} ${d._read_only ? '<span class="chip warn">frozen, read-only</span>' : ''}</div>
    ${noProv ? `<div class="note info">No provision found for this indicator. The Discovery Tag is blank on purpose: the row is neither a discovery nor a baseline reproduction. The law and link, when given, are the governing instrument cited for reference, not evidence.</div>` : `
    <div class="pair">
      <div class="col"><h4>Verbatim snippet · the evidence (${esc(d['Language of Source'])})</h4><div class="quote">${esc(d['Verbatim Snippet'])}</div></div>
      <div class="col"><h4>English · ${isEnglish ? 'the source is English' : g ? `machine translation, ${esc(g.model)}, for review only` : 'no gloss in this run'}</h4>
        ${isEnglish ? '<div class="muted small">No translation needed.</div>' : g ? `<div class="quote">${esc(g.english)}</div>${literalWarn(g)}${g.ambiguous ? '<div class="muted small">Joined by law, article and indicator; more than one gloss matched, the first is shown.</div>' : ''}` : '<div class="muted small">The glosser did not cover this row.</div>'}
      </div>
    </div>
    ${sg && !isEnglish ? `<details><summary>Provision text and its English (${esc(sg.model)})</summary><div class="pair">
        <div class="col"><h4>Provision text · original</h4><div class="quote small">${esc(short(sg.original, 3000))}</div></div>
        <div class="col"><h4>Provision text · machine English</h4><div class="quote small">${esc(short(sg.english, 3000))}</div>${literalWarn(sg)}</div></div></details>` : ''}
    ${d._raw_context ? `<details><summary>Where the quote sits in the source text</summary><div class="quote small" style="margin-top:6px">${esc(short(d._raw_context.before, 700))}<mark>${esc(d._raw_context.span || d['Verbatim Snippet'])}</mark>${esc(short(d._raw_context.after, 700))}</div></details>` : ''}`}
    <dl class="facts">
      <dt>Score for ${esc(d['Indicator ID'])}</dt><dd>${d._score == null ? '<span class="muted">not in this run’s rollup</span>' : `<b>${d._score}</b>${d._score_inverted ? ' — inverted indicator: 0 means the economy <i>has</i> a framework' : ''}${sd?.basis ? `<div class="small muted">${esc(sd.basis)}</div>` : ''}${sd?.controlling_law ? `<div class="small">Controlling law: ${esc(sd.controlling_law)}</div>` : ''}`}</dd>
      <dt>Verification</dt><dd>${noProv && !v ? '<span class="muted">none: a no-provision row has no fire to verify</span>' : v ? `${verChip(v.verifier_verdict)} final applies: <b>${v.final_applies}</b>, score hint ${esc(v.final_score_hint)}${v.verifier?.reason ? `<div class="small"><b>Verifier:</b> ${esc(v.verifier.reason)}</div>` : ''}${v.mapper?.rationale ? `<div class="small muted"><b>Mapper:</b> ${esc(v.mapper.rationale)}</div>` : ''}` : '<span class="muted">reasoning trail not in this run</span>'}</dd>
      <dt>Confidence</dt><dd>${esc(d.Confidence) || '<span class="muted">—</span>'}</dd>
      <dt>Mapping rationale</dt><dd>${esc(d['Mapping Rationale'])}</dd>
      <dt>Location</dt><dd>${esc(d['Location Reference']) || '<span class="muted">—</span>'}</dd>
      <dt>Source</dt><dd>${isUrl ? `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(url)}</a>` : esc(url)}</dd>
      <dt>Law number · amended</dt><dd>${esc(d['Law Number / Ref']) || '—'} · ${esc(d['Last Amended']) || '—'}</dd>
      <dt>Notes</dt><dd class="small">${esc(d.Notes)}</dd>
    </dl>
    ${reviewControls(d)}
    <div class="foot">${esc(d._file)}${d._pid ? ` · ${esc(d._pid)}` : ''}</div>
  </div>`;
  bindReview(d);
}

/* ---------- Other ---------- */
async function loadOther() {
  try {
    const j = await api('/api/docs');
    const byFolder = {};
    j.docs.forEach((d) => { (byFolder[d.folder] ||= []).push(d); });
    $('#docs').innerHTML = Object.entries(byFolder).map(([f, ds]) => `<h4 class="small muted">${esc(f)}</h4><ul class="docs">${ds.map((d) => `<li><a href="#" data-doc="${esc(d.path)}">${esc(d.title)}</a></li>`).join('')}</ul>`).join('') + '<pre class="doc" id="doc-view" hidden></pre>';
    $('#docs').querySelectorAll('a[data-doc]').forEach((a) => a.addEventListener('click', async (e) => {
      e.preventDefault();
      const t = await api(`/api/doc?path=${encodeURIComponent(a.dataset.doc)}`);
      const pre = $('#doc-view'); pre.hidden = false; pre.textContent = t.text; pre.scrollIntoView({ behavior: 'smooth' });
    }));
  } catch (e) { $('#docs').innerHTML = `<p class="note">${esc(e.message)}</p>`; }
  $('#selftest-btn')?.addEventListener('click', runSelftest);
  loadMachine();
  const st = S.health?.settings || [];
  $('#settings').innerHTML = `<table class="settings-table"><tr><th>Setting</th><th>Value</th><th></th></tr>${st.map((s) => `<tr><td>${esc(s.name)}</td><td class="v">${esc(s.value)}</td><td class="small muted">${s.source === 'env' ? 'from environment' : 'default'}${s.value ? (s.exists ? ' · exists' : ' · <span style="color:var(--bad)">missing</span>') : ''}</td></tr>`).join('')}</table>`;
}

/* Which Python runs each stage on this computer: kept per machine, set here, in effect at once. */
async function loadMachine() {
  const el = $('#machine');
  if (!el) return;
  let j;
  try { j = await api('/api/machine'); } catch (e) { el.innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  el.innerHTML = `<p class="small muted">Which Python runs each stage on this computer. Blank lets the tool choose: a <code>.venv</code> in the repository, else the Python running the page. Check on each stage's Run block says whether the choice has the stage's packages.</p>
    <table class="settings-table"><tr><th>Stage</th><th>Python in use</th><th>Name another</th></tr>
    ${j.stages.map((s) => `<tr><td>${esc(s.label)}</td><td class="v">${esc(s.python)}<div class="small muted">${esc(s.chosen_by)}</div></td>
      <td><input type="text" class="mc-py" data-name="${esc(s.name)}" size="56" value="${esc(s.kept)}" placeholder="full path of the python program, or blank" ${s.from_environment ? 'disabled' : ''}>
        <button class="btn small mc-save" data-name="${esc(s.name)}" ${s.from_environment ? 'disabled' : ''}>Save</button>
        <div class="small muted mc-msg">${s.from_environment ? `set by the environment variable ${esc(s.name)}, which wins` : ''}</div></td></tr>`).join('')}</table>
    <p class="small muted">Kept in <code>${esc(j.file)}</code>, for this computer only.</p>`;
  el.querySelectorAll('button.mc-save').forEach((b) => b.addEventListener('click', async () => {
    const cell = b.parentElement;
    const msg = cell.querySelector('.mc-msg');
    msg.textContent = 'Checking…';
    try {
      await api('/api/machine', { method: 'POST', body: JSON.stringify({ name: b.dataset.name, value: cell.querySelector('input.mc-py').value }) });
      EX.loaded = false; MP.loaded = false; SC.checks = null;
      await loadHealth();
      loadMachine();
    } catch (e) { msg.textContent = e.message; }
  }));
}

/* ---------- shared ---------- */
const fmtBytes = (n) => n == null ? '' : n < 1024 ? `${n} B` : n < 1048576 ? `${(n / 1024).toFixed(0)} KB` : n < 1073741824 ? `${(n / 1048576).toFixed(1)} MB` : `${(n / 1073741824).toFixed(2)} GB`;
const kv = (obj) => Object.entries(obj || {}).map(([k, v]) => `${esc(k)} ${v}`).join(', ');
const kvb = (obj) => Object.entries(obj || {}).map(([k, v]) => `${esc(String(k).replace(/_/g, ' '))} <b>${v}</b>`).join(' · ');
const stamp = () => { const d = new Date(), p = (n) => String(n).padStart(2, '0'); return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}`; };

/* ---------- Scraping ---------- */
const SC = { loaded: false, econs: [], scopes: [], chosen: new Set(), scope: '', forms: '', sources: {} };  // forms: always the stage default

async function loadScrape() {
  SC.loaded = true;
  try {
    const j = await api('/api/scrape/economies');
    SC.econs = j.economies; SC.scopes = j.scopes; SC.scope = SC.scope || j.default_scope; SC.seedNote = j.seed_note;
    if (!SC.scopes.find((x) => x.id === SC.scope)) SC.scope = j.default_scope;
  } catch (e) { $('#scrape-setup').innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  renderScrapeSetup();
  renderScrapeSources();
  loadScrapeOutputs();
  loadInbox();
}

function delayFor(codes) {
  return Math.max(3000, ...codes.map((c) => (SC.econs.find((e) => e.code === c) || {}).delay_ms || 3000));
}

function renderScrapeSetup() {
  const codes = [...SC.chosen];
  const engineCodes = codes.filter((c) => c !== 'CN');
  const scopeHelp = SC.scopes.map((s) => `<b>${esc(s.label)}</b>: ${esc(s.text)}`).join('. ') + '.';
  $('#scrape-setup').innerHTML = `
    <div class="setup-row"><div class="setup-label">Economies</div>
      <div class="econ-grid">${SC.econs.filter((e) => e.crawlable || e.tools).map((e) => `<label class="radio big ${SC.chosen.has(e.code) ? 'on' : ''}" title="${esc(e.note)}">
        <input type="checkbox" value="${e.code}" ${SC.chosen.has(e.code) ? 'checked' : ''}> <span class="name">${esc(e.name)}</span>
        <span class="sub">${e.crawlable ? (e.links ? `${e.links.all} listed, ${e.links.relevant ?? '?'} in Sample` : 'no link list') : 'CAC, gov.cn by the China tools'}</span></label>`).join('')}
      </div>
    </div>
    <div class="setup-row"><div class="setup-label">Scope</div>
      <div class="row">${SC.scopes.map((s) => `<label class="radio big ${SC.scope === s.id ? 'on' : ''}"><input type="radio" name="sc-scope" value="${s.id}" ${SC.scope === s.id ? 'checked' : ''}> ${esc(s.label)}</label>`).join('')}
      </div>
    </div>
    <details class="notes-box" ${SC.notesOpen ? 'open' : ''}><summary>Note:</summary>
      <p>* ${scopeHelp}</p>
      <p>* The file format is conditional on the portal: some publish only PDF, some only web pages, some both. The crawler takes what the portal offers, and the Extraction stage reads each kind, web page, native PDF or scanned PDF through OCR.</p>
      ${SC.econs.some((e) => e.tools) ? `<p>* <b>China</b> is not crawled by the engine: its national database forbids automated tools. With China ticked, the China tools read the publishers you tick on its card; the rest is collected by hand as <a href="#" id="sc-goto-cn">Scraping › China</a> explains. Scope does not apply to China.</p>` : ''}
    </details>
    ${SC.chosen.has('CN') ? cnCaution(true) : ''}`;
  const nb = $('#scrape-setup details.notes-box'); if (nb) nb.addEventListener('toggle', () => { SC.notesOpen = nb.open; });
  const go = $('#sc-goto-cn'); if (go) go.onclick = (e) => { e.preventDefault(); $('#tabs button[data-tab=cn]').click(); };
  $('#scrape-setup').querySelectorAll('a.goto-cn').forEach((a) => { a.onclick = (e) => { e.preventDefault(); showTab('cn'); }; });
  $('#scrape-setup').querySelectorAll('input[type=checkbox]').forEach((inp) => inp.addEventListener('change', () => {
    if (inp.checked) SC.chosen.add(inp.value); else SC.chosen.delete(inp.value);
    renderScrapeSetup(); renderScrapeSources();
  }));
  $('#scrape-setup').querySelectorAll('input[name=sc-scope]').forEach((inp) => inp.addEventListener('change', () => { SC.scope = inp.value; renderScrapeSetup(); }));
  SC.checks = null; renderScrapeRun();
  const parts = [];
  const srcOf = (c) => (SC.econs.find((e) => e.code === c) || {}).source || '';
  const crawlCmd = (list, out) => `cwd stages/p1-scrape  REQUEST_DELAY_MS=${delayFor(list)}${SC.scope === 'relevant' ? ' MAX_CANDIDATES_PER_ECONOMY=100000' : ''}  python scrape.py --economy ${list.join(',')} --pillars 6,7 --scope ${SC.scope} --forms ${SC.forms || 'pdf'} --out ${out}`;
  // one run per economy: a new crawl is filed by economy and source, a second pass goes over that economy's own folder
  if (SC.mode === 'same') engineCodes.forEach((c) => { const f = passFolder(c); parts.push(crawlCmd([c], f ? f.id : '<no crawl folder yet>')); });
  else engineCodes.forEach((c) => parts.push(crawlCmd([c], srcOf(c) ? `outputs/scrape/${c}/${srcOf(c)}/${stamp()}` : `outputs/scrape/${c}_${stamp()}`)));
  if (codes.includes('CN')) {
    const req = scrapeRequest();
    const tool = req.cn_mode === 'update'
      ? `python update.py --base CN_sources_2026-09-21${SC.dryRun ? '' : ' --fetch'}`
      : (req.cn_sources.length ? req.cn_sources.map((src) => `python collect.py ${src}${SC.dryRun ? ' --list-only' : ''}`).join('   then   ') : '(tick a publisher on the China card)');
    parts.push(`cwd stages/p1-scrape/src/p1_scrape/adapters/cn_npc  HANDOFF1_DIR=outputs/scrape/CN/china-tools/${stamp()}/data  ${tool}`);
  }
  $('#scrape-cmd').textContent = parts.join('   then   ') || 'pick at least one economy';
}

function sourcesBlock(code, d, crawl) {
  if (d.error) return `<div class="note">${esc(code)}: ${esc(d.error)}</div>`;
  const kindLabel = { principal_act: 'principal acts', subsidiary_legislation: 'subsidiary legislation', amending_act: 'amending acts', agency_or_other: 'agency or other' };
  const kindLine = d.document_kinds ? Object.entries(d.document_kinds).map(([k, v]) => `${esc(kindLabel[k] || k.replace(/_/g, ' '))} <b>${v}</b>`).join(' · ') : '';
  const china = !!d.tools_note;
  const countBullets = !china && d.counts ? `<dl class="portal-facts">
      <dt>All</dt><dd><b>${d.counts.all}</b> documents listed on the portal</dd>
      <dt>Sample</dt><dd><b>${d.counts.relevant ?? '?'}</b> documents whose titles match the pillar 6 and 7 vocabulary or are named in the registry</dd>
      ${kindLine ? `<dt>By kind</dt><dd>${kindLine}</dd>` : ''}
      ${d.catalogued_at ? `<dt>List built</dt><dd>${esc(String(d.catalogued_at).slice(0, 10))}</dd>` : ''}
    </dl>` : '';
  const crawled = d.portals.filter((p) => p.crawled);
  const portals = china ? cnSourceCards(d) : `<div class="portal-grid">${crawled.map((p, i) => `<div class="portal-card"><a class="name" href="${esc(p.root)}" target="_blank" rel="noopener">${esc(p.name)}</a><span class="sub">${esc(p.kind.replace(/_/g, ' '))}</span>${i === 0 ? countBullets : ''}<label class="pick single"><input type="checkbox" class="econ-pick" value="${esc(code)}" checked> collect it in the next run</label></div>`).join('') || '<span class="muted">no portal list in the registry</span>'}</div>`;
  const h = d.holdings;
  const factsList = (facts) => `<dl class="portal-facts">${facts.map(([k, v]) => `<dt>${esc(k)}</dt><dd>${esc(v).replace(/^(\d+)/, '<b>$1</b>')}</dd>`).join('')}</dl>`;
  const watch = d.watchlist.map((w) => `<tr><td><a href="${esc(w.url)}" target="_blank" rel="noopener">${esc(w.name)}</a></td><td class="small">${esc(w.kind)}</td><td class="small">${esc(String(w.why_not_automatic || '').replace(/\*\*/g, ''))}</td><td class="small">${esc(w.what_to_look_for)}</td><td class="small">${esc(w.indicators)}</td><td class="small">${esc(w.last_checked)}</td></tr>`).join('');
  return `<details class="src-card" open>
    <summary><span class="econ-name">${esc(d.name)}</span> <span class="chip ${crawl ? 'ok' : 'warn'}">${crawl ? (china ? 'China tools' : 'crawled') : 'checked by hand'}</span></summary>
    ${crawl ? `<div class="setup-row"><div class="setup-label">${china ? 'Sources, by layer' : 'Sources the crawler reads'}</div>
      <div>${portals}
      ${!china && d.counts ? `<details class="doclist" id="doclist-${esc(code)}" data-code="${esc(code)}" data-src="documents"><summary>Documents on the link list <span class="muted">(${d.counts.all}; All or Sample, with a filter)</span></summary><div class="doclist-body"></div></details>` : ''}
      ${china ? `<div class="callout gap"><b class="gap-title">Card colours</b><ul class="legend"><li><b>White:</b> the China tools can read the source, and they have run.</li><li><b>Yellow:</b> collected by hand; no tool may read it.</li><li><b>Grey:</b> the tools can read it and once did, but it was never taken into Extraction, so it is not in the corpus.</li></ul><span class="small">The two layers and what to check by hand: <a href="#" class="goto-cn">Scraping › China</a>.</span></div>` : ''}
      ${!d.counts && !china ? '<p class="muted small">No link list for this economy.</p>' : ''}
      </div></div>
    ${h ? `<details class="hand hold" data-hold="${esc(code)}" ${SC.holdOpen && SC.holdOpen.has(code) ? 'open' : ''}><summary class="setup-label">${esc(h.label)} <span class="muted">${esc(h.sub || '')}</span> <span class="hint">${h.rows} documents</span></summary>
      ${factsList(h.facts)}
      <details class="doclist" id="holdings-${esc(code)}" data-code="${esc(code)}" data-src="holdings"><summary>Documents ${esc(h.doclist_label || 'held')} <span class="muted">(${h.rows}; ${esc(h.scope_hint || 'with a filter')})</span></summary><div class="doclist-body"></div></details>
      </details>` : `<details class="hand hold"><summary class="setup-label">What we hold today <span class="muted">(9.30 Finale Submission)</span> <span class="hint">nothing in this clone</span></summary><p class="muted">No shipped corpus for this economy in this clone.</p></details>`}` : ''}
    <details class="hand"><summary class="setup-label">Sources to check by hand <span class="muted">(${d.watchlist.length})</span> <span class="hint">recommended, not yet incorporated</span></summary>
      <p class="src-counts">${esc(d.manual_note)}</p>
      ${d.watchlist.length ? `<div class="table-wrap short"><table class="rows"><thead><tr><th>Source</th><th>Kind</th><th>Why not automatic</th><th>What to look for</th><th>Indicators</th><th>Last checked</th></tr></thead><tbody>${watch}</tbody></table></div>` : '<p class="muted small">No watchlist shipped for this economy.</p>'}
    </details>
    <div class="foot">${esc([d.sources_file, d.links_file, h && h.id, d.watchlist_file].filter(Boolean).join('  ·  '))}</div>
  </details>`;
}

async function renderScrapeSources() {
  const codes = [...SC.chosen];
  const parts = [];
  for (const code of codes) {
    if (!SC.sources[code]) {
      try { SC.sources[code] = await api(`/api/scrape/sources?economy=${code}`); } catch (e) { SC.sources[code] = { error: e.message }; }
    }
    parts.push(sourcesBlock(code, SC.sources[code], true));
  }
  $('#scrape-sources').innerHTML = parts.join('');
  bindDocLists();
  // a fold stays as the reader left it when the cards are drawn again
  document.querySelectorAll('#scrape-sources details.hold[data-hold]').forEach((d) => d.addEventListener('toggle', () => {
    SC.holdOpen = SC.holdOpen || new Set();
    if (d.open) SC.holdOpen.add(d.dataset.hold); else SC.holdOpen.delete(d.dataset.hold);
  }));
  document.querySelectorAll('#scrape-sources a.goto-cn').forEach((a) => { a.onclick = (e) => { e.preventDefault(); showTab('cn'); }; });
  document.querySelectorAll('#scrape-sources input.cn-src').forEach((inp) => inp.addEventListener('change', () => {
    if (inp.checked) SC.cnSources.add(inp.value); else SC.cnSources.delete(inp.value);
    SC.checks = null;
    renderScrapeSetup();
  }));
  document.querySelectorAll('#scrape-sources input.econ-pick').forEach((inp) => inp.addEventListener('change', () => {
    if (!inp.checked) { SC.chosen.delete(inp.value); renderScrapeSetup(); renderScrapeSources(); }
  }));
}

async function loadScrapeOutputs() {
  let j;
  try { j = await api('/api/scrape/outputs'); } catch (e) { $('#scrape-output').innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  SC.folders = j.folders; renderScrapeRun();
  const present = (f) => !f.raw_checked ? '' : f.raw_present === f.raw_checked ? '<span class="chip ok">yes</span>' : f.raw_present ? `<span class="chip warn">${f.raw_present} of ${f.raw_checked} checked</span>` : '<span class="chip">manifest only</span>';
  const tools = (f) => f.cn_sources && Object.keys(f.cn_sources).length ? kv(f.cn_sources) : '';
  // filed by economy and source: the two columns say where a folder sits; an older folder shows its economies and no source
  const econ = (f) => f.economy ? `<b>${esc(f.economy)}</b>` : kv(f.by_economy);
  const source = (f) => f.source ? `<span title="${esc(f.source)}">${esc(f.source_name || f.source)}</span>${tools(f) ? ` <span class="muted">(${tools(f)})</span>` : ''}` : tools(f);
  const last = (f) => f.kind === 'hand-collected' ? `<span class="small muted">${f.batches && f.batches.length ? `${f.batches.length} batch${f.batches.length === 1 ? '' : 'es'}` : 'by hand'}</span>`
    : f.kind === 'hand-collected manifest' ? '<span class="small muted">by hand</span>'
    : f.kind === 'link list' ? '<span class="small muted">in use from here on</span>'
    : `${f.fetched_last_pass ?? ''}`;
  // how the run stands: the crawler's own record, and this session's runs for "running" and "stopped"
  const STATE = { running: ['chip warn', 'running', 'a run is writing into this folder now'], complete: ['chip ok', 'complete', 'the crawler finished'],
    paused: ['chip warn', 'paused', 'paused by the portal: it stopped answering. Update an existing crawl fetches the rest later'],
    stopped: ['chip', 'stopped', 'Stop was pressed; Update an existing crawl fetches the rest'],
    'not complete': ['chip bad', 'not complete', 'the run ended before the crawler finished: stopped, or failed. Update an existing crawl fetches the rest'] };
  const state = (f) => { const x = STATE[f.run_state]; if (!x) return '<span class="muted">–</span>';
    const c = f.crawl_state; const n = c && c.todo ? `${c.attempted} of ${c.todo} attempted, ${c.stored_total} stored. ` : '';
    return `<span class="${x[0]}" title="${esc(n + x[2])}">${x[1]}</span>`; };
  const when = (x) => x ? x.split(' ').map((y) => `<span>${esc(y)}</span>`).join(' ') : '<span class="muted">–</span>';   // the date over the time
  const buttons = (f) => `<button class="btn small" data-open="${esc(f.path)}">Open folder</button>`
    + (f.kind === 'interface run' ? ` <button class="btn small" data-clear="${esc(f.path)}/raw" data-what="the downloaded documents (raw/)">Clear raw</button>` : '')
    + (f.kind === 'interface run' || f.kind === 'China tools run' ? ` <button class="btn small" data-clear="${esc(f.path)}" data-what="the whole run folder">Clear folder</button>` : '')
    + (f.kind === 'hand-collected manifest' ? ` <button class="btn small" data-clear="${esc(f.path)}" data-what="the manifest written for these hand-collected files; the files stay in the inbox">Clear folder</button>` : '')
    + (f.kind === 'link list' ? ` <button class="btn small" data-clear="${esc(f.path)}" data-what="this refreshed link list; the list before it, or the shipped one, is used again">Clear folder</button>` : '');
  $('#scrape-output').innerHTML = j.folders.length ? `<div class="table-wrap short"><table class="rows"><thead><tr><th>Began</th><th>Last run</th><th>Economy</th><th>Source</th><th>Folder</th><th>Kind</th><th>Status</th><th>Documents</th><th>By type</th><th>Bytes<br>present</th><th>Fetched<br>last pass</th><th></th></tr></thead><tbody>
    ${j.folders.map((f) => `<tr><td class="small began">${when(f.began)}</td><td class="small began">${when(f.last_run)}</td><td class="small">${econ(f)}</td><td class="small">${source(f)}</td><td class="small folder" title="${esc(f.path)}">${esc(f.id)}${carried(f)}</td><td class="small">${esc(f.kind)}</td><td class="small state">${state(f)}</td><td class="num">${f.rows}</td><td class="small">${kv(f.by_source_type)}</td><td class="small">${present(f)}</td><td class="num">${last(f)}</td><td class="small">${buttons(f)}</td></tr>`).join('')}
    </tbody></table></div><p class="muted small"><b>Began</b> is when Start was pressed, read from the folder's name. <b>Last run</b> is when the crawler last started in that folder; a second pass moves it. <b>Status</b> is the crawler's own record: complete, running, paused (by the portal), stopped, or not complete (the run ended early); a dash where there is no record. Results are filed by economy, then source: <code>scrape/&lt;economy&gt;/&lt;source&gt;/&lt;time&gt;</code> for a crawl, <code>inbox/&lt;economy&gt;/&lt;source&gt;</code> for files fetched by hand. A shipped manifest describes every document without containing one; the bytes come back by running the crawler. The fetched count is the crawler's own figure from cost_report.json and must read 0 on a second pass over the same folder. A China tools run counts the documents its raw folders hold. A hand-collected row goes to Extraction like a crawl folder. A link list is what Refresh from the portal wrote: the documents the portal lists, not yet fetched.</p>`
    : '<p class="muted">No crawl folders yet.</p>';
  bindClear('#scrape-output', loadScrapeOutputs);
  bindOpen('#scrape-output');
}

/* ---------- Extraction ---------- */
const EX = { loaded: false, inputs: [], languages: [], defaultLang: {}, chosen: null, typed: '', desc: null, language: '', pack: 'fast', workers: 16, checks: null, checking: false, notesOpen: false, runNotesOpen: false, htmlHosts: [] };

async function loadExtract() {
  EX.loaded = true;
  try {
    const j = await api('/api/extract/inputs');
    EX.inputs = j.inputs; EX.languages = j.languages; EX.defaultLang = j.default_language; EX.economies = j.economies; EX.htmlHosts = j.html_hosts || []; EX.stagePresent = j.stage_present; EX.python = j.python;
    if (!EX.chosen && EX.inputs.length) EX.chosen = EX.inputs[0].id;
  } catch (e) { $('#extract-setup').innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  EX.desc = EX.inputs.find((i) => i.id === EX.chosen) || null;
  renderExtractSetup();
  renderExtractDescribe();
  loadExtractOutputs();
}

function inputLabel(i) {
  const n = `${i.rows} file${i.rows === 1 ? '' : 's'}`;
  if (i.origin === 'hand-collected source') return `${i.id}: ${n} by hand from ${i.source_name || i.source} (every batch)`;
  if (i.origin === 'hand-collected batch') return `${i.id}: ${n} by hand from ${i.source_name || i.source} (one batch)`;
  if (i.origin === 'inbox batch') return `${i.id}: ${n} (one batch of ${i.economy}, filed under no source)`;
  if (i.origin === 'inbox') return `${i.id}: ${n} (every source of ${i.economy})`;
  const what = i.kind === 'crawled' ? `${i.rows} documents` : `${i.rows} files, no manifest`;
  const bytes = i.kind !== 'crawled' ? '' : i.raw_checked === 0 ? '' : i.raw_present === 0 ? ', bytes not shipped' : i.raw_present < i.raw_checked ? `, ${i.raw_present} of ${i.raw_checked} present` : '';
  return `${i.id}: ${what}${bytes} (${i.origin})`;
}

/* a shipped manifest describes documents without holding them: listed last, under its own heading */
const listOnly = (i) => i.kind === 'crawled' && i.raw_checked > 0 && i.raw_present === 0;
const inputOption = (i) => `<option value="${esc(i.id)}" ${EX.chosen === i.id ? 'selected' : ''}>${esc(inputLabel(i))}</option>`;

function renderExtractSetup() {
  const d = EX.desc;
  const inboxSetting = ((S.health && S.health.settings) || []).find((x) => x.name === 'RDTII_INBOX_DIR');
  const inbox = inboxSetting ? inboxSetting.value : 'inbox';
  $('#extract-setup').innerHTML = `
    <div class="setup-row"><div class="setup-label">Input</div>
      <div class="row"><select id="ex-input" class="wide-select">${EX.inputs.filter((i) => !listOnly(i)).map(inputOption).join('')}<option value="__typed" ${EX.chosen === '__typed' ? 'selected' : ''}>another folder on this machine</option>${EX.inputs.some(listOnly) ? `<optgroup label="Lists only: the documents are not on this machine">${EX.inputs.filter(listOnly).map(inputOption).join('')}</optgroup>` : ''}</select>
        ${EX.chosen === '__typed' ? `<input type="text" id="ex-typed" size="48" placeholder="a folder holding PDF, HTML or Word files" value="${esc(EX.typed)}"> <button class="btn" id="ex-describe">Look</button>` : ''}
      </div>
    </div>
    <details class="notes-box" ${EX.notesOpen ? 'open' : ''}><summary>Note:</summary>
      <p>* <b>Input</b> is a crawl folder from Scraping, with its manifest, or a folder of documents collected by hand.</p>
      <p>* <b>Hand-collected files</b> go in the inbox, one folder per economy: <code>${esc(inbox)}/CN/Hand_collected</code>, <code>${esc(inbox)}/SG/Hand_collected</code>, a dated subfolder per drop. Drop them at 1 Scraping → Hand-collected. The folder names the economy, and the language follows. The interface writes the manifest and the law table under the runs root and leaves the files as they are.</p>
      <p>* <b>Readiness</b> says, per file, how it is read or why it cannot be. Files that cannot be read are left out of the run and listed in <code>left_out.csv</code> beside the manifest.</p>
      <p>* <b>Language</b> is not chosen. The crawler records each document’s language; a document without one takes its economy’s language from the stage’s table (English, Chinese, Lao, Portuguese, Malay). Check reads the text of hand-collected files it can read and warns when a file does not fit its folder.</p>
      <p>* Each document is read by the lane its kind needs: A web page, B native PDF, C scanned PDF through OCR, D Word.${EX.htmlHosts && EX.htmlHosts.length ? ` Web pages parse for ${EX.htmlHosts.length} registered hosts only.` : ''}</p>
    </details>`;
  const nb = $('#extract-setup details.notes-box'); if (nb) nb.addEventListener('toggle', () => { EX.notesOpen = nb.open; });
  $('#ex-input').onchange = (e) => { EX.chosen = e.target.value; EX.checks = null; EX.outName = ''; EX.economy = ''; EX.desc = EX.inputs.find((i) => i.id === EX.chosen) || null; renderExtractSetup(); renderExtractDescribe(); };
  const look = $('#ex-describe');
  if (look) look.addEventListener('click', async () => {
    EX.typed = $('#ex-typed').value.trim();
    try { EX.desc = await api(`/api/extract/describe?path=${encodeURIComponent(EX.typed)}`); }
    catch (e) { EX.desc = { error: e.message }; }
    EX.checks = null; EX.outName = ''; EX.economy = '';
    renderExtractSetup(); renderExtractDescribe();
  });
  renderExtractCmd();
}

function renderExtractCmd() {
  const d = EX.desc;
  const el = $('#extract-cmd');
  if (!el) return;
  if (!d || d.error) { el.textContent = ''; return; }
  const out = `outputs/extract/${EX.outName || d.out_name || d.name}`;
  const types = d.by_source_type || {};
  const scanned = types.pdf_scanned || (d.kind === 'hand_collected' ? types.pdf : 0);
  const dl = EX.defaultLang || {};
  const plan = d.kind !== 'hand_collected' ? (d.language_plan || [])
    : d.per_subfolder ? Object.keys(d.by_economy || {}).sort().map((c) => [c, dl[c] || 'eng'])
    : [[d.economy || EX.economy || '', dl[d.economy || EX.economy] || 'eng']];
  const langs = [...new Set(plan.map((p) => p[1]))];
  const passes = langs.length <= 1 ? [['', langs[0] || 'eng']] : plan;
  const rootSetting2 = ((S.health && S.health.settings) || []).find((x) => x.name === 'RDTII_RUNS_ROOT');
  const pathSep = rootSetting2 && rootSetting2.value.includes('/') ? ':' : ';';
  const one = (econ, lang) => {
    const sel = `${econ ? `--economy ${econ} ` : ''}--default-language ${lang}`;
    const ocr = scanned ? `python -m rdtii_p2.cli ocr --manifest <in>/manifest.csv --raw <in> --out ${out} ${sel} --workers ${EX.workers} --pack ${EX.pack}   then   ` : '';
    return `${ocr}python -m rdtii_p2.cli run --manifest <in>/manifest.csv --raw <in> --out ${out} ${sel} --skip-tags`;
  };
  el.textContent = `cwd stages/p2-extract  PYTHONPATH=src${pathSep}.  ` + passes.map(([e, l]) => one(e, l)).join('   then   ');
}

function renderExtractDescribe() {
  const d = EX.desc;
  const det = d && d.detected;
  if (d && !d.error && d.kind === 'hand_collected') {
    if (d.economy) EX.economy = d.economy;
    else if (d.per_subfolder) EX.economy = '';
    else if (!EX.economy && det && det.suggested_economy) EX.economy = det.suggested_economy;
  }
  renderExtractRun();
  const host = $('#extract-describe');
  if (!d) { host.innerHTML = ''; return; }
  if (d.error) { host.innerHTML = `<div class="note">${esc(d.error)}</div>`; return; }
  let present = '';
  if (d.kind === 'crawled' && d.raw_checked) {
    present = d.raw_present === d.raw_checked ? '<span class="chip ok">documents present</span>'
      : d.raw_present ? `<span class="chip warn">${d.raw_present} of ${d.raw_checked} documents present</span>`
      : '<span class="chip warn">manifest only, documents not in the folder</span>';
  } else if (d.kind !== 'crawled') {
    present = `<span class="chip ok">${d.rows} files, ${fmtBytes(d.size_bytes)}</span>`;
    if (det && det.mismatch) present += ` <span class="chip warn">${det.mismatch} file(s) do not fit the folder</span>`;
  }
  let facts;
  if (d.kind === 'crawled') {
    facts = `<dt>Path</dt><dd><code>${esc(d.path)}</code></dd>${d.note ? `<dt>Run note</dt><dd>${carried(d)}</dd>` : ''}
       <dt>Documents</dt><dd><b>${d.rows}</b></dd>
       <dt>By economy</dt><dd>${kvb(d.by_economy) || 'none'}</dd>
       <dt>By type</dt><dd>${kvb(d.by_source_type) || 'none'}</dd>
       <dt>Languages</dt><dd>${esc(d.language_line || '')}</dd>`;
  } else {
    const econLine = d.per_subfolder
      ? `from the folder names: ${Object.entries(d.by_economy || {}).map(([c, n]) => `<b>${esc(econName(c))}</b> ${n}`).join(' · ')}`
      : d.economy ? `<b>${esc(econName(d.economy))}</b> (${esc(d.economy)}), from the folder name`
      : det && det.suggested_economy ? `not named by the folder; the text points to <b>${esc(econName(det.suggested_economy))}</b>, confirm it in Run`
      : 'not named by the folder; choose it in Run';
    const langLine = d.per_subfolder
      ? Object.keys(d.by_economy || {}).map((c) => `${esc(c)} ${esc(langName((EX.defaultLang || {})[c] || 'eng'))}`).join(' · ')
      : (d.economy || EX.economy) ? `${esc(langName((EX.defaultLang || {})[d.economy || EX.economy] || 'eng'))}, from the economy table` : 'follows the economy';
    facts = `<dt>Path</dt><dd><code>${esc(d.path)}</code></dd>${d.note ? `<dt>Run note</dt><dd>${carried(d)}</dd>` : ''}
       <dt>Files</dt><dd>${kvb(d.by_source_type)}</dd>
       <dt>Economy</dt><dd>${econLine}</dd>
       ${d.source ? `<dt>Source</dt><dd>${d.source_url ? `<a href="${esc(d.source_url)}" target="_blank" rel="noopener">${esc(d.source_name || d.source)}</a>` : esc(d.source_name || d.source)} <span class="muted">(${esc(d.source)})</span></dd>` : ''}
       ${d.batch ? `<dt>Batch</dt><dd>${esc(d.batch)}</dd>` : ''}
       <dt>Language</dt><dd>${langLine}</dd>
       ${det ? `<dt>Text check</dt><dd>${esc(det.line)}${det.mismatch ? `<br><span class="hint">Does not fit the folder: ${esc(det.mismatch_files.join(', '))}</span>` : ''}</dd>` : ''}`;
  }
  const perFile = det && det.files && det.files.length ? `<details class="doclist"><summary>Detection per file <span class="muted">(${det.files.length})</span></summary><div class="table-wrap short"><table class="rows"><thead><tr><th>File</th><th>Language</th><th>Economy</th><th>Basis</th></tr></thead><tbody>
      ${det.files.map((f) => `<tr><td class="small">${esc(f.file)}</td><td>${f.language ? esc(langName(f.language)) : '<span class="muted">not read</span>'}</td><td>${f.economy ? esc(econName(f.economy)) : ''}</td><td class="small muted">${esc(f.basis)}</td></tr>`).join('')}</tbody></table></div></details>` : '';
  host.innerHTML = `<details class="src-card" open>
    <summary><span class="econ-name">${esc(d.name)}</span> <span class="chip">${d.kind === 'crawled' ? 'crawl folder with manifest' : 'hand-collected documents'}</span> ${present}</summary>
    <dl class="portal-facts">${facts}</dl>
    ${perFile}
    <div id="ex-manifest-preview"></div>
  </details>`;
  // hand-collected files: say at once how each will be read (a very large folder waits for the button)
  if (d.kind === 'hand_collected' && d.rows && d.rows <= 500 && (d.per_subfolder || d.economy || EX.economy)) previewManifest(true);
}

async function loadExtractOutputs() {
  let j;
  try { j = await api('/api/extract/outputs'); } catch (e) { $('#extract-output').innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  $('#extract-output').innerHTML = j.folders.length ? `<div class="table-wrap short"><table class="rows"><thead><tr><th>Folder</th><th>Kind</th><th>Documents</th><th>By status</th><th>By lane</th><th>Provisions</th><th>Laws</th><th>OCR cache</th><th>Frozen text</th><th></th></tr></thead><tbody>
    ${j.folders.map((f) => `<tr><td title="${esc(f.path)}">${esc(f.id)}${carried(f)}</td><td class="small">${esc(f.kind)}</td><td class="num">${f.documents}</td><td class="small">${kv(f.by_status)}</td><td class="small">${kv(f.by_lane)}</td><td class="num">${f.provisions}</td><td class="num">${f.laws}</td><td class="num">${fmtBytes(f.cache_bytes.ocr)}</td><td class="num">${fmtBytes(f.cache_bytes.source_text)}</td><td class="small">${f.to_check ? `<button class="btn small tocheck" data-unread="${esc(f.path)}">${f.to_check} to check</button> ` : ''}<button class="btn small" data-open="${esc(f.path)}">Open folder</button> ${f.kind === 'interface run' ? `<button class="btn small" data-clear-ocr="${esc(f.path)}">Clear OCR cache</button> <button class="btn small" data-clear="${esc(f.path)}" data-what="the whole extraction folder">Clear folder</button>` : ''}</td></tr>`).join('')}
    </tbody></table></div><p class="muted small">Lanes: A web page, B native PDF, C scanned PDF read by OCR, D Word. The OCR cache and the frozen text are what a re-run reuses; clearing both forces a fresh OCR.</p>`
    : '<p class="muted">No extraction output yet. HANDOFF2_DIR points at a folder that appears after the first run.</p>';
  bindClear('#extract-output', loadExtractOutputs);
  bindOpen('#extract-output');
  $('#extract-output').insertAdjacentHTML('beforeend', '<div id="ex-unread"></div>');
  document.querySelectorAll('#extract-output [data-unread]').forEach((b) => b.addEventListener('click', () => showUnread(b.dataset.unread)));
  if (EX.unread) showUnread(EX.unread);      // the list stays open across a refresh of the table
}

/* the documents of one output that gave no provision, for a person to check */
async function showUnread(path) {
  const box = $('#ex-unread');
  if (!box) return;
  let j;
  try { j = await api('/api/extract/unread?folder=' + encodeURIComponent(path)); } catch (e) { EX.unread = null; box.innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  EX.unread = path;
  const link = (d) => /^https?:/.test(d.source_url) ? `<a href="${esc(d.source_url)}" target="_blank" rel="noopener">source</a>` : '';
  box.innerHTML = `<div class="src-card unread">
    <div class="unread-head"><b>${j.documents.length} of ${j.total} documents to check</b> <code>${esc(j.id)}</code>
      ${j.text_folder ? `<button class="btn small" data-open="${esc(j.text_folder)}">Open the text folder</button>` : ''} <button class="btn small" id="ex-unread-close">Close</button></div>
    <p class="small muted">These gave no provisions, so Mapping does not see them. Open one to see whether it holds a rule; the text file is what the tool read.</p>
    <div class="table-wrap"><table class="rows"><thead><tr><th>Document</th><th>What happened</th><th>The stage’s note</th><th>Where</th></tr></thead><tbody>
    ${j.documents.map((d) => `<tr><td><b>${esc(d.title)}</b>${d.title_original ? `<div class="small">${esc(d.title_original)}</div>` : ''}<div class="small muted">${esc(d.doc_id)}${d.lane ? ` · lane ${esc(d.lane)}` : ''}</div></td>
      <td>${esc(d.what)}</td><td class="small">${esc(d.reason)}</td>
      <td class="small">${d.text_file ? `<code>${esc(d.text_file)}</code><div class="muted">${d.text_chars.toLocaleString()} bytes</div>` : '<span class="muted">no text kept</span>'} ${link(d)}</td></tr>`).join('')}
    </tbody></table></div></div>`;
  bindOpen('#ex-unread');
  $('#ex-unread-close').onclick = () => { EX.unread = null; box.innerHTML = ''; };
  box.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
}

function bindClear(rootSel, reload) {
  document.querySelectorAll(`${rootSel} [data-clear]`).forEach((b) => b.addEventListener('click', async () => { if (await clearPath(b.dataset.clear, b.dataset.what)) reload(); }));
  document.querySelectorAll(`${rootSel} [data-clear-ocr]`).forEach((b) => b.addEventListener('click', async () => {
    const base = b.dataset.clearOcr;
    const a = await clearPath(`${base}/ocr`, 'the OCR page cache (ocr/)');
    const c = await clearPath(`${base}/source_text`, 'the frozen text (source_text/), so scanned documents go through OCR again');
    if (a || c) reload();
  }));
}

function econName(code) {
  const hit = (EX.economies || []).find((e) => e.code === code);
  return hit ? hit.name : code;
}

function langName(code) {
  const hit = (EX.languages || []).find((l) => l.id === code);
  return hit ? hit.label : code;
}

const IB = { data: null, economy: '', source: '', files: [], log: [], busy: false, notesOpen: false, filesOpen: null };
const IB_SHOWN = 300;   // rows drawn in the file list; every file still goes to Extraction

function ibEconomy() { return IB.data ? IB.data.economies.find((e) => e.code === IB.economy) : null; }
function ibSource() { const e = ibEconomy(); return e ? e.hand : null; }   // one folder per economy: its Hand_collected

async function loadInbox() {
  const host = $('#inbox-body');
  if (!host) return;
  const block = $('#inbox-block');
  if (block && !block.dataset.bound) {
    block.dataset.bound = '1';
    block.open = false;   // always starts folded
  }
  try { IB.data = await api('/api/inbox'); } catch (e) { host.innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  if (!IB.economy && SC.chosen && SC.chosen.size === 1) IB.economy = [...SC.chosen][0];
  if (IB.economy && !ibEconomy()) IB.economy = '';
  await loadInboxFiles();
  renderInbox();
}

async function loadInboxFiles() {
  if (!IB.economy) { IB.files = []; return; }
  try { IB.files = (await api(`/api/inbox/files?${new URLSearchParams({ economy: IB.economy })}`)).files; } catch (e) { IB.files = []; }
}

function renderInbox() {
  const d = IB.data;
  const host = $('#inbox-body');
  if (!host || !d) return;
  const cur = ibEconomy();
  const src = ibSource();
  const target = src ? `${d.root}/${cur.code}/${src.key}` : '';
  const n = (k) => `${k} file${k === 1 ? '' : 's'}`;
  const batchLine = !src || !src.files ? '' : src.batches.length
    ? `${src.batches.length} batch${src.batches.length === 1 ? '' : 'es'}: ${src.batches.map((b) => `${b.name} (${b.files})`).join(', ')}${src.loose ? `; ${n(src.loose)} outside a batch` : ''}`
    : 'no batches: the files were copied in by hand';
  const cannot = IB.files.filter((f) => f.status === 'cannot_read');
  const listed = [...cannot, ...IB.files.filter((f) => f.status !== 'cannot_read')].slice(0, IB_SHOWN);
  const filesOpen = IB.filesOpen == null ? (cannot.length > 0 || IB.files.length <= 30) : IB.filesOpen;
  const fileRow = (f) => {
    const parts = f.name.split('/');
    const name = parts[parts.length - 1];
    const direct = parts.length === (f.batch ? 2 : 1);   // an address is kept for a file that sits in the folder or one of its batches
    const reads = f.status === 'cannot_read'
      ? `<span class="chip bad">cannot be read</span><div class="small">${esc(f.action || '')}</div>`
      : `<span class="chip ok">ready</span> <span class="small">${esc(f.method || '')}</span>${f.action ? `<div class="small muted">${esc(f.action)}</div>` : ''}`;
    const basis = f.url ? (f.url_basis || 'noted beside the file') : 'none noted';
    return `<tr><td>${esc(name)}</td><td>${reads}</td>
      <td class="addr">${direct ? `<input type="url" class="ib-url" data-file="${esc(name)}" data-batch="${esc(f.batch || '')}" value="${esc(f.url || '')}" placeholder="https://… the document’s own address">` : esc(f.url || '')}<div class="small muted">${esc(basis)}</div></td>
      <td class="small">${esc(f.batch || '')}</td><td class="num">${fmtBytes(f.size)}</td></tr>`;
  };
  host.innerHTML = `
    <div class="callout cn-caution"><b>Why this block.</b>
      <ul>
        <li>Some sources cannot be crawled: a robots.txt ban, a host that refuses an automated client, a portal with no machine-readable list.</li>
        <li>Fetch those files by hand and drop them here. They go in the economy’s <code>Hand_collected</code> folder, one dated subfolder per drop.</li>
        <li>They sit beside the crawler’s results in Output and pass down to Extraction and Mapping through the same pipeline.</li>
      </ul></div>
    <div class="callout cn-caution"><b>Before you drop.</b>
      <ul>
        <li><mark><b>Use PDF or Word.</b></mark> A saved web page is read only from ${(d.html_hosts || []).length ? esc(d.html_hosts.join(', ')) : 'a few portals'}. From any other site, print the page to PDF first.</li>
        <li><b>Unusual layouts.</b> Extraction splits a law at the headings common in that economy’s laws. A file laid out differently may not split well; check it in Extraction’s Output.</li>
      </ul></div>
    <div class="setup-row"><div class="setup-label">Economy</div>
      <div class="econ-grid">${d.economies.map((e) => `<label class="radio big ${IB.economy === e.code ? 'on' : ''}"><input type="radio" name="ib-econ" value="${e.code}" ${IB.economy === e.code ? 'checked' : ''}> <span class="name">${esc(e.name)}</span><span class="sub">${e.files ? n(e.files) : 'empty'}</span></label>`).join('')}</div>
    </div>
    <div class="setup-row"><div class="setup-label">Files</div>
      <div>
        <label class="dropzone ${src ? '' : 'off'}" id="ib-drop"><input type="file" id="ib-files" multiple accept=".pdf,.html,.htm,.docx,.doc,.zip" ${src ? '' : 'disabled'}>
          ${src ? `Drop PDF or Word files here, or a .zip of them, or click to choose. Each drop is one batch, saved under <code>${esc(target)}/&lt;date_time&gt;</code>.` : 'Choose the economy first.'}</label>
        ${IB.log.length ? `<ul class="ib-log">${IB.log.map((x) => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
      </div>
    </div>
    ${src ? `<div class="setup-row"><div class="setup-label">In the folder</div>
      <div><div class="row"><span><b>${src.files}</b> file${src.files === 1 ? '' : 's'} in <code>${esc(target)}</code></span> <button class="btn small" data-open="${esc(src.path)}">Open folder</button> ${src.files ? '<a href="#" id="ib-goto">Extract them: 2 Extraction → Input</a>' : ''}</div>
        ${batchLine ? `<p class="small muted" style="margin:6px 0 0">${esc(batchLine)}</p>` : ''}
        ${cur.elsewhere ? `<p class="small muted" style="margin:6px 0 0">${n(cur.elsewhere)} filed before this folder existed sit elsewhere under <code>${esc(d.root)}/${esc(cur.code)}</code>. They still go to Extraction.</p>` : ''}
        ${cannot.length ? `<p class="ib-warn"><span class="chip bad">${cannot.length} cannot be read</span> Each says what to do. Extraction runs on the rest and leaves these out.</p>` : ''}
        ${IB.files.length ? `<details class="doclist" id="ib-list" ${filesOpen ? 'open' : ''}><summary>Files <span class="muted">(${IB.files.length}${IB.files.length > IB_SHOWN ? `, the first ${IB_SHOWN} shown` : ''})</span></summary><div class="table-wrap short"><table class="rows ib-files"><thead><tr><th>File</th><th>Reads as</th><th>Address it came from</th><th>Batch</th><th>Size</th></tr></thead><tbody>
          ${listed.map(fileRow).join('')}</tbody></table></div></details>` : ''}
      </div></div>` : ''}
    <details class="notes-box" ${IB.notesOpen ? 'open' : ''}><summary>Note:</summary>
      <p>* One economy at a time. The folder names it, and the language follows from the economy table. Each drop is a batch, a dated subfolder of <code>Hand_collected</code>; 2 Extraction → Input lists the folder (every batch) and each batch on its own.</p>
      <p>* No source is asked for: how a file is read follows from what it is and from the economy’s language. The one exception is a saved web page, read by the parser of the portal it came from, so it needs its address.</p>
      <p>* PDF (native or scanned), Word .docx, and web pages saved from a portal the reader knows. A .zip is unpacked on arrival. A file already in the batch is kept once; a different file with the same name is saved under a numbered name.</p>
      <p>* <b>Reads as</b> is judged from what the file is, not from its name. An old .doc and a page from another site cannot be read; the line says what to do (Save As .docx, or print the page to PDF).</p>
      <p>* <b>Address</b>: a saved web page brings its own; for anything else, paste the document’s address, so the output can cite it. Addresses are kept in <code>provenance.tsv</code> beside the files.</p>
    </details>`;
  const nb = host.querySelector('details.notes-box'); if (nb) nb.addEventListener('toggle', () => { IB.notesOpen = nb.open; });
  const fl = $('#ib-list'); if (fl) fl.addEventListener('toggle', () => { IB.filesOpen = fl.open; });
  host.querySelectorAll('input[name=ib-econ]').forEach((inp) => inp.addEventListener('change', async () => { IB.economy = inp.value; IB.files = []; IB.log = []; IB.filesOpen = null; await loadInboxFiles(); renderInbox(); }));
  host.querySelectorAll('input.ib-url').forEach((inp) => inp.addEventListener('change', () => saveAddress(inp)));
  const drop = $('#ib-drop');
  const input = $('#ib-files');
  if (drop && src) {
    drop.addEventListener('dragover', (e) => { e.preventDefault(); drop.classList.add('over'); });
    drop.addEventListener('dragleave', () => drop.classList.remove('over'));
    drop.addEventListener('drop', (e) => { e.preventDefault(); drop.classList.remove('over'); if (e.dataTransfer && e.dataTransfer.files.length) uploadFiles(e.dataTransfer.files); });
    input.addEventListener('change', () => { if (input.files.length) uploadFiles(input.files); });
  }
  const go = $('#ib-goto');
  if (go) go.onclick = (e) => { e.preventDefault(); if (typeof EX !== 'undefined') { EX.chosen = src.id; EX.desc = null; EX.checks = null; EX.economy = ''; EX.loaded = false; } showTab('extract'); };
  bindOpen('#inbox-body');
}

async function saveAddress(inp) {
  const note = inp.parentElement.querySelector('.small');
  try {
    await api('/api/inbox/address', { method: 'POST', body: JSON.stringify({ economy: IB.economy, batch: inp.dataset.batch, file: inp.dataset.file, url: inp.value.trim() }) });
    await loadInboxFiles();   // the address can change how a web page is read
    renderInbox();
    if (typeof EX !== 'undefined') EX.loaded = false;
  } catch (e) { inp.classList.add('bad'); if (note) note.textContent = e.message; }
}

async function uploadFiles(fileList) {
  if (!IB.economy || !ibSource() || IB.busy) return;
  const files = [...fileList];
  const batch = batchStamp();
  IB.busy = true;
  IB.filesOpen = null;
  IB.log = [`Adding ${files.length} file${files.length === 1 ? '' : 's'} to ${IB.data.root}/${IB.economy}/${ibSource().key}/${batch}…`];
  renderInbox();
  const results = [];
  let done = 0;
  for (const f of files) {
    try {
      const r = await fetch(`/api/inbox/upload?${new URLSearchParams({ economy: IB.economy, name: f.name, batch })}`,
        { method: 'POST', headers: { 'Content-Type': 'application/octet-stream', 'X-RDTII-Token': TOKEN }, body: f });
      let j; try { j = await r.json(); } catch (e) { j = { error: r.statusText }; }
      if (!r.ok) throw new Error(j.error || `HTTP ${r.status}`);
      const reads = !j.reads ? '' : j.reads.status === 'ready' ? `; reads as ${j.reads.method}` : `; cannot be read. ${j.reads.action}`;
      results.push(`${j.saved}: ${j.status} (${fmtBytes(j.bytes)})${reads}`);
    } catch (e) { results.push(`${f.name}: not added, ${e.message}`); }
    done += 1;
    IB.log = [`${done} of ${files.length} handled, batch ${batch}`, ...results];
    renderInbox();
  }
  IB.busy = false;
  try { IB.data = await api('/api/inbox'); } catch (e) { /* keep the old counts */ }
  await loadInboxFiles();
  renderInbox();
  loadScrapeOutputs();
  if (typeof EX !== 'undefined') EX.loaded = false;   // the Extraction tab re-reads its inputs on its next visit
}

function batchStamp() {
  const d = new Date(), p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}_${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

function cnSourceCards(d) {
  if (!SC.cnSources) SC.cnSources = new Set(d.portals.filter((p) => p.selectable && p.held).map((p) => p.src));
  const card = (p) => `<div class="portal-card ${p.mode === 'hand' ? 'hand' : ''} ${p.deferred ? 'off' : ''}">
      <div class="mode"><span class="chip ${p.mode === 'tools' ? 'ok' : 'warn'}">${p.mode === 'tools' ? 'China tools' : 'by hand'}</span></div>
      <a class="name" href="${esc(p.root)}" target="_blank" rel="noopener">${esc(p.name)}</a><span class="sub">${esc(p.note || '')}</span>
      <div class="run">${esc(p.run || '')}</div>
      <div class="held">${p.held ? `${p.held} held from it` : p.set_aside ? `${p.set_aside} listed, set aside on ${esc(p.set_aside_on || '')}` : 'nothing held yet'}</div>
      ${p.selectable ? `<label class="pick"><input type="checkbox" class="cn-src" value="${esc(p.src)}" ${SC.cnSources.has(p.src) ? 'checked' : ''}> collect it in the next run</label>` : ''}
    </div>`;
  const layer = (n, title) => { const ps = d.portals.filter((p) => p.layer === n); return ps.length ? `<div class="layer-group"><div class="layer-title">${esc(title)}</div><div class="portal-grid">${ps.map(card).join('')}</div></div>` : ''; };
  return layer(1, 'Layer 1: the national database') + layer(2, 'Layer 2: what the laws delegate to');
}



function cnPicked() {
  const d = SC.sources.CN;
  if (!d || !d.portals || !SC.cnSources) return [];
  return d.portals.filter((p) => p.selectable && SC.cnSources.has(p.src));
}

/* ---------- Extraction · Start ---------- */
EX.economy = EX.economy || '';
EX.outName = EX.outName || '';

function extractRequest() {
  const d = EX.desc;
  const economy = d && d.kind === 'hand_collected' ? (d.per_subfolder ? '' : (d.economy || EX.economy || '')) : EX.economy;
  return { input: d ? d.path : '', pack: EX.pack, workers: EX.workers,
    out_name: EX.outName || (d ? (d.out_name || d.name) : ''), economy, note: EX.note || '' };
}

function renderExtractRun() {
  const d = EX.desc;
  const note = $('#extract-run-note');
  if (!note) return;
  const ok = !!(d && !d.error);
  const outName = EX.outName || (ok ? (d.out_name || d.name) : '');
  const rootSetting = ((S.health && S.health.settings) || []).find((x) => x.name === 'RDTII_RUNS_ROOT');
  const root = rootSetting ? rootSetting.value : 'outputs';
  const BS = root.includes('/') ? '/' : String.fromCharCode(92);
  const hand = ok && d.kind === 'hand_collected';
  const needEcon = hand && !d.economy && !d.per_subfolder;
  const det = hand ? d.detected : null;
  const fails = EX.checks ? EX.checks.filter((c) => c.level === 'fail') : null;
  const canStart = ok && EX.stagePresent !== false && EX.checks && fails.length === 0;
  const target = ok ? `${esc(root)}${BS}extract${BS}${esc(outName)}` : '<span class="muted">choose an input first</span>';
  const econRow = !hand ? '' : d.per_subfolder
    ? `<div class="stack-row"><span class="setup-label">Economies</span> <span>from the folder names: ${esc(Object.keys(d.by_economy || {}).join(', '))}</span> <button class="btn small" id="ex-preview">Preview the manifest</button></div>`
    : d.economy
      ? `<div class="stack-row"><span class="setup-label">Economy</span> <span><b>${esc(econName(d.economy))}</b> (${esc(d.economy)}), from the folder name</span> <button class="btn small" id="ex-preview">Preview the manifest</button></div>`
      : `<label class="stack-row"><span class="setup-label">Economy</span> <select id="ex-econ"><option value="">choose the economy these documents belong to</option>${(EX.economies || []).map((e) => `<option value="${e.code}" ${EX.economy === e.code ? 'selected' : ''}>${esc(e.name)} (${e.code})</option>`).join('')}</select> ${EX.economy ? '<button class="btn small" id="ex-preview">Preview the manifest</button>' : ''}${det && det.suggested_economy ? `<span class="muted">${EX.economy === det.suggested_economy ? 'suggested by the text' : `the text points to ${esc(econName(det.suggested_economy))}`}</span>` : ''}</label>`;
  note.innerHTML = `
    <div class="callout time-note"><b>How well extraction works.</b>
      <ul>
        <li>It splits each law at the headings common in the economy’s laws: Section 1, Article 1, Artigo 1.º, ມາດຕາ 1, 第一条.</li>
        <li>A file laid out differently may come out as one piece, or split in the wrong places.</li>
        <li>Output lists the documents that gave no provisions, <b>to check</b>. A wrong split is not flagged: read through an unusual file yourself.</li>
      </ul></div>
    <div class="target"><span class="setup-label">Writes to</span> <code>${target}</code></div>
    <div class="stack">
      <label class="stack-row"><span class="setup-label">Output name</span> <input type="text" id="ex-out" size="22" value="${esc(outName)}" ${ok ? '' : 'disabled'}></label>
      ${econRow}
      <label class="stack-row"><span class="setup-label">OCR pack</span> <select id="ex-pack"><option value="fast" ${EX.pack === 'fast' ? 'selected' : ''}>Fast: the measured choice</option><option value="best" ${EX.pack === 'best' ? 'selected' : ''}>Best: slower, for hard scans</option></select></label>
      <label class="stack-row"><span class="setup-label">OCR workers</span> <input type="text" id="ex-workers" size="3" value="${EX.workers}"></label>
      <label class="stack-row note-row"><span class="setup-label">Run note</span> <span class="note-cell"><textarea id="ex-note" class="run-note-input" rows="3" maxlength="300" placeholder="a line to carry with this run, optional">${esc(EX.note || '')}</textarea><span class="muted">shown in Output and at Mapping’s Input</span></span></label>
      <details class="notes-box" ${EX.runNotesOpen ? 'open' : ''}><summary>Note:</summary>
        <p>* <b>Output name</b> names the folder under ${esc(root)}${BS}extract. Running into an existing folder reuses its OCR cache and frozen text; Clear OCR cache below forces a fresh OCR.</p>
        <p>* <b>OCR pack</b>: Fast is the measured choice from the stage’s own tests; Best trades time for difficult scans. <b>Workers</b> is how many pages are read at once.</p>
        ${hand ? `<p>* <b>Economy</b> names every document id and fixes the language${needEcon ? '. This folder does not name one, so the text was read to suggest it; you confirm' : ', from the folder name'}. Preview the manifest to see the ids and kinds before the run.</p>` : ''}
        ${ok && d.recoverable ? `<p>* ${d.recoverable} document(s) missing from this folder are restored from committed copies by hash.</p>` : ''}
        <p>* Interpreter: <code>${esc(EX.python || 'python')}</code>.</p>
      </details>
      <div class="stack-row full"><b>Press Check first; Start unlocks when no check fails.</b></div>
      <div class="stack-row full"><button class="btn wide" id="ex-check" ${ok && EX.stagePresent !== false ? '' : 'disabled'}>${EX.checking ? 'Checking…' : 'Check'}</button></div>
      ${EX.checks ? `<div class="stack-row full"><ul class="checks">${EX.checks.map((c) => `<li><span class="chip ${c.level === 'ok' ? 'ok' : c.level === 'warn' ? 'warn' : 'bad'}">${esc(c.level)}</span> ${esc(c.text)}</li>`).join('')}</ul></div>` : ''}
      <div class="stack-row full"><button class="btn primary wide" id="extract-start" ${canStart ? '' : 'disabled'}>Start</button></div>
    </div>`;
  if (EX.stagePresent === false) note.insertAdjacentHTML('afterbegin', '<p class="note">The extraction stage is not in this repository.</p>');
  const nb = note.querySelector('details.notes-box'); if (nb) nb.addEventListener('toggle', () => { EX.runNotesOpen = nb.open; });
  const exNote = $('#ex-note'); if (exNote) exNote.oninput = (e) => { EX.note = e.target.value; };
  $('#ex-out').onchange = (e) => { EX.outName = e.target.value.trim(); EX.checks = null; renderExtractRun(); renderExtractCmd(); };
  $('#ex-pack').onchange = (e) => { EX.pack = e.target.value; EX.checks = null; renderExtractRun(); renderExtractCmd(); };
  $('#ex-workers').onchange = (e) => { EX.workers = parseInt(e.target.value, 10) || 16; EX.checks = null; renderExtractRun(); renderExtractCmd(); };
  const econ = $('#ex-econ'); if (econ) econ.onchange = (e) => { EX.economy = e.target.value; EX.checks = null; renderExtractRun(); renderExtractCmd(); renderExtractDescribe(); };
  const pv = $('#ex-preview'); if (pv) pv.addEventListener('click', () => previewManifest(false));
  $('#ex-check').onclick = async () => {
    EX.checking = true; renderExtractRun();
    try { const j = await api('/api/extract/precheck', { method: 'POST', body: JSON.stringify(extractRequest()) }); EX.checks = j.checks; }
    catch (e) { EX.checks = [{ level: 'fail', text: e.message }]; }
    EX.checking = false; renderExtractRun();
  };
  $('#extract-start').onclick = startExtract;
}

/* How each hand-collected file will be read, and the manifest row the interface writes for it. Drawn on its own
   when the input is chosen (quiet), and on the Preview button. */
async function previewManifest(quiet) {
  const d = EX.desc;
  const seq = (EX.previewSeq = (EX.previewSeq || 0) + 1);
  const host = $('#ex-manifest-preview') || $('#extract-describe');
  try {
    const economy = d.per_subfolder ? '' : (d.economy || EX.economy || '');
    const r = await api('/api/extract/manifest/preview', { method: 'POST', body: JSON.stringify({ path: d.path, economy }) });
    if (seq !== EX.previewSeq) return;   // a later choice has replaced this one
    const rows = [...r.rows.filter((x) => x._status !== 'ready'), ...r.rows.filter((x) => x._status === 'ready')];
    const reads = (x) => x._status === 'ready'
      ? `<span class="chip ok">ready</span> <span class="small">${esc(x._method)}</span>${x._action ? `<div class="small muted">${esc(x._action)}</div>` : ''}`
      : `<span class="chip bad">cannot be read</span><div class="small">${esc(x._action)}</div>`;
    const addr = (x) => x.source_url ? `<a href="${esc(x.source_url)}" target="_blank" rel="noopener">${esc(short(x.source_url, 56))}</a><div class="small muted">${esc(x._url_basis)}</div>` : '<span class="muted">none</span>';
    host.innerHTML = `<p class="ready-line"><b>Readiness</b> <span class="chip ok">${r.ready} ready</span>${r.cannot_read ? ` <span class="chip bad">${r.cannot_read} cannot be read</span> <span class="small">left out of the run; each says what to do</span>` : ''}</p>
      <details class="doclist" ${r.cannot_read || !quiet ? 'open' : ''}><summary>Per file: how it is read, and its manifest row <span class="muted">(${r.count})</span></summary><div class="table-wrap short"><table class="rows"><thead><tr><th>File</th><th>Reads as</th><th>Address</th><th>doc_id</th><th>Type</th><th>Pages</th></tr></thead><tbody>
      ${rows.map((x) => `<tr><td class="small">${esc(x.local_path)}</td><td>${reads(x)}</td><td class="small">${addr(x)}</td><td class="num">${esc(x.doc_id)}</td><td class="small">${esc(String(x.source_type).replace(/_/g, ' '))}</td><td class="num">${esc(x.page_count)}</td></tr>`).join('')}</tbody></table></div></details>`;
  } catch (e) {
    if (seq !== EX.previewSeq) return;
    if (quiet) host.innerHTML = `<p class="small muted">${esc(e.message)}</p>`; else alert(e.message);
  }
}

async function startExtract() {
  const btn = $('#extract-start'); if (btn) btn.disabled = true;
  try {
    const r = await api('/api/extract/start', { method: 'POST', body: JSON.stringify(extractRequest()) });
    $('#extract-run-panel').innerHTML = '';
    watchJob(r.job.id, 'extract-run-panel', () => { loadExtractOutputs(); EX.checks = null; renderExtractRun(); if (typeof loadMapHandoffs === 'function') loadMapHandoffs(); });
    loadHealth();
  } catch (e) { alert(e.message); EX.checks = null; renderExtractRun(); }
}

/* ---------- Mapping · Set up + Start ---------- */
const MP = { loaded: false, handoffs: [], handoff: null, economies: new Set(), selectMode: 'scores', dense: 'auto', gloss: true, limit: '', checks: null, stagePresent: true, python: '',
  thetas: {}, caps: {}, models: null };   // thetas, caps: a number typed for an indicator, kept only while it differs from the recommended one

/* the steps of a run that call a model, in run order; `role` is what the step asks the stage for */
const MODEL_STEPS = [
  { key: 'screen', role: 'verifier', letter: 'B', title: 'Quick screen', sub: 'a fast model drops the borderline pairs that are clearly unrelated' },
  { key: 'mapper', role: 'mapper', letter: 'C', title: 'Careful reading', sub: 'each provision is read against the indicator’s rulebook' },
  { key: 'verifier', role: 'verifier', letter: 'D', title: 'Re-check', sub: 'a second model re-reads every match without seeing the first answer' },
  { key: 'escalation', role: 'escalation', letter: 'E', title: 'Tie-break', sub: 'a third model decides when the reading and the re-check disagree' },
];

/* every step on one engine's own models: what the banner's choice means */
function presetModels(eid) {
  const e = engineOf(eid);
  if (!e) return null;
  const out = {};
  MODEL_STEPS.forEach((s) => { out[s.key] = { engine: eid, model: (e.roles || {})[s.role] || ((e.models || [])[0] || {}).id || '' }; });
  return out;
}

const dollars = (x) => `$${Number(x)}`;
const priceText = (m) => !m.price ? 'no price card' : (m.price[0] === 0 && m.price[1] === 0) ? 'no charge' : `${dollars(m.price[0])} / ${dollars(m.price[1])}`;

/* one step: the provider blocks, then the models of the chosen provider */
let KEY_HINTED = new Set();
function modelBlock(step) {
  const pick = MP.models[step.key];
  const held = heldKeys();
  const e = engineOf(pick.engine);
  const provs = engineList().map((x) => {
    const on = x.id === pick.engine;
    const sub = x.key_env ? (held[x.key_env] ? 'key held' : 'no key') : 'local';
    return `<label class="radio big ${on ? 'on' : ''}"><input type="radio" name="mp-eng-${step.key}" value="${esc(x.id)}" ${on ? 'checked' : ''}> <span class="name">${esc(x.name)}</span> <span class="sub">${sub}</span></label>`;
  }).join('');
  const models = ((e && e.models) || []).map((m) => {
    const on = m.id === pick.model;
    const measured = e.measured && m.measured;
    return `<label class="radio model ${on ? 'on' : ''} ${measured ? '' : 'unmeasured'}" title="${esc(m.id)}${measured ? '' : ', not measured'}"><input type="radio" name="mp-mod-${step.key}" value="${esc(m.id)}" ${on ? 'checked' : ''}> <span class="name">${esc(m.label)}</span> <span class="sub">${esc(priceText(m))}</span></label>`;
  }).join('');
  const m = modelOf(e, pick.model);
  const notes = [];
  if (!(e && e.measured && m && m.measured)) notes.push('<span class="chip warn">not measured</span> the prompts and every reported figure were made on Claude');
  if (e && e.key_env && !held[e.key_env] && !KEY_HINTED.has(e.key_env)) {   // said once, in the first step that needs it; the pill says "no key" in each
    KEY_HINTED.add(e.key_env);
    notes.push(`<span class="chip bad">no key</span> hold the ${esc(e.name)} key in the banner above`);
  }
  return `<div class="subblock">
      <div class="subblock-head"><b><span class="letter">${step.letter}</span>${esc(step.title)}</b><span>${esc(step.sub)}</span></div>
      <div class="stack">
        <div class="stack-row"><span class="setup-label">Provider</span> <div class="picks">${provs}</div></div>
        <div class="stack-row"><span class="setup-label">Model</span> <div class="picks">${models || '<span class="muted">no model listed</span>'}</div></div>
        ${notes.length ? `<div class="stack-row"><span class="setup-label"></span> <div class="pick-note">${notes.map((n) => `<div>${n}</div>`).join('')}</div></div>` : ''}
      </div>
    </div>`;
}

/* how the number boxes stand: all recommended, or how many were typed for this run */
function numState() {
  const ids = chosenIndicators();
  if (MP.selectMode === 'caps') {
    const caps = (((S.picker || {}).selection || {}).caps || {}).per_indicator || {};
    const n = ids.filter((id) => MP.caps[id] != null).length;
    const missing = ids.filter((id) => caps[id] == null && MP.caps[id] == null).length;
    return (n ? `${n} changed for this run.` : 'Round 1’s caps, the recommended numbers.') + (missing ? ` ${missing} ticked indicator(s) have no Round 1 cap: type one, or use Score threshold.` : '');
  }
  const n = ids.filter((id) => MP.thetas[id] != null).length;
  return n ? `${n} changed for this run.` : 'The recommended numbers.';
}

/* a number was typed: the last Check no longer describes the run */
function staleMapChecks() {
  MP.checks = null;
  const start = $('#map-start'); if (start) start.disabled = true;
  const list = $('#map-run-note ul.checks'); if (list) list.closest('.stack-row').remove();
}

async function loadMapHandoffs() {
  MP.loaded = true;
  try { const j = await api('/api/map/handoffs'); MP.handoffs = j.handoffs; MP.stagePresent = j.stage_present; MP.python = j.python; MP.names = j.economy_names || {}; }
  catch (e) { $('#map-input').innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  if (!MP.handoff || !MP.handoffs.find((h) => h.id === MP.handoff)) { MP.handoff = MP.handoffs[0] ? MP.handoffs[0].id : null; MP.economies = new Set(); }
  const h = MP.handoffs.find((x) => x.id === MP.handoff);
  if (h && !MP.economies.size) Object.keys(h.economies).forEach((c) => MP.economies.add(c));
  MP.checks = null;
  renderMapInput();
}

function renderMapInput() {
  const h = MP.handoffs.find((x) => x.id === MP.handoff);
  const el = $('#map-input');
  if (!h) {
    el.innerHTML = '<p class="lead">No extraction output found yet. Run Extraction first (the demo takes about a minute), or point HANDOFF2_DIR at one.</p>';
    renderMapRun();
    return;
  }
  const name = (c) => (MP.names && MP.names[c]) || c;
  el.innerHTML = `
    <div class="setup-row"><div class="setup-label">Input</div>
      <div><select id="mp-handoff" class="wide-select">${MP.handoffs.map((x) => `<option value="${esc(x.id)}" ${x.id === MP.handoff ? 'selected' : ''}>${esc(x.id)}: ${x.documents} documents, ${x.provisions} provisions, ${Object.keys(x.economies).join(', ')} (${esc(x.kind)})</option>`).join('')}</select></div>
    </div>
    ${h.note ? `<div class="setup-row"><div class="setup-label">Run note</div><div>${carried(h)} <span class="small muted">written when this extraction was started</span></div></div>` : ''}
    <div class="setup-row"><div class="setup-label">Economies</div>
      <div class="row">${Object.entries(h.economies).map(([c, k]) => `<label class="radio big ${MP.economies.has(c) ? 'on' : ''}"><input type="checkbox" value="${c}" ${MP.economies.has(c) ? 'checked' : ''}> <span class="name">${esc(name(c))}</span> <span class="sub">${k} law${k === 1 ? '' : 's'}, ${esc(h.languages[c] || '?')}</span></label>`).join('')}</div>
    </div>`;
  $('#mp-handoff').onchange = (e) => { MP.handoff = e.target.value; MP.economies = new Set(); const hh = MP.handoffs.find((x) => x.id === MP.handoff); if (hh) Object.keys(hh.economies).forEach((c) => MP.economies.add(c)); MP.checks = null; renderMapInput(); };
  el.querySelectorAll('input[type=checkbox][value]').forEach((inp) => inp.addEventListener('change', () => { if (inp.checked) MP.economies.add(inp.value); else MP.economies.delete(inp.value); MP.checks = null; renderMapInput(); }));
  renderMapRun();
}

/* a number box per ticked indicator: its threshold in scores mode, its cap in caps mode; the recommended number is the default */
function selectionLine() {
  const sel = (S.picker || {}).selection;
  if (!sel) return '<span class="muted">loading the values…</span>';
  const ids = chosenIndicators();
  if (!ids.length) return '<span class="muted">tick an indicator</span>';
  if (MP.selectMode === 'caps') {
    const caps = (sel.caps || {}).per_indicator || {};
    const range = sel.cap_range || [1, 5000];
    const parts = ids.map((id) => {
      const typed = MP.caps[id] != null; const val = typed ? MP.caps[id] : (caps[id] != null ? caps[id] : '');
      const tip = caps[id] != null ? `recommended: ${caps[id]}, Round 1’s cap` : 'Round 1 has no cap for this indicator: type one, or use Score threshold';
      return `<label class="theta num ${typed ? 'moved' : ''} ${val === '' ? 'bad' : ''}" title="${esc(tip)}"><b>${esc(id)}</b><input type="number" class="mp-num" data-id="${esc(id)}" min="${range[0]}" max="${range[1]}" step="10" value="${val}" placeholder="none"></label>`;
    });
    return parts.join(' ') + `<span class="muted small">counts of provisions, not scores; grey band ${esc(String((sel.caps || {}).gray_mult || 3))}\u00d7 the cap</span>`;
  }
  const measured = new Set(sel.measured || Object.keys(sel.thetas || {}));
  const range = sel.theta_range || [0.05, 0.95];
  const parts = ids.map((id) => {
    if (sel.thetas[id] == null) return `<span class="theta bad"><b>${esc(id)}</b> none</span>`;
    const typed = MP.thetas[id] != null; const rec = Number(sel.thetas[id]).toFixed(2);
    const tip = `recommended: ${rec}, ${measured.has(id) ? 'measured' : 'the default of its class, ' + ((sel.classes || {})[id] || '')}`;
    return `<label class="theta num ${measured.has(id) ? '' : 'cls'} ${typed ? 'moved' : ''}" title="${esc(tip)}"><b>${esc(id)}</b><input type="number" class="mp-num" data-id="${esc(id)}" min="${range[0]}" max="${range[1]}" step="0.01" value="${typed ? Number(MP.thetas[id]).toFixed(2) : rec}"></label>`;
  });
  const unmeasured = ids.filter((id) => !measured.has(id)).length;
  const offs = Object.entries(sel.language_offset || {}).filter(([k, v]) => k !== '_default' && Number(v) !== 0).map(([k, v]) => `${k} ${v}`).join(', ');
  return parts.join(' ') + `<span class="muted small">${offs ? `language offset ${esc(offs)}` : ''}${unmeasured ? `${offs ? '; ' : ''}italic values are class defaults, not measured` : ''}</span>`;
}

function chosenIndicators() {
  return [...document.querySelectorAll('#map-setup input[type=checkbox]:checked')].map((i) => i.value);
}

function mapRequest() {
  const ids = chosenIndicators();
  const typed = (store) => { const o = {}; ids.forEach((id) => { if (store[id] != null) o[id] = store[id]; }); return o; };   // ticked indicators only
  return { handoff: MP.handoff, economies: [...MP.economies], indicators: ids,
    engine: MP.models ? MP.models.mapper.engine : (S.health && S.health.engine ? S.health.engine.selected : null), models: MP.models || undefined,
    thetas: MP.selectMode === 'scores' ? typed(MP.thetas) : {}, caps: MP.selectMode === 'caps' ? typed(MP.caps) : {},
    select_mode: MP.selectMode, dense: MP.dense, gloss: MP.gloss, limit: MP.limit ? parseInt(MP.limit, 10) : null, note: MP.note || '' };
}

async function runMapCheck() {
  MP.checking = true; renderMapRun();
  try { const j = await api('/api/map/precheck', { method: 'POST', body: JSON.stringify(mapRequest()) }); MP.checks = j.checks; }
  catch (e) { MP.checks = [{ level: 'fail', check: 'request', text: e.message }]; }
  MP.checking = false; renderMapRun();
}

function renderMapChecks() {
  const chip = { ok: 'chip ok', warn: 'chip warn', fail: 'chip bad' };
  return MP.checks ? `<ul class="checks">${MP.checks.map((c) => `<li><span class="${chip[c.level] || 'chip'}">${esc(c.level)}</span> ${esc(c.text)}</li>`).join('')}</ul>` : '';
}

function renderMapRun() {
  const note = $('#map-run-note');
  if (!note) return;
  const h = MP.handoffs.find((x) => x.id === MP.handoff);
  const eng = S.health && S.health.engine ? S.health.engine : null;
  if (!MP.models && eng && eng.selected) MP.models = presetModels(eng.selected);
  const runEngine = MP.models ? MP.models.mapper.engine : (eng && eng.selected) || 'A';   // the careful reading's engine names the run
  const capsMode = MP.selectMode === 'caps';
  const typedNow = chosenIndicators().some((id) => (capsMode ? MP.caps : MP.thetas)[id] != null);
  const rootSetting = ((S.health && S.health.settings) || []).find((x) => x.name === 'RDTII_RUNS_ROOT');
  const root = rootSetting ? rootSetting.value : 'outputs';
  const BS = root.includes('/') ? '/' : String.fromCharCode(92);
  const fails = MP.checks ? MP.checks.filter((c) => c.level === 'fail') : null;
  const canStart = !!(MP.stagePresent && h && MP.checks && fails.length === 0);
  const idx = h ? h.index : null;
  const idxState = idx ? [idx.corpus ? 'corpus ready' : 'no corpus', idx.bm25 ? 'keyword index ready' : 'no keyword index', idx.dense ? (idx.dense_is_stub ? 'meaning index stubbed' : 'meaning index ready') : 'no meaning index'].join(', ') : '';
  // the index holds a ranking per indicator: one that is ticked and missing means both legs are ranked again at Start
  const idxRanked = (idx && idx.indicators && idx.indicators.bm25) || null;
  const idxLacks = idxRanked ? chosenIndicators().filter((i) => !idxRanked.includes(i)) : [];
  // what the next run does with the index: Build rebuilds from scratch; Auto and Skip rebuild only when it is older than the output
  const idxPlan = !idx || !idx.corpus ? '' : MP.dense === 'real' ? '<span class="chip">Build: rebuilt from scratch</span>'
    : idx.stale ? `<span class="chip warn">older than the output (${esc(idx.built || '')} against ${esc(idx.source_written || '')}), will be rebuilt</span>`
    : idxLacks.length ? `<span class="chip">ranked for ${esc(idxRanked.join(', ') || 'no indicator')}; ranked again at Start</span>` : '<span class="chip ok">as new as the output</span>';
  note.innerHTML = `
    <div class="targets">
      <div class="target"><span class="setup-label">Writes to</span> <code>${esc(root)}${BS}map${BS}${stamp()}_${esc(runEngine)}${BS}out</code> <span class="muted">(a new folder, created at Start)</span></div>
    </div>
    <div class="subblock">
      <div class="subblock-head"><b><span class="letter">A</span>Candidate selection</b><span>which provisions go forward, scored by meaning with BGE-M3</span></div>
      <div class="stack">
      ${idx ? `<div class="stack-row"><span class="setup-label">Index</span> <div class="idxline"><code>${esc(idx.id)}</code> <span class="muted">${esc(idxState)}</span> ${idxPlan} ${idx.corpus ? `<button class="btn small" data-clear="${esc(idx.dir)}" data-what="the corpus index">Clear index</button>` : ''}</div></div>` : ''}
      <label class="stack-row"><span class="setup-label">Selection</span> <select id="mp-mode"><option value="scores" ${MP.selectMode === 'scores' ? 'selected' : ''}>Score threshold</option><option value="caps" ${MP.selectMode === 'caps' ? 'selected' : ''}>Caps</option></select></label>
      <div class="stack-row"><span class="setup-label">${capsMode ? 'Caps' : 'Thresholds'}</span> <div class="thetas" id="mp-thetas">${selectionLine()}</div></div>
      <div class="stack-row"><span class="setup-label"></span> <div class="num-state"><b id="mp-num-state" class="${typedNow ? 'moved' : ''}">${esc(numState())}</b> <button class="btn small" id="mp-num-reset" ${typedNow ? '' : 'disabled'}>Reset to recommended</button> <span class="muted">type in a box to change one indicator, for this run only</span></div></div>
      <label class="stack-row"><span class="setup-label">Meaning index</span> <select id="mp-dense"><option value="auto" ${MP.dense === 'auto' ? 'selected' : ''}>Auto</option><option value="real" ${MP.dense === 'real' ? 'selected' : ''}>Build</option><option value="stub" ${MP.dense === 'stub' ? 'selected' : ''}>Skip</option></select> <span class="muted">matches provisions to indicators by meaning, in any language; the thresholds are read on its score</span></label>
      </div>
    </div>
    ${MP.models ? (KEY_HINTED = new Set(), MODEL_STEPS.map(modelBlock)).join('') : ''}
    <div class="stack">
      <label class="stack-row"><span class="setup-label">Translation</span> <input type="checkbox" id="mp-gloss" ${MP.gloss ? 'checked' : ''}> <span>for review</span></label>
      <label class="stack-row"><span class="setup-label">Quick run</span> <input type="text" id="mp-limit" size="5" value="${esc(MP.limit)}" placeholder="all"> <span>map at most this many provisions per economy; blank for everything</span></label>
      <label class="stack-row note-row"><span class="setup-label">Run note</span> <span class="note-cell"><textarea id="mp-note" class="run-note-input" rows="3" maxlength="300" placeholder="a line to carry with this run, optional">${esc(MP.note || '')}</textarea><span class="muted">shown in Output</span></span></label>
      <details class="notes-box" ${MP.runNotesOpen ? 'open' : ''}><summary>Note:</summary>
        <ul class="note-list">
          <li><b>A Candidate selection</b>: the first step of a run, which provisions go forward for each indicator.
            <ul>
              <li><b>Score threshold</b>, the stage’s default: keep every provision whose meaning score clears the indicator’s threshold. Needs the meaning index.</li>
              <li><b>Caps</b>: rank the provisions by score and keep the top N per indicator and economy, N being Round 1’s numbers. Works with the keyword index alone.</li>
              <li><b>Why two units</b>: a threshold is a score, a cosine between 0 and 1 that each provision must clear, so how many pass follows the corpus. A cap is a count, so how many pass is fixed whatever the scores. Round 1 fixed the count; the finale measured the score instead, so the two rules cannot share one setting.</li>
              <li>The quick screen of the borderline pairs is the next step, block B.</li>
            </ul>
          </li>
          <li><b>Thresholds</b>: from the stage’s selection.json, shown for the ticked indicators.
            <ul>
              <li>Measured for the nine indicators of pillars 6 and 7. The other 52 take the default of their class from the codebook, 0.55 to 0.60, shown in italics.</li>
              <li>A small offset per language; at 0.65 or above a candidate skips triage.</li>
              <li><b>Each box holds the recommended number</b>: the measured threshold, or the class default. Type another to change that indicator for this run only. Lower reads more candidates and costs more; higher reads fewer. The run reads a copy of selection.json written into its own folder; <mark>the stage’s file is never changed</mark>. Reset puts the recommended numbers back.</li>
            </ul>
          </li>
          <li><b>Caps</b>: a cap on the number of provisions, ranked by score. Round 1’s numbers, 150 to 600 per indicator and economy; the grey band takes three times the cap. Each box holds Round 1’s cap; type another to change that indicator for this run only.
            <ul>
              <li><mark>No cap exists outside pillars 6 and 7</mark>: Round 1 never ran those indicators, so their boxes are empty. Type a cap to run one this way, or use Score threshold; Check refuses a ticked indicator with no cap.</li>
            </ul>
          </li>
          <li><b>Meaning index</b>: BGE-M3 scores every provision against every indicator by meaning, in any language. The thresholds are read on this score, and the keyword index alone reads almost nothing in Chinese or Lao. Built once per extraction output and reused until that output changes.
            <ul>
              <li><b>Auto</b>: reuse the index when it is as new as the extraction output; build it when it is missing, stubbed or older. The Index line above says which.</li>
              <li><b>Build</b>: build everything from scratch now, the manual rebuild for the rare case the dates cannot see. Needs torch and a one-time 2 GB model download.</li>
              <li><b>Skip</b>: keyword only. Fine for English economies on Caps.</li>
            </ul>
          </li>
          <li><b>B Quick screen, C Careful reading, D Re-check, E Tie-break</b>: the four steps that call a model. Each takes a provider and one of its models; the banner’s engine sets all four at once.
            <ul>
              <li><mark>Measured: Claude Sonnet 5, Haiku 4.5 and Opus 4.8, and local Qwen 2.5.</mark> The prompts and the traps were written for Claude, and every reported figure comes from those models. Anything else is marked not measured: try it on a Quick run first.</li>
              <li>Prices are US dollars per million tokens, input then output, from each provider’s own page on 4 October 2026; DeepSeek’s is its peak rate. Claude Sonnet 5 shows the stage’s own card, which the reported costs used.</li>
              <li>Each hosted provider reads its own API key, held in memory in the banner. The translation for review uses the Re-check model, and the economy-level scores use the Careful reading model.</li>
            </ul>
          </li>
          <li><b>Translation</b>: machine English of the quotes for the review screen only; never in the export.</li>
          <li><b>Quick run</b>: one number applied twice, triage judges only the first N borderline pairs and the careful reading maps only the first N provisions per economy. For a proof of the chain in minutes, not for coverage. Blank runs everything.</li>
          <li>Every run writes a new folder; the engine, the cost and each substage are recorded in its run_manifest.json. Interpreter: <code>${esc(MP.python || 'python')}</code>.</li>
        </ul>
      </details>
      <div class="stack-row full"><b>Press Check first; Start unlocks when no check fails.</b></div>
      <div class="stack-row full"><button class="btn wide" id="mp-check" ${h && MP.stagePresent ? '' : 'disabled'}>${MP.checking ? 'Checking…' : 'Check'}</button></div>
      ${MP.checks ? `<div class="stack-row full">${renderMapChecks()}</div>` : ''}
      <div class="stack-row full"><button class="btn primary wide" id="map-start" ${canStart ? '' : 'disabled'}>Start</button></div>
    </div>`;
  if (!MP.stagePresent) note.insertAdjacentHTML('afterbegin', '<p class="note">The mapping stage is not in this repository.</p>');
  const nb = note.querySelector('details.notes-box'); if (nb) nb.addEventListener('toggle', () => { MP.runNotesOpen = nb.open; });
  const mpNote = $('#mp-note'); if (mpNote) mpNote.oninput = (e) => { MP.note = e.target.value; };
  $('#mp-mode').onchange = (e) => { MP.selectMode = e.target.value; MP.checks = null; renderMapRun(); };
  note.querySelectorAll('input.mp-num').forEach((inp) => inp.addEventListener('change', () => {
    const id = inp.dataset.id; const caps = MP.selectMode === 'caps';
    const sel = (S.picker || {}).selection || {};
    const rec = caps ? ((sel.caps || {}).per_indicator || {})[id] : (sel.thetas || {})[id];
    const range = caps ? (sel.cap_range || [1, 5000]) : (sel.theta_range || [0.05, 0.95]);
    const store = caps ? MP.caps : MP.thetas;
    let v = inp.value.trim() === '' ? NaN : Number(inp.value);
    if (!Number.isNaN(v)) v = Math.min(range[1], Math.max(range[0], caps ? Math.round(v) : Math.round(v * 100) / 100));
    if (Number.isNaN(v) || (rec != null && v === Number(rec))) delete store[id]; else store[id] = v;   // the recommended number is not a change
    // only this box is redrawn, so the next one keeps the focus when tabbing through them
    const shown = store[id] != null ? store[id] : rec;
    inp.value = shown == null ? '' : (caps ? shown : Number(shown).toFixed(2));
    inp.parentElement.classList.toggle('moved', store[id] != null);
    inp.parentElement.classList.toggle('bad', shown == null);
    const any = chosenIndicators().some((x) => store[x] != null);
    $('#mp-num-state').textContent = numState(); $('#mp-num-state').classList.toggle('moved', any); $('#mp-num-reset').disabled = !any;
    staleMapChecks();
  }));
  $('#mp-num-reset').onclick = () => { if (MP.selectMode === 'caps') MP.caps = {}; else MP.thetas = {}; MP.checks = null; renderMapRun(); };
  note.querySelectorAll('input[name^="mp-eng-"]').forEach((inp) => inp.addEventListener('change', () => {
    const step = MODEL_STEPS.find((x) => x.key === inp.name.slice(7)); const e = engineOf(inp.value);
    MP.models[step.key] = { engine: inp.value, model: (e.roles || {})[step.role] || ((e.models || [])[0] || {}).id || '' };
    MP.checks = null; renderMapRun(); renderTop();   // the banner shows a key row for each provider in use
  }));
  note.querySelectorAll('input[name^="mp-mod-"]').forEach((inp) => inp.addEventListener('change', () => { MP.models[inp.name.slice(7)].model = inp.value; MP.checks = null; renderMapRun(); }));
  $('#mp-dense').onchange = (e) => { MP.dense = e.target.value; MP.checks = null; renderMapRun(); };
  $('#mp-gloss').onchange = (e) => { MP.gloss = e.target.checked; };
  $('#mp-limit').onchange = (e) => { MP.limit = e.target.value.trim(); MP.checks = null; renderMapRun(); };
  $('#mp-check').onclick = runMapCheck;
  $('#map-start').onclick = startMap;
  bindClear('#map-run-note', () => { MP.checks = null; loadMapHandoffs(); });
}

async function startMap() {
  $('#map-start').disabled = true;
  try {
    const r = await api('/api/map/start', { method: 'POST', body: JSON.stringify(mapRequest()) });
    $('#map-run-panel').innerHTML = '';
    const outDir = r.job.out_dir || '';
    watchJob(r.job.id, 'map-run-panel', async (j) => {
      await loadRuns();
      const name = outDir.replace(/\\/g, '/').split('/').pop();
      const hit = S.runs.find((x) => x.id.endsWith('/' + name));
      if (hit) { S.run = hit.id; S.sel = null; $('#map-detail').innerHTML = ''; renderRunRow(); loadRows(); }
      MP.checks = null; loadMapHandoffs();
    });
    loadHealth();
  } catch (e) { alert(e.message); renderMapRun(); }
}

/* ---------- Review and export ---------- */
const RV = { reasons: ['wrong indicator', 'quote not in the source', 'citation wrong', 'provision not in force', 'out of scope', 'other'], reviewer: '' };

const decisionChip = (d) => !d ? '' : d.verdict === 'accept' ? '<span class="chip ok">accepted</span>' : d.verdict === 'reject' ? `<span class="chip bad" title="${esc(d.reason)}">rejected</span>` : `<span class="chip warn" title="${esc(Object.keys(d.corrections || {}).join(', '))}">corrected</span>`;

function reviewControls(d) {
  if (d._read_only) return '<div class="row" style="margin-top:10px"><span class="muted small">The filed submission is frozen: read-only. Review applies to run output.</span></div>';
  const dec = d._decision;
  const hist = (d._decision_history || []).length;
  return `<div class="review" style="margin-top:10px">
    <div class="row">
      <span class="rv-label">Review as</span> <input type="text" id="rv-name" size="14" value="${esc(RV.reviewer || (S.health && S.health.reviewer) || '')}" placeholder="your name">
      <button class="btn" id="rv-accept">Accept</button>
      <button class="btn" id="rv-reject">Reject…</button>
      <button class="btn" id="rv-correct">Correct…</button>
      ${dec ? `${decisionChip(dec)} <span class="muted small">by ${esc(dec.reviewer)} at ${esc(dec.decided_at)}${dec.reason ? `: ${esc(dec.reason)}` : ''}${hist > 1 ? `, ${hist} decisions on this row` : ''}</span> <button class="btn" id="rv-clear" title="withdraw this decision; the log keeps it">Clear decision</button>` : '<span class="chip warn rv-none">no decision yet</span>'}
    </div>
    <div id="rv-form"></div>
  </div>`;
}

function bindReview(d) {
  const name = () => { const v = ($('#rv-name') || {}).value || ''; RV.reviewer = v.trim(); return RV.reviewer; };
  const post = async (body) => {
    try {
      await api('/api/map/decisions', { method: 'POST', body: JSON.stringify({ run: S.run, i: d._i, reviewer: name(), ...body }) });
      await loadRows(); openRow(d._i); loadExportSummary();
    } catch (e) { alert(e.message); }
  };
  const acc = $('#rv-accept'); if (acc) acc.onclick = () => post({ verdict: 'accept' });
  const clr = $('#rv-clear'); if (clr) clr.onclick = () => post({ verdict: 'clear' });
  const rej = $('#rv-reject'); if (rej) rej.onclick = () => {
    $('#rv-form').innerHTML = `<div class="row" style="margin-top:8px"><label>Reason <select id="rv-reason">${RV.reasons.map((r) => `<option>${esc(r)}</option>`).join('')}</select></label> <input type="text" id="rv-reason-text" size="40" placeholder="detail (optional, required for “other”)"> <button class="btn primary" id="rv-reject-go">Reject this row</button> <button class="btn" id="rv-cancel">Cancel</button></div>`;
    $('#rv-reject-go').onclick = () => { const r = $('#rv-reason').value, t = $('#rv-reason-text').value.trim(); if (r === 'other' && !t) { alert('Say why.'); return; } post({ verdict: 'reject', reason: t ? `${r}: ${t}` : r }); };
    $('#rv-cancel').onclick = () => { $('#rv-form').innerHTML = ''; };
  };
  const cor = $('#rv-correct'); if (cor) cor.onclick = () => {
    const fields = ['Indicator ID', 'Article / Section', 'Verbatim Snippet', 'Discovery Tag', 'Notes'];
    $('#rv-form').innerHTML = `<div class="correct" style="margin-top:8px">
      <p class="small muted">Only these five fields can be corrected; every other column stays as the pipeline wrote it. A snippet must remain a passage of the source text shown above, never the translation.</p>
      ${fields.map((f) => f === 'Discovery Tag'
        ? `<label class="cf">${esc(f)} <select data-col="${esc(f)}"><option value="NEW" ${d[f] === 'NEW' ? 'selected' : ''}>NEW</option><option value="KNOWN" ${d[f] === 'KNOWN' ? 'selected' : ''}>KNOWN</option><option value="" ${d[f] === '' ? 'selected' : ''}>blank (no provision)</option></select></label>`
        : f === 'Verbatim Snippet' || f === 'Notes'
          ? `<label class="cf">${esc(f)}<textarea data-col="${esc(f)}" rows="3">${esc(d[f])}</textarea></label>`
          : `<label class="cf">${esc(f)} <input type="text" data-col="${esc(f)}" value="${esc(d[f])}" size="${f === 'Indicator ID' ? 8 : 24}"></label>`).join('')}
      <div class="row"><button class="btn primary" id="rv-correct-go">Save the correction</button> <button class="btn" id="rv-cancel">Cancel</button></div></div>`;
    $('#rv-correct-go').onclick = () => {
      const corrections = {};
      $('#rv-form').querySelectorAll('[data-col]').forEach((el) => { if (el.value !== d[el.dataset.col]) corrections[el.dataset.col] = el.value; });
      if (!Object.keys(corrections).length) { alert('Nothing changed.'); return; }
      post({ verdict: 'correct', corrections });
    };
    $('#rv-cancel').onclick = () => { $('#rv-form').innerHTML = ''; };
  };
}

async function loadExportSummary() {
  const el = $('#map-export');
  if (!el || !S.run) return;
  let j;
  try { j = await api(`/api/map/export/summary?${new URLSearchParams({ run: S.run, economy: S.filters.economy })}`); } catch (e) { el.innerHTML = ''; return; }
  const qs = (fmt) => `/api/map/export?${new URLSearchParams({ run: S.run, economy: S.filters.economy, fmt })}`;
  el.innerHTML = `<div class="setup-row"><div class="setup-label">Export</div><div>
    <div class="row"><a class="btn wide" href="${qs('csv')}" data-export="csv">Export CSV</a> <a class="btn wide" href="${qs('xlsx')}" data-export="xlsx">Export xlsx</a> <span class="muted">${esc(S.filters.economy || 'all economies')}: <b>${j.rows_out}</b> of ${j.rows_in} rows</span></div>
    <details class="notes-box" ${RV.exportNotesOpen ? 'open' : ''}><summary>Note:</summary>
      <p>* ${j.frozen ? 'Filed rows are exported as they are.' : `<b>${j.decisions}</b> decision(s) so far: ${j.accepted} accepted, ${j.rejected} rejected, ${j.corrected} corrected. Rejected rows are removed and corrections applied.`}</p>
      <p>* The file carries the host’s 14 columns; column O is left to the host’s formula.</p>
      <p>* review_log.csv is written beside the file in <code>${esc(j.export_dir)}</code>.</p>
    </details>
    <div id="export-saved"></div></div></div>`;
  const nb = el.querySelector('details.notes-box'); if (nb) nb.addEventListener('toggle', () => { RV.exportNotesOpen = nb.open; });
  // in the tool's own window there is no download bar: the server keeps the file and the page says where
  if (SHELL.kind === 'window') el.querySelectorAll('a[data-export]').forEach((a) => a.addEventListener('click', async (e) => {
    e.preventDefault();
    const out = $('#export-saved');
    try {
      const r = await api(`${qs(a.dataset.export)}&save=1`);
      out.innerHTML = `<p class="saved-line"><span class="chip ok">saved</span> <b>${esc(r.filename)}</b>, ${r.rows} rows, in <code>${esc(r.folder_id)}</code> <button class="btn small" data-open="${esc(r.folder)}">Open folder</button></p>`;
      bindOpen('#export-saved');
    } catch (err) { out.innerHTML = `<p class="note">${esc(err.message)}</p>`; }
  }));
}

/* ---------- Scraping · Start ---------- */
SC.mode = SC.mode || 'fresh'; SC.folder = SC.folder || ''; SC.frontier = SC.frontier || 'links'; SC.dryRun = SC.dryRun || false; SC.checks = null; SC.folders = SC.folders || [];

/* which link list each ticked economy would replay: the shipped one, or one refreshed from this page */
function listLine(codes) {
  return codes.map((c) => { const e = (SC.econs || []).find((x) => x.code === c) || {};
    return e.list_built ? `${c}: ${e.list_origin === 'refreshed' ? 'refreshed here' : 'shipped'}, ${e.list_built}` : ''; }).filter(Boolean).join(' · ');
}

/* the crawl folders one economy's second pass may run over, newest first */
function runsOf(code) {
  return (SC.folders || []).filter((f) => f.kind === 'interface run' && (f.economy ? f.economy === code : !!(f.by_economy && f.by_economy[code])));
}

function passFolder(code) {
  const runs = runsOf(code);
  const picked = (SC.pass || {})[code];
  return runs.find((f) => f.id === picked) || runs[0] || null;
}

function scrapeRequest() {
  const mode = SC.cnMode === 'collect_cac' || SC.cnMode === 'collect_all' ? 'collect' : (SC.cnMode || 'update');
  const engine = [...SC.chosen].filter((c) => c !== 'CN');
  const folders = {};
  if (SC.mode === 'same') engine.forEach((c) => { const f = passFolder(c); if (f) folders[c] = f.id; });
  return { economies: [...SC.chosen], scope: SC.scope, forms: SC.forms, dry_run: SC.dryRun, mode: SC.mode, frontier: SC.frontier,
    folders: SC.mode === 'same' ? folders : null, limit: SC.mode === 'fresh' && SC.limit ? SC.limit : null,
    cn_mode: mode, cn_sources: cnPicked().map((p) => p.src), note: SC.note || '' };
}

function renderScrapeRun() {
  const note = $('#scrape-run-note');
  if (!note) return;
  const fails = SC.checks ? SC.checks.filter((c) => c.level === 'fail') : null;
  const rootSetting = ((S.health && S.health.settings) || []).find((x) => x.name === 'RDTII_RUNS_ROOT');
  const root = rootSetting ? rootSetting.value : 'outputs';
  const BS = root.includes('/') ? '/' : String.fromCharCode(92);  // the machine's own separator; the backslash is kept out of the template literal
  const codes = [...SC.chosen];
  const engineCodes = codes.filter((c) => c !== 'CN');
  const china = codes.includes('CN');
  const same = SC.mode === 'same';
  const engineTarget = !engineCodes.length ? '' : same
    ? engineCodes.map((c) => { const f = passFolder(c); return f ? `${esc(f.path)} <span class="muted">(${esc(c)}: ${f.rows} documents already there; only new laws are fetched)</span>` : `<span class="muted">${esc(c)}: no crawl folder yet, run a new crawl first</span>`; }).join('<br>')
    : engineCodes.map((c) => { const k = ((SC.econs || []).find((e) => e.code === c) || {}).source; return k ? `${esc(root)}${BS}scrape${BS}${esc(c)}${BS}${esc(k)}${BS}${stamp()}` : `${esc(root)}${BS}scrape${BS}${esc(c)}_${stamp()}`; }).join('<br>')
      + ` <span class="muted">(${engineCodes.length === 1 ? 'a new folder' : 'a new folder and a run for each economy'}, filed by economy and source, created at Start)</span>`;
  const chinaTarget = china ? `${esc(root)}${BS}scrape${BS}CN${BS}china-tools${BS}${stamp()} <span class="muted">(China, a new folder for the China tools)</span>` : '';
  const target = [engineTarget, chinaTarget].filter(Boolean).join('<br>') || '<span class="muted">pick at least one economy</span>';
  const canStart = SC.stagePresent !== false && SC.checks && fails.length === 0;
  const mode = SC.cnMode === 'collect_cac' || SC.cnMode === 'collect_all' ? 'collect' : (SC.cnMode || 'update');
  const picked = cnPicked();
  const pickedNames = picked.map((p) => p.name.split(' ')[0]).join(', ');
  const passRows = !same ? '' : engineCodes.map((c) => { const runs = runsOf(c); const cur = passFolder(c);
    return `<label class="stack-row"><span class="setup-label">${esc(c)} folder</span> <select class="sc-pass" data-code="${esc(c)}">${runs.length ? runs.map((f) => `<option value="${esc(f.id)}" ${cur && cur.id === f.id ? 'selected' : ''}>${esc(f.id)} (${f.rows} documents)</option>`).join('') : '<option value="">no crawl folder for this economy yet</option>'}</select></label>`; }).join('');
  note.innerHTML = `
    <div class="callout time-note"><b>How long scraping takes.</b>
      <ul>
        <li><b>Quick run:</b> about a minute.</li>
        <li><b>Sample:</b> 5 to 35 minutes per economy.</li>
        <li><b>All:</b> 2 to 5 hours per economy; Singapore needs pauses and a second pass.</li>
        <li><b>Refresh from the portal</b> reads the listings first: 2 minutes (Timor-Leste) to over 2 hours (Malaysia).</li>
        <li><b>China tools:</b> the update check about 2 minutes, collecting CAC about 25.</li>
      </ul>
      Check gives the figures for your choice.</div>
    <div class="target"><span class="setup-label">Writes to</span> <code>${target}</code></div>
    <div class="stack">
      ${engineCodes.length ? `<label class="stack-row"><span class="setup-label">Run</span> <select id="sc-mode"><option value="fresh" ${!same ? 'selected' : ''}>New crawl</option><option value="same" ${same ? 'selected' : ''}>Update an existing crawl</option></select></label>
      ${passRows}
      <label class="stack-row"><span class="setup-label">Sources</span> <select id="sc-frontier"><option value="links" ${SC.frontier === 'links' ? 'selected' : ''}>Link list</option><option value="discover" ${SC.frontier === 'discover' ? 'selected' : ''}>Refresh from the portal</option></select> <span class="muted">${esc(listLine(engineCodes))}</span></label>
      <label class="stack-row"><span class="setup-label">Quick run</span> <input type="text" id="sc-limit" size="5" value="${esc(same ? '' : (SC.limit || ''))}" placeholder="all" ${same ? 'disabled' : ''}> <span>fetch only the first documents of each economy; blank for all</span></label>` : ''}
      ${china ? `<label class="stack-row"><span class="setup-label">China</span> <select id="sc-cn"><option value="update" ${mode === 'update' ? 'selected' : ''}>Update check: what changed at CAC and gov.cn</option><option value="collect" ${mode === 'collect' ? 'selected' : ''}>Collect the ticked publishers${pickedNames ? `: ${esc(pickedNames)}` : ' (none ticked yet)'}</option></select></label>` : ''}
      <label class="stack-row"><span class="setup-label">Dry run</span> <input type="checkbox" id="sc-dry" ${SC.dryRun ? 'checked' : ''}> <span>list only, fetch nothing</span></label>
      <label class="stack-row note-row"><span class="setup-label">Run note</span> <span class="note-cell"><textarea id="sc-note" class="run-note-input" rows="3" maxlength="300" placeholder="a line to carry with this run, optional">${esc(SC.note || '')}</textarea><span class="muted">shown in Output and at Extraction’s Input</span></span></label>
      <details class="notes-box" ${SC.runNotesOpen ? 'open' : ''}><summary>Note:</summary>
        <p>* <b>New crawl</b> writes into a new folder, filed by economy and source; several economies run one after another, one folder each. <b>Update an existing crawl</b> reuses that economy's folder and fetches only laws not already retrieved, which is how a second pass over a complete folder fetches zero.</p>
        <p>* <b>Link list</b>: the document addresses are already known, so fetching starts at once. It is the list shipped with the crawler, or the one last refreshed here. <b>Refresh from the portal</b>: the portal's listings are read again first, the new list is kept under the runs root and used from then on, and the documents are fetched from it. Reading the listings takes from two minutes (Timor-Leste) to over two hours (Malaysia); Check says how long for each economy. With Dry run ticked it only rebuilds the list.</p>
        <p>* <b>Quick run</b>: a number, for example 5, fetches only the first documents of each economy. A proof in a minute that fetching works, not a crawl. Blank fetches everything in scope, which takes hours for All.</p>
        ${china ? `<p>* <b>China</b> runs through the China tools, not the crawler, as a job of its own. <b>Update check</b> compares CAC and gov.cn with the shipped collection and fetches what is new. <b>Collect</b> takes the whole index of each publisher ticked on the China card, one pass each: CAC alone takes about 25 minutes, several publishers an hour or more. The documents then appear in 2 Extraction → Input with the economy fixed to China. The national database, MIIT and Customs stay by hand.</p>` : ''}
        <p>* <b>Dry run</b> lists what would be fetched and fetches nothing; no manifest is written.</p>
      </details>
      <div class="stack-row full"><span class="setup-label">Press Check first; Start unlocks when no check fails.</span></div>
      <div class="stack-row full"><button class="btn wide" id="sc-check">${SC.checking ? 'Checking…' : 'Check'}</button></div>
      ${SC.checks ? `<div class="stack-row full"><ul class="checks">${SC.checks.map((c) => `<li><span class="chip ${c.level === 'ok' ? 'ok' : c.level === 'warn' ? 'warn' : 'bad'}">${esc(c.level)}</span> ${esc(c.text)}</li>`).join('')}</ul></div>` : ''}
      <div class="stack-row full"><button class="btn primary wide" id="scrape-start" ${canStart ? '' : 'disabled'}>Start</button></div>
    </div>`;
  const rn = note.querySelector('details.notes-box'); if (rn) rn.addEventListener('toggle', () => { SC.runNotesOpen = rn.open; });
  const scNote = $('#sc-note'); if (scNote) scNote.oninput = (e) => { SC.note = e.target.value; };
  const sm = $('#sc-mode'); if (sm) sm.onchange = (e) => { SC.mode = e.target.value; SC.checks = null; renderScrapeSetup(); };
  note.querySelectorAll('select.sc-pass').forEach((sel) => { sel.onchange = (e) => { SC.pass = { ...(SC.pass || {}), [sel.dataset.code]: e.target.value }; SC.checks = null; renderScrapeSetup(); }; });
  const sf = $('#sc-frontier'); if (sf) sf.onchange = (e) => { SC.frontier = e.target.value; SC.checks = null; renderScrapeRun(); };
  const lim = $('#sc-limit'); if (lim) lim.onchange = (e) => { const n = parseInt(e.target.value, 10); SC.limit = n > 0 ? n : ''; SC.checks = null; renderScrapeRun(); };
  const cn = $('#sc-cn'); if (cn) cn.onchange = (e) => { SC.cnMode = e.target.value; SC.checks = null; renderScrapeSetup(); };
  $('#sc-dry').onchange = (e) => { SC.dryRun = e.target.checked; SC.checks = null; renderScrapeSetup(); };
  $('#sc-check').onclick = async () => {
    SC.checking = true; renderScrapeRun();     // the first Check asks the crawler about each link list, which takes a second
    try { const j = await api('/api/scrape/precheck', { method: 'POST', body: JSON.stringify(scrapeRequest()) }); SC.checks = j.checks; }
    catch (e) { SC.checks = [{ level: 'fail', text: e.message }]; }
    SC.checking = false; renderScrapeRun();
  };
  $('#scrape-start').onclick = startScrape;
}

async function startScrape() {
  $('#scrape-start').disabled = true;
  try {
    const r = await api('/api/scrape/start', { method: 'POST', body: JSON.stringify(scrapeRequest()) });
    const jobs = r.jobs || [r.job];
    // one panel per run, so an economy's result stays on the page while the next one runs
    $('#scrape-run-panel').innerHTML = jobs.map((j) => `<div id="scrape-run-panel-${j.id}"></div>`).join('');
    let left = jobs.length;
    jobs.forEach((j) => watchJob(j.id, `scrape-run-panel-${j.id}`, () => {
      loadScrapeOutputs();
      left -= 1;
      if (!left) {
        SC.checks = null; EX.loaded = false;
        // a refresh changes which link list is in use: the cards and the counts follow it
        SC.sources = {};
        api('/api/scrape/economies').then((x) => { SC.econs = x.economies; renderScrapeSetup(); renderScrapeSources(); }).catch(() => renderScrapeRun());
      }
    }));
    loadHealth();
  } catch (e) { alert(e.message); SC.checks = null; renderScrapeRun(); }
}

/* ---------- Scraping › China ---------- */
const CN = { loaded: false, data: null };

async function loadChina() {
  CN.loaded = true;
  try { CN.data = await api('/api/scrape/china'); } catch (e) { $('#cn-body').innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  renderChina();
}

function cnCaution(withLink) {
  return `<div class="callout cn-caution"><b>A personal note from the developer on China.</b>
    <ul>
      ${withLink ? '<li>Its national database forbids automated tools in its robots.txt, and several ministries refuse an automated client.</li>' : ''}
      <li><mark><b>One reason for the caution is my own personal concern:</b> as the developer I carry the risk of crawling where a host says no, so I treat those signals as limits, not obstacles to route around.</mark></li>
      ${withLink ? '<li>Collecting the main files by hand is quick: the national database comes as eleven archives, 945 documents, about five minutes.</li>' : ''}
      <li>Automation can follow wherever a host lifts its ban or grants access${withLink ? '; the China tools already read the publishers that permit us. See <a href="#" class="goto-cn">Scraping › China</a>.' : '.'}</li>
    </ul></div>`;
}

function renderChina() {
  const d = CN.data;
  if (!d.present) { $('#cn-body').innerHTML = '<p class="note">The crawler stage’s China material is not in this repository.</p>'; return; }
  const corpus = d.folders.find((f) => f.name.startsWith('CN_sources')) || {};
  const src = (name) => (corpus.sources || []).find((x) => x.source === name) || {};
  const cac = src('cac'), miit = src('miit'), npc = src('npc-database'), govcn = src('govcn'), customs = src('customs');
  const ws = d.folders.find((f) => f.name.startsWith('CN_ws')) || {};
  const docLink = (p, label) => `<a href="#" data-doc="${esc(p)}">${esc(label || p.split('/').pop())}</a>`;
  const inboxLink = () => '<a href="#" class="cn-inbox"><code>inbox/CN/Hand_collected</code></a>';   // one folder for every file fetched by hand

  $('#cn-body').innerHTML = `
    <div class="cn-lead">
      <div class="cn-lead-title">Why China is collected by hand</div>
      <ul class="plain-list big">
        <li><b>Forbids automated tools:</b> the national database, the central bank. <b>By hand.</b></li>
        <li><b>Refuses our client</b> (403, 412): MIIT, NDRC, Customs. <b>By hand.</b></li>
        <li><b>Permits us:</b> CAC, gov.cn. <b>Crawled</b>, one request every 6 to 12 seconds.</li>
      </ul>
    </div>

    ${cnCaution(false)}

    <div class="block">
      <h2>Layer 1: the national database</h2>
      <ul class="plain-list big">
        <li><b>Quick to get:</b> ${esc(npc.index_rows || 945)} documents in eleven archives, about five minutes by hand.</li>
        <li><b>Covers:</b> 18 of 61 indicators and all of pillar 7. Consolidated and current.</li>
        <li><b>Check:</b> download a fresh export into ${inboxLink()}, then run the offline diff.</li>
      </ul>
    </div>

    <div class="block">
      <h2>Layer 2: what the laws delegate to</h2>
      <ul class="plain-list big">
        <li><b>Why:</b> a law states the rule; the number sits in a catalogue published elsewhere.</li>
        <li><b>Set aside:</b> twelve more publishers, not deleted; 31 indicators are still served.</li>
        <li><b>Check:</b> run the update tool from 1 Scraping with China ticked (CAC, gov.cn). For MIIT and Customs, save the attachments into ${inboxLink()}.</li>
      </ul>
      <div class="table-wrap short"><table class="rows"><thead><tr><th>Source</th><th>Mode</th><th>Held</th><th>What</th></tr></thead><tbody>
        <tr><td>CAC 国家互联网信息办公室</td><td><span class="chip ok">crawled</span></td><td class="num">${cac.provenance_rows || ws.manifest_rows || ''}</td><td>Operative rules of pillars 6 and 7. Whole index: 42 of its 68 tier-2 rules were not on the hand list.</td></tr>
        <tr><td>MIIT 工业和信息化部</td><td><span class="chip warn">by hand</span></td><td class="num">${miit.provenance_rows || ''}</td><td>Telecom service catalogue, licensing, 2024 equity pilot, domain rules.</td></tr>
        <tr><td>Customs 海关总署</td><td><span class="chip warn">by hand</span></td><td class="num">${customs.provenance_rows || 0}</td><td>E-commerce thresholds, supervision modes and lists.</td></tr>
        <tr><td>gov.cn 中国政府网</td><td><span class="chip ok">crawled</span></td><td class="num">${govcn.provenance_rows || 6}</td><td>Permitted copies, including the third cross-border transfer route.</td></tr>
      </tbody></table></div>
    </div>

    <details class="block">
      <summary><h2>Sources to check by hand <span class="muted small">(${d.watchlist_total})</span> <span class="fold"></span></h2></summary>
      ${d.watchlist.map((g) => `<details class="wl"><summary>${esc(g.label)} <span class="muted small">(${g.rows.length})</span></summary>
        <div class="table-wrap short"><table class="rows"><thead><tr><th>Source</th><th>Why not automatic</th><th>What to look for</th><th>Indicators</th></tr></thead><tbody>
        ${g.rows.map((w) => `<tr><td><a href="${esc(w.url)}" target="_blank" rel="noopener">${esc(w.name)}</a></td><td class="small">${esc(String(w.why_not_automatic || '').replace(/\\*\\*/g, ''))}</td><td class="small">${esc(w.what_to_look_for)}</td><td class="small">${esc(w.indicators)}</td></tr>`).join('')}
        </tbody></table></div></details>`).join('')}
    </details>

    <details class="block">
      <summary><h2>What ships <span class="fold"></span></h2></summary>
      <div class="table-wrap short"><table class="rows"><thead><tr><th>Folder</th><th>Holds</th><th>Notes</th></tr></thead><tbody>
        ${d.folders.map((f) => `<tr><td class="small">${esc(f.name)}</td><td class="small">${f.manifest_rows ? `${f.manifest_rows} manifest rows` : ''}${f.provenance_rows ? `${f.manifest_rows ? ', ' : ''}${f.provenance_rows} provenance rows` : ''}${(f.sources || []).length ? (f.manifest_rows || f.provenance_rows ? '; ' : '') + f.sources.map((x) => `${x.source} ${x.provenance_rows || x.index_rows || 0}`).join(', ') : ''}</td><td class="small">${(f.notes || []).map((n) => docLink(n)).join(' · ')}</td></tr>`).join('')}
      </tbody></table></div>
      <p class="small muted">Manifests, provenance sheets and notes ship; the documents’ bytes do not. Click a note to read it here.</p>
      <pre class="doc" id="cn-doc-view" hidden></pre>
    </details>`;
  renderOutline('cn');
  $('#cn-body').querySelectorAll('a[data-doc]').forEach((a) => a.addEventListener('click', async (e) => {
    e.preventDefault();
    try { const t = await api(`/api/doc?path=${encodeURIComponent(a.dataset.doc)}`); const pre = $('#cn-doc-view'); pre.hidden = false; pre.textContent = t.text; pre.scrollIntoView({ behavior: 'smooth' }); }
    catch (err) { alert(err.message); }
  }));
  $('#cn-body').querySelectorAll('a.cn-inbox').forEach((a) => a.addEventListener('click', (e) => {
    e.preventDefault();
    if (typeof IB !== 'undefined') { IB.economy = 'CN'; IB.log = []; IB.filesOpen = null; }
    showTab('scrape');
    const block = $('#inbox-block');
    if (block) { block.open = true; try { localStorage.setItem('rdtii.inbox.open', '1'); } catch (err) { /* private window */ } }
    if (typeof loadInboxFiles === 'function' && IB.data) { loadInboxFiles().then(renderInbox); }
    setTimeout(() => { const b = $('#inbox-block'); if (b) b.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 250);
  }));
}

/* ---------- the full link list per economy, loaded on demand ---------- */
const DL = { cache: {}, scope: {}, q: {} };

async function loadDocList(code, src) {
  src = src || 'documents';
  const scope = DL.scope[`${code}:${src}`] || 'all';
  const key = `${code}:${src}:${scope}`;
  const host = document.querySelector(`details.doclist[data-code="${code}"][data-src="${src}"] .doclist-body`);
  if (!host) return;
  if (!DL.cache[key]) {
    host.innerHTML = '<p class="muted small">Loading…</p>';
    try { DL.cache[key] = await api(`/api/scrape/${src}?economy=${code}&scope=${scope}`); }
    catch (e) { host.innerHTML = `<p class="note">${esc(e.message)}</p>`; return; }
  }
  const d = DL.cache[key];
  const qkey = `${code}:${src}`;
  const q = (DL.q[qkey] || '').toLowerCase();
  const rows = q ? d.documents.filter((r) => `${r.law_name} ${r.law_number} ${r.kind} ${r.indicators} ${r.status}`.toLowerCase().includes(q)) : d.documents;
  const shown = rows.slice(0, 600);
  const scopes = d.scopes || [{ id: 'all', label: 'All' }, { id: 'relevant', label: 'Sample' }];
  host.innerHTML = `
    <div class="row doclist-bar">
      ${scopes.length > 1 ? scopes.map((sc) => `<label class="radio ${scope === sc.id ? 'on' : ''}"><input type="radio" name="dl-scope-${code}-${src}" value="${sc.id}" ${scope === sc.id ? 'checked' : ''}> ${esc(sc.label)} (${d.counts[sc.id] ?? '?'})</label>`).join('') : ''}
      <input type="search" class="dl-q" placeholder="filter by law, number, kind, status" value="${esc(DL.q[qkey] || '')}">
      <span class="muted small">${rows.length} of ${d.total}${shown.length < rows.length ? `, first ${shown.length} shown` : ''}</span>
    </div>
    <div class="table-wrap doclist-table"><table class="rows"><thead><tr><th>#</th><th>Law</th><th>Number</th><th>Kind</th><th>Status</th><th>Version</th><th>Indicators</th></tr></thead><tbody>
      ${shown.map((r) => `<tr><td class="num small">${esc(r.order)}</td><td>${r.url ? `<a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.law_name)}</a>` : esc(r.law_name)}</td><td class="small">${esc(r.law_number)}</td><td class="small">${esc(String(r.kind || '').replace(/_/g, ' '))}</td><td class="small">${esc(r.status)}</td><td class="small">${esc(r.version)}</td><td class="small">${esc(r.indicators)}</td></tr>`).join('')}
    </tbody></table></div>
    <div class="foot">${esc(d.file || '')}</div>`;
  host.querySelectorAll(`input[name="dl-scope-${code}-${src}"]`).forEach((inp) => inp.addEventListener('change', () => { DL.scope[qkey] = inp.value; loadDocList(code, src); }));
  let t; host.querySelector('.dl-q').oninput = (e) => { clearTimeout(t); t = setTimeout(() => { DL.q[qkey] = e.target.value; loadDocList(code, src); }, 200); };
}

function bindDocLists() {
  document.querySelectorAll('details.doclist[data-code]').forEach((det) => {
    if (det.dataset.bound) return;
    det.dataset.bound = '1';
    det.addEventListener('toggle', () => { if (det.open) loadDocList(det.dataset.code, det.dataset.src || 'documents'); });
  });
}

/* ---------- open a folder in the file manager of the machine running the server ---------- */
async function openFolder(path) {
  try { await api('/api/open', { method: 'POST', body: JSON.stringify({ path }) }); } catch (e) { alert(e.message); }
}
function bindOpen(rootSel) {
  document.querySelectorAll(`${rootSel} [data-open]`).forEach((b) => b.addEventListener('click', () => openFolder(b.dataset.open)));
}

/* ---------- the run layer: job strip, job panel, Clear ---------- */
const JOBS = { active: null, watching: {}, timers: {} };

function fmtWhen(t) { return t ? new Date(t * 1000).toLocaleTimeString() : ''; }
function fmtDur(a, b) { if (!a) return ''; const s = Math.max(0, Math.round((b || Date.now() / 1000) - a)); return s < 60 ? `${s} s` : `${Math.floor(s / 60)} min ${s % 60} s`; }

function renderJobStrip() {
  const j = S.health?.job;
  const el = $('#jobstrip');
  if (!el) return;
  if (!j || (!j.active && !(j.queued || []).length)) { el.hidden = true; el.innerHTML = ''; fixTop(); return; }
  el.hidden = false;
  const a = j.active;
  el.innerHTML = a
    ? `<span class="dot warn"></span><b>Running:</b> ${esc(a.title)} <span class="muted">· ${esc(a.step_label)}${a.progress?.total ? ` · ${a.progress.done}/${a.progress.total} ${esc(a.progress.unit || '')}` : ''}</span> <span class="muted small">${esc(a.last)}</span> <button class="btn small" data-cancel="${a.id}">Stop</button>${(j.queued || []).length ? `<span class="chip">${j.queued.length} queued</span>` : ''}${SHELL.kind === 'window' ? '<span class="muted small">Closing the window stops the run.</span>' : ''}`
    : `<span class="chip">${j.queued.length} job(s) queued</span>`;
  el.querySelector('[data-cancel]')?.addEventListener('click', () => cancelJob(a.id));
  fixTop();
}

async function cancelJob(id) {
  try { await api(`/api/jobs/${id}/cancel`, { method: 'POST' }); } catch (e) { alert(e.message); }
  loadHealth();
}

/* Poll one job into a container until it ends. onDone(job) fires once. */
function watchJob(jobId, containerId, onDone) {
  clearInterval(JOBS.timers[containerId]);
  let since = 0, all = [];
  const tick = async () => {
    let j;
    try { j = await api(`/api/jobs/${jobId}?since=${since}`); } catch (e) { $(`#${containerId}`).innerHTML = `<div class="note">${esc(e.message)}</div>`; clearInterval(JOBS.timers[containerId]); return; }
    all = all.concat(j.sentences); since = j.n_sentences;
    renderJobPanel(containerId, j, all);
    if (!['queued', 'running'].includes(j.status)) { clearInterval(JOBS.timers[containerId]); loadHealth(); if (onDone) onDone(j); }
  };
  tick();
  JOBS.timers[containerId] = setInterval(tick, 1500);
}

function renderJobPanel(containerId, j, sentences) {
  const p = j.progress || {};
  const pct = p.total ? Math.min(100, Math.round(100 * (p.done || 0) / p.total)) : null;
  const statusChip = { queued: 'chip', running: 'chip warn', done: 'chip ok', failed: 'chip bad', cancelled: 'chip' }[j.status] || 'chip';
  const steps = (j.steps || []).map((s, i) => `<li class="${i < j.step_index ? 'past' : i === j.step_index ? 'now' : ''}">${esc(s)}</li>`).join('');
  $(`#${containerId}`).innerHTML = `<div class="job">
    <div class="row"><span class="${statusChip}">${esc(j.status)}</span> <b>${esc(j.title)}</b>
      <span class="muted small">started ${fmtWhen(j.started)}${j.started ? `, ${fmtDur(j.started, j.ended)}` : ''}</span>
      ${['queued', 'running'].includes(j.status) ? `<button class="btn small" data-cancel="${j.id}">Stop</button>` : `<button class="btn small" data-dismiss="${j.id}" title="Hide this finished run; its folder stays in Output">Dismiss</button>`}
      ${p.cost_usd != null ? `<span class="chip">$${Number(p.cost_usd).toFixed(2)} so far</span>` : ''}</div>
    ${pct != null ? `<div class="bar"><div style="width:${pct}%"></div></div><div class="muted small">${p.done} of ${p.total} ${esc(p.unit || '')}${p.failed ? `, ${p.failed} failed` : ''}${p.skipped ? `, ${p.skipped} skipped` : ''}</div>` : ''}
    <ol class="steps">${steps}</ol>
    <ul class="said">${sentences.slice(-40).map((s) => `<li><span class="muted small">${fmtWhen(s.t)}</span> ${esc(s.text)}</li>`).join('')}</ul>
    ${j.env_public && Object.keys(j.env_public).length ? `<details><summary class="small">Settings this run received</summary><div class="foot">${Object.entries(j.env_public).map(([k, v]) => `${esc(k)}=${esc(v)}`).join('  ')}</div></details>` : ''}
    <details><summary class="small">Raw output (last ${(j.raw_tail || []).length} lines)</summary><pre class="doc small">${esc((j.raw_tail || []).join('\n'))}</pre></details>
  </div>`;
  $(`#${containerId}`).querySelector('[data-cancel]')?.addEventListener('click', () => cancelJob(j.id));
  $(`#${containerId}`).querySelector('[data-dismiss]')?.addEventListener('click', () => dismissJob(j.id, containerId));
}

/* A finished run's panel can be hidden; the server still remembers the job, the page just stops showing it. */
function dismissedJobs() {
  try { return new Set(JSON.parse(localStorage.getItem('rdtii.dismissed') || '[]')); } catch (e) { return new Set(); }
}
function dismissJob(jobId, containerId) {
  const d = dismissedJobs(); d.add(jobId);
  try { localStorage.setItem('rdtii.dismissed', JSON.stringify([...d].slice(-200))); } catch (e) { /* private window */ }
  clearInterval(JOBS.timers[containerId]);
  const el = $(`#${containerId}`); if (el) el.innerHTML = '';
}

/* Clear: preview, confirm in the browser, then confirm on the server with the one-minute token. */
async function clearPath(path, what) {
  let pv;
  try { pv = await api('/api/clear/preview', { method: 'POST', body: JSON.stringify({ path }) }); }
  catch (e) { alert(`Cannot clear: ${e.message}`); return false; }
  const ok = confirm(`Remove ${what}?\n\n${pv.path}\n${pv.files} files, ${fmtBytes(pv.bytes)}.\n\nThis cannot be undone.`);
  if (!ok) return false;
  try { const r = await api('/api/clear/confirm', { method: 'POST', body: JSON.stringify({ token: pv.token }) }); alert(`Removed ${r.files} files (${fmtBytes(r.bytes)}) from ${r.removed}`); return true; }
  catch (e) { alert(`Not cleared: ${e.message}`); return false; }
}

/* On page load, show the newest job of each stage in its Run block (finished jobs render once). */
async function restoreJobPanels() {
  let j;
  try { j = await api('/api/jobs'); } catch (e) { return; }
  const newest = {};
  const hidden = dismissedJobs();
  (j.jobs || []).forEach((x) => { if (!newest[x.stage] && !hidden.has(x.id)) newest[x.stage] = x; });
  const panels = { p2: 'extract-run-panel', p3: 'map-run-panel', selftest: 'selftest-panel' };
  Object.entries(panels).forEach(([stage, id]) => { if (newest[stage] && $(`#${id}`)) watchJob(newest[stage].id, id); });
  // a crawl is one run per economy: show the ones still going and the last few finished, oldest first, each in its own panel
  const crawls = (j.jobs || []).filter((x) => x.stage === 'p1' && !hidden.has(x.id)).slice(0, 6).reverse();
  if (crawls.length && $('#scrape-run-panel')) {
    $('#scrape-run-panel').innerHTML = crawls.map((x) => `<div id="scrape-run-panel-${x.id}"></div>`).join('');
    crawls.forEach((x) => watchJob(x.id, `scrape-run-panel-${x.id}`, () => loadScrapeOutputs()));
  }
}

/* Self-test button on the Appendix tab. */
async function runSelftest() {
  try { const r = await api('/api/jobs/selftest', { method: 'POST' }); watchJob(r.job.id, 'selftest-panel'); loadHealth(); }
  catch (e) { alert(e.message); }
}

/* ---------- the shell: a browser tab, or the tool's own window ---------- */
const SHELL = { kind: (document.querySelector('meta[name=rdtii-shell]') || {}).content === 'window' ? 'window' : 'tab', busy: false, misses: 0, stream: null };

function shellNotice(text) {
  let el = $('#shell-overlay');
  if (!text) { if (el) el.remove(); return; }
  if (!el) { el = document.createElement('div'); el.id = 'shell-overlay'; document.body.appendChild(el); }
  el.innerHTML = `<div class="box"><h2>The interface has stopped</h2><p>${esc(text)}</p><button class="btn primary" id="shell-reload">Reload</button></div>`;
  $('#shell-reload').onclick = () => location.reload();
}

/* One stream per open page. The server counts them to know a window is still there; the page reads from it
   whether a run is in progress, and learns from its silence that the server has gone. */
function shellConnect() {
  if (!window.EventSource) return;
  const es = new EventSource(`/api/presence?t=${encodeURIComponent(TOKEN)}`);
  SHELL.stream = es;
  es.onmessage = (e) => {
    SHELL.misses = 0;
    shellNotice('');
    try { SHELL.busy = !!JSON.parse(e.data).busy; } catch (err) { /* a line that is not ours */ }
  };
  es.onerror = async () => {
    SHELL.misses += 1;
    if (es.readyState !== EventSource.CLOSED) {      // the browser is retrying by itself
      if (SHELL.misses >= 3) shellNotice(SHELL.kind === 'window' ? 'Close this window and start RDTII Rocky again.' : 'Start it again (python interface/app.py), then reload this page.');
      return;
    }
    // refused, not unreachable: a server is there but it is a new one, and this page holds the old one's token
    es.close();
    let up = false;
    try { up = (await fetch('/api/ping', { cache: 'no-store' })).ok; } catch (err) { up = false; }
    shellNotice(up ? 'It was started again since this page was opened. Reload to continue.' : (SHELL.kind === 'window' ? 'Close this window and start RDTII Rocky again.' : 'Start it again (python interface/app.py), then reload this page.'));
    if (!up) setTimeout(shellConnect, 3000);
  };
}

/* Closing the window stops the interface, and a run with it: ask first. A tab can be closed freely, the server stays. */
window.addEventListener('beforeunload', (e) => {
  if (SHELL.kind === 'window' && SHELL.busy) { e.preventDefault(); e.returnValue = 'A run is in progress. Closing the window stops it.'; }
});

/* In the window, a link to a source opens in the person's own browser, not inside the tool. */
document.addEventListener('click', (e) => {
  if (SHELL.kind !== 'window' || !e.target.closest) return;
  const a = e.target.closest('a[href]');
  if (!a || !/^https?:/i.test(a.getAttribute('href') || '')) return;
  if (new URL(a.href, location.href).origin === location.origin) return;
  e.preventDefault();
  api('/api/open-url', { method: 'POST', body: JSON.stringify({ url: a.href }) }).catch((err) => alert(err.message));
});

/* ---------- boot ---------- */
(async function boot() {
  shellConnect();
  await loadHealth();
  showTab('overview');   // every visit lands on the Overview
  bindOverview();
  renderCost();
  loadPicker();
  loadMapHandoffs();
  await loadRuns();
  restoreJobPanels();
  setInterval(() => { if (S.health?.job?.active) loadHealth(); }, 4000);
  setInterval(loadHealth, 20000);
})();

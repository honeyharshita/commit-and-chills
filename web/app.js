const $ = (selector) => document.querySelector(selector);
const runButton = $('#runButton');
const errorBox = $('#error');

function number(value) { return new Intl.NumberFormat('en-IN').format(value); }
function actionClass(action) { return action.toLowerCase().replace(' ', '-'); }

function drawChart(results) {
  const svg = $('#chart');
  const empty = $('#chartEmpty');
  svg.innerHTML = '';
  if (!results || !results.local.windows.length) { empty.hidden = false; return; }
  empty.hidden = true;
  const width = 760, height = 260, pad = { left: 38, right: 14, top: 14, bottom: 28 };
  const all = [...results.none.windows, ...results.local.windows];
  const max = Math.max(100, ...all.map(point => point.auto_correct_pct));
  const x = (index) => pad.left + index * ((width - pad.left - pad.right) / Math.max(1, results.local.windows.length - 1));
  const y = (value) => height - pad.bottom - (value / max) * (height - pad.top - pad.bottom);
  [0, 50, 100].forEach((tick) => {
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
    line.setAttribute('x1', pad.left); line.setAttribute('x2', width - pad.right);
    line.setAttribute('y1', y(tick)); line.setAttribute('y2', y(tick)); line.setAttribute('class', 'grid-line'); svg.appendChild(line);
    const label = document.createElementNS('http://www.w3.org/2000/svg', 'text');
    label.setAttribute('x', 0); label.setAttribute('y', y(tick) + 4); label.setAttribute('class', 'axis-label'); label.textContent = `${tick}%`; svg.appendChild(label);
  });
  [['local', '#18714d'], ['none', '#e9874d']].forEach(([name, color]) => {
    const points = results[name].windows.map((point, index) => `${x(index)},${y(point.auto_correct_pct)}`).join(' ');
    const polyline = document.createElementNS('http://www.w3.org/2000/svg', 'polyline');
    polyline.setAttribute('points', points); polyline.setAttribute('fill', 'none'); polyline.setAttribute('stroke', color); polyline.setAttribute('stroke-width', '3'); polyline.setAttribute('stroke-linecap', 'round'); polyline.setAttribute('stroke-linejoin', 'round'); svg.appendChild(polyline);
    results[name].windows.forEach((point, index) => { const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle'); circle.setAttribute('cx', x(index)); circle.setAttribute('cy', y(point.auto_correct_pct)); circle.setAttribute('r', '4'); circle.setAttribute('fill', color); svg.appendChild(circle); });
  });
  svg.querySelectorAll('.grid-line').forEach((line) => { line.setAttribute('stroke', '#e7ede8'); line.setAttribute('stroke-width', '1'); });
  svg.querySelectorAll('.axis-label').forEach((label) => { label.setAttribute('fill', '#9ba9a3'); label.setAttribute('font-size', '10'); label.setAttribute('font-family', 'DM Mono'); });
}

function updateTable(rows) {
  $('#rows').innerHTML = rows.map(row => `<tr><td class="vendor">${row.i + 1}</td><td>${row.vendor}</td><td>${row.exc}</td><td><span class="action ${actionClass(row.agent)}">${row.agent}</span></td><td>${row.truth}</td><td class="evidence">${row.auto_correct ? 'Cited precedent' : row.agent === 'ESCALATE' ? 'Human review' : 'Corrected'}</td></tr>`).join('');
}

function render(data) {
  const none = data.results.none;
  const local = data.results.local;
  const lift = local.total_auto_correct - none.total_auto_correct;
  $('#lift').textContent = `${lift >= 0 ? '+' : ''}${number(lift)}`;
  $('#localCorrect').textContent = `${number(local.total_auto_correct)} / ${number(data.n)}`;
  $('#wrong').textContent = number(local.total_auto_wrong);
  $('#breaches').textContent = number(local.policy_breaches);
  $('#streamMeta').textContent = `${number(data.n)} invoices / seed ${data.seed} / offline test double`;
  drawChart(data.results); updateTable(local.rows);
}

async function runEvaluation() {
  runButton.disabled = true; runButton.querySelector('span').textContent = 'Running...'; errorBox.hidden = true;
  try {
    const response = await fetch('/api/eval', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ n: Number($('#invoiceCount').value), seed: Number($('#seed').value) }) });
    const data = await response.json(); if (!response.ok) throw new Error(data.detail || 'Evaluation failed'); render(data);
  } catch (error) { errorBox.textContent = error.message; errorBox.hidden = false; }
  finally { runButton.disabled = false; runButton.querySelector('span').textContent = 'Run evaluation'; }
}

async function checkHealth() {
  try { const response = await fetch('/api/health'); if (!response.ok) throw new Error(); $('#healthText').textContent = 'Backend connected'; $('.status-pill').classList.add('ready'); }
  catch { $('#healthText').textContent = 'Backend unavailable'; }
}
runButton.addEventListener('click', runEvaluation); checkHealth(); runEvaluation();

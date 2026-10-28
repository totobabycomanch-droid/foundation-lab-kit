const $ = (id) => document.getElementById(id);
let busy = false;
let observations = [];

function text(tag, value, parent) {
  const element = document.createElement(tag);
  element.textContent = value;
  parent.append(element);
  return element;
}

function show(result) {
  $('request').textContent = `요청 ${result.request_id} · HTTP ${result.status_code} · ${result.outcome} · ${result.detail}`;
  $('status').textContent = result.detail;
  $('error').textContent = result.status_code >= 400 ? result.detail : '';
  const snapshot = result.snapshot;
  $('history').querySelector('tbody').replaceChildren();
  if (snapshot) {
    $('observed').textContent = `품목 ${result.product_code} · 요청 ${result.request_id}의 별도 DB 연결 재조회`;
    $('current').textContent = snapshot.current?.quantity ?? '—';
    $('total').textContent = snapshot.history_quantity;
    $('match').textContent = snapshot.current?.quantity === snapshot.history_quantity ? '일치' : '불일치';
    $('empty').hidden = snapshot.history.length > 0;
    for (const row of snapshot.history) {
      const tr = document.createElement('tr');
      for (const key of ['seq', 'product_code', 'change_qty', 'reason']) text('td', row[key], tr);
      $('history').querySelector('tbody').append(tr);
    }
  } else {
    $('observed').textContent = '이 요청은 저장 전에 거부됐습니다. 상태 다시 조회로 DB 값을 확인하세요.';
    for (const id of ['current', 'total', 'match']) $(id).textContent = '—';
    $('empty').hidden = false;
  }
  $('trace').replaceChildren();
  if (!result.trace.length) text('p', '이 요청에서 실행한 SQL이 없습니다.', $('trace'));
  for (const step of result.trace) {
    const card = document.createElement('article'); card.className = 'sql-step';
    text('h3', `${step.step}. ${step.phase}${step.error ? ' · 오류 ' + step.error : ''}`, card);
    text('p', '호출한 구문과 전달값', card);
    text('pre', `${step.sql}\n전달값: ${JSON.stringify(step.parameters)}`, card);
    text('p', 'SQLite가 실제 실행한 SQL', card);
    text('pre', step.executed_sql.join('\n') || '실행 전 오류로 실행 콜백이 없습니다.', card);
    if (step.rows.length) text('pre', JSON.stringify(step.rows, null, 2), card);
    if (step.affected_rows !== null) text('p', `영향받은 행: ${step.affected_rows}`, card);
    $('trace').append(card);
  }
}

async function send(path, method = 'GET', body, keep = false) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button,input,select').forEach(e => { e.disabled = true; });
  $('movement-form').setAttribute('aria-busy', 'true');
  $('error').textContent = ''; $('copy-status').textContent = '';
  $('request').textContent = '요청 처리 중입니다.'; $('trace').replaceChildren();
  try {
    const response = await fetch(path, {method, cache: 'no-store',
      ...(body ? {headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)} : {})});
    const result = await response.json();
    if (result.status_code !== response.status || !Array.isArray(result.trace)) throw new Error('Unexpected response');
    show(result);
    if (path.startsWith('/api/reset')) observations = [];
    if (keep) observations.push({input: body ?? {product_code: $('product').value}, response: result});
    $('report').value = JSON.stringify(observations, null, 2);
  } catch {
    $('error').textContent = '서버 연결을 확인한 뒤 상태 다시 조회를 누르세요. 결과를 확인하기 전에는 같은 입출고를 다시 보내지 마세요.';
    $('request').textContent = '요청 결과 미확인'; $('trace').replaceChildren();
    $('observed').textContent = '현재 DB 상태를 확인하지 못했습니다.';
    for (const id of ['current', 'total', 'match']) $(id).textContent = '—';
    $('history').querySelector('tbody').replaceChildren(); $('empty').hidden = false;
  } finally {
    busy = false;
    document.querySelectorAll('button,input,select').forEach(e => { e.disabled = false; });
    $('movement-form').setAttribute('aria-busy', 'false');
  }
}

$('movement-form').addEventListener('submit', event => {
  event.preventDefault();
  if (!$('movement-form').reportValidity()) return;
  send('/api/movements', 'POST', {product_code: $('product').value, direction: $('direction').value,
    quantity: Number($('quantity').value)}, true);
});
$('movement-form').addEventListener('invalid', () => {
  $('status').textContent = '입력값을 확인하세요. 이 입력은 서버에 보내지 않았습니다.';
  $('request').textContent = '입력 단계에서 중단 · 서버 요청 없음';
  $('trace').replaceChildren();
  text('p', '이 입력으로 실행한 SQL이 없습니다.', $('trace'));
}, true);
const refresh = () => send(`/api/state?product_code=${encodeURIComponent($('product').value)}`, 'GET', null, true);
$('refresh').addEventListener('click', refresh);
$('product').addEventListener('change', refresh);
$('reset').addEventListener('click', () => send(`/api/reset?product_code=${encodeURIComponent($('product').value)}`, 'POST', null, true));
$('copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText($('report').value); $('copy-status').textContent = '실제 실행 결과를 복사했습니다.'; }
  catch { $('report-details').open = true; $('report').focus(); $('report').select(); $('copy-status').textContent = '아래 결과를 Ctrl+C로 복사하세요.'; }
});
refresh();

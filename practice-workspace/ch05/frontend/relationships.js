const $ = id => document.getElementById(id);
let busy = false;
let observations = [];
function text(tag, value, parent) {
  const el = document.createElement(tag); el.textContent = value; parent.append(el); return el;
}
function option(parent, label, value = '') {
  const el = text('option', label, parent); el.value = value; return el;
}
function show(result) {
  $('request').textContent = `요청 ${result.request_id} · HTTP ${result.status_code} · ${result.outcome} · ${result.detail}`;
  $('status').textContent = result.detail;
  $('error').textContent = result.status_code >= 400 ? result.detail : '';
  for (const id of ['products', 'target', 'selection', 'trades', 'trace']) $(id).replaceChildren();
  const s = result.snapshot;
  $('product-empty').textContent = s ? (s.products.length ? '' : '아직 준비한 상품이 없습니다.') : 'DB 상태를 확인하지 못했습니다.';
  $('read-issue').textContent = s?.read_issue ?? '';
  if (s) {
    for (const p of s.products) {
      option($('target'), `${p.code} · ${p.name}`, p.code);
      const tr = text('tr', '', $('products'));
      for (const val of [p.code, p.name, p.is_deleted ? '취급 중단' : '취급 중']) text('td', val, tr);
    }
    if (!s.products.length) option($('target'), '준비한 상품 없음');
    if (s.read_ready) {
      for (const p of s.selection) option($('selection'), `${p.code} · ${p.name}`, p.code);
      if (!s.selection.length) option($('selection'), '선택할 상품 없음');
      $('selection-count').textContent = `선택 목록 ${s.selection.length}건`;
      $('trade-empty').textContent = s.trades.length ? '' : '조회된 거래가 없습니다.';
      for (const t of s.trades) {
        const tr = text('tr', '', $('trades'));
        for (const val of [t.trade_no, t.code, t.name, t.quantity, t.is_deleted ? '취급 중단' : '취급 중']) text('td', val, tr);
      }
    } else {
      option($('selection'), '조회 코드 구현 후 확인');
      $('selection-count').textContent = '선택 목록 미확인';
      $('trade-empty').textContent = `DB에 저장된 거래 ${s.raw_trades.length}건 · 상품 연결 조회는 아직 미구현입니다.`;
    }
  } else {
    option($('target'), '상태 미확인'); option($('selection'), '상태 미확인');
    $('selection-count').textContent = '목록 미확인'; $('trade-empty').textContent = '거래 미확인';
  }
  for (const step of result.trace) {
    const card = text('article', '', $('trace')); card.className = 'sql-step';
    text('h3', `${step.step}. ${step.phase}${step.error ? ' · 오류 ' + step.error : ''}`, card);
    text('p', '호출한 구문과 전달값', card);
    text('pre', `${step.sql}\n전달값: ${JSON.stringify(step.parameters)}`, card);
    text('p', 'SQLite가 실제 실행한 SQL', card);
    text('pre', step.executed_sql.join('\n') || '실행 콜백 없음', card);
    if (step.error) text('pre', `${step.error_detail ?? step.error}\nSQLite 오류: ${step.sqlite_errorname ?? '없음'} (${step.sqlite_errorcode ?? '없음'})`, card);
    if (step.rows.length) text('pre', JSON.stringify(step.rows, null, 2), card);
    if (step.affected_rows !== null) text('p', `영향받은 행: ${step.affected_rows}`, card);
  }
  if (!result.trace.length) text('p', '이 요청에서 실행한 SQL이 없습니다.', $('trace'));
}
async function send(action, body) {
  if (busy) return;
  busy = true; $('error').textContent = ''; $('copy-status').textContent = '';
  document.querySelectorAll('button,input,select').forEach(e => { e.disabled = true; });
  $('prepare-form').setAttribute('aria-busy', 'true');
  $('request').textContent = '요청 처리 중입니다.'; $('trace').replaceChildren();
  try {
    const response = await fetch(`/api/relationships/${action}`, {method: action === 'state' ? 'GET' : 'POST', cache: 'no-store',
      ...(body ? {headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)} : {})});
    const result = await response.json();
    if (result.status_code !== response.status || !Array.isArray(result.trace)) throw new Error('Unexpected response');
    show(result);
    if (action === 'reset' && response.ok) observations = [];
    observations.push({action, input: body ?? {}, response: result});
    $('report').value = JSON.stringify(observations, null, 2);
  } catch {
    show({request_id: '미확인', status_code: 0, outcome: '미확인', detail: '서버 연결을 확인하고 예전 거래 다시 조회를 누르세요. 상태 확인 전 같은 작업을 다시 보내지 마세요.', snapshot: null, trace: []});
  } finally {
    busy = false;
    document.querySelectorAll('button,input,select').forEach(e => { e.disabled = false; });
    $('prepare-form').setAttribute('aria-busy', 'false');
    $('selection').disabled = !$('selection').value;
  }
}
$('prepare-form').addEventListener('submit', event => {
  event.preventDefault(); if (!$('prepare-form').reportValidity()) return;
  send('prepare', {code: $('code').value, name: $('name').value, quantity: Number($('quantity').value)});
});
$('prepare-form').addEventListener('invalid', () => {
  $('request').textContent = '입력 단계에서 중단 · 서버 요청 없음'; $('trace').replaceChildren();
  text('p', '이 입력으로 실행한 SQL이 없습니다.', $('trace'));
}, true);
for (const action of ['delete', 'discontinue']) $(action).addEventListener('click', () => {
  if (!$('target').value) { $('error').textContent = '먼저 상품과 거래를 준비하세요.'; return; }
  send(action, {code: $('target').value});
});
$('refresh').addEventListener('click', () => send('state'));
$('reset').addEventListener('click', () => send('reset'));
$('copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText($('report').value); $('copy-status').textContent = '실제 실행 결과를 복사했습니다.'; }
  catch { $('report-details').open = true; $('report').focus(); $('report').select(); $('copy-status').textContent = '아래 결과를 Ctrl+C로 복사하세요.'; }
});
send('state');

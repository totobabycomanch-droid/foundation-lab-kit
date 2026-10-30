'use strict';
const $ = id => document.getElementById(id);
let session = sessionStorage.getItem('ch09-session');
let busy = false;
const observations = [];
function current(data) { $('current').textContent = `주문 ${data.order_id} · ${data.state ?? data.after}`; }
function remember(action, input, response) {
  observations.push({action, input, response});
  $('report').value = JSON.stringify(observations, null, 2);
}
function showAction(data) {
  const row = document.createElement('tr');
  for (const value of [data.order_id, data.before, data.action, `HTTP ${data.status_code} · ${data.exception || '성공'}`, data.after]) {
    const cell = document.createElement('td'); cell.textContent = value; row.append(cell);
  }
  $('history').append(row);
  $('result').textContent = JSON.stringify(data, null, 2);
  current(data);
}
async function send(kind, action) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button').forEach(button => button.disabled = true);
  $('error').textContent = ''; $('copy-status').textContent = ''; $('message').textContent = '요청 처리 중입니다.';
  const input = kind === 'new' ? {} : {session, ...(action ? {action} : {})};
  try {
    const response = await fetch(kind === 'state' ? '/api/state?session=' + encodeURIComponent(session || '') : '/api/' + kind, kind === 'state' ? {cache:'no-store'} : {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(input), cache:'no-store'});
    const data = await response.json();
    remember(kind, input, {...data, http_status:response.status});
    if (data.session) { session = data.session; sessionStorage.setItem('ch09-session', session); }
    if (kind === 'action' && Object.hasOwn(data, 'after')) showAction(data);
    else if (response.ok) { current(data); $('result').textContent = JSON.stringify(data, null, 2); }
    if (kind === 'new' && response.ok) $('result').textContent = '새 주문을 만들었습니다. 행동을 선택하세요.';
    $('message').textContent = `HTTP ${response.status} · ${data.detail || '실제 상태를 조회했습니다.'}`;
    if (!response.ok) $('error').textContent = data.detail;
    if (response.status === 404) $('current').textContent = '이전 주문을 찾을 수 없습니다. 새 주문을 만드세요.';
  } catch {
    $('message').textContent = '결과 미확인'; $('error').textContent = '서버 연결을 확인한 뒤 현재 상태 다시 조회를 누르세요. 이전 표시값으로 성공을 판단하지 마세요.';
    $('result').textContent = '이번 요청의 결과를 받지 못했습니다.';
    remember(kind, input, {outcome:'미확인', detail:'서버 응답을 받지 못했습니다.'});
  } finally { busy = false; document.querySelectorAll('button').forEach(button => button.disabled = false); }
}
$('new').addEventListener('click', () => send('new'));
$('refresh').addEventListener('click', () => send('state'));
document.querySelectorAll('[data-action]').forEach(button => button.addEventListener('click', () => send('action', button.dataset.action)));
$('copy').addEventListener('click', async () => {
  try { await navigator.clipboard.writeText($('report').value); $('copy-status').textContent = '실제 실행 결과를 복사했습니다.'; }
  catch { $('report-details').open = true; $('report').focus(); $('report').select(); $('copy-status').textContent = '아래 결과를 Ctrl+C로 복사하세요.'; }
});
if (session) send('state');

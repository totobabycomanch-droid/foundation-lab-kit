'use strict';
const $ = (id) => document.getElementById(id);
let history = [];
let busy = false;
const format = (value) => JSON.stringify(value, null, 2);

function setBusy(value) {
  busy = value;
  for (const control of $('order-form').elements) control.disabled = value;
  if (!value) $('request-price').disabled = !$('include-price').checked;
  $('copy').disabled = value || history.length === 0;
  $('order-form').setAttribute('aria-busy', String(value));
}

function clearResult() {
  $('summary').replaceChildren();
  $('summary').hidden = true;
  $('details').open = false;
  $('evidence').textContent = '실행 뒤 실제 호출 순서와 결과가 표시됩니다.';
  $('copy-status').textContent = '';
  $('copy-fallback').hidden = true;
  $('copy-text').value = '';
}

function numberValue(id) {
  // valueAsNumber는 소수를 보존한다. 빈 값은 null로 전달해 업무 함수가 판단한다.
  const value = $(id).valueAsNumber;
  return Number.isFinite(value) ? value : null;
}

function metric(label, value) {
  const card = document.createElement('div');
  const title = document.createElement('strong');
  const content = document.createElement('span');
  title.textContent = label;
  content.textContent = String(value);
  card.append(title, content);
  $('summary').append(card);
}

$('include-price').addEventListener('change', () => {
  $('request-price').disabled = !$('include-price').checked;
});
$('order-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  if (busy) return;
  const payload = {prod_code: $('product').value, qty: numberValue('quantity')};
  if ($('include-price').checked) payload.unit_price = numberValue('request-price');
  const input = {payload, server_unit_price: numberValue('server-price'), is_vat: $('vat').value};
  clearResult();
  setBusy(true);
  $('status').textContent = 'Python 함수를 실행하고 있습니다.';
  try {
    const response = await fetch('/api/calculate', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(input),
    });
    const result = await response.json();
    history.push({sent: input, http_status: response.status, observed: result});
    $('status').textContent = `HTTP ${response.status} · ${result.detail}`;
    $('evidence').textContent = format(result);
    metric('계산 실행', result.calculation_status ?? '미확인');
    // 오류의 반환값은 상세에 남긴다. 이전 성공 금액을 오류 화면에 재사용하지 않는다.
    if (response.ok && result.amounts) {
      metric('공급가액(원)', result.amounts.supply_amount);
      metric('VAT(원)', result.amounts.vat_amount);
      metric('합계(원)', result.amounts.total_amount);
    }
    $('summary').hidden = false;
    if (!response.ok) $('details').open = true;
  } catch (error) {
    $('status').textContent = '연결 실패: 실행 터미널과 포트를 확인한 뒤 다시 실행하세요.';
    $('evidence').textContent = String(error);
    history.push({sent: input, connection_error: String(error)});
  } finally {
    setBusy(false);
  }
});
$('reset-lab').addEventListener('click', () => {
  if (busy) return;
  $('order-form').reset();
  history = [];
  clearResult();
  setBusy(false);
  $('status').textContent = '기본 입력으로 돌아왔습니다. 관찰 내역을 비웠습니다.';
});
$('copy').addEventListener('click', async () => {
  const text = format({scope: 'Chapter 8 로컬 함수 관찰. 실제 ERP API·DB 검증 아님.', observations: history});
  try {
    await navigator.clipboard.writeText(text);
    $('copy-status').textContent = '실제 실행 내역을 복사했습니다.';
  } catch {
    $('copy-fallback').hidden = false;
    $('copy-text').value = text;
    $('copy-text').focus();
    $('copy-text').select();
    $('copy-status').textContent = '아래 내용을 Ctrl+C로 복사하세요.';
  }
});

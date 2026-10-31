'use strict';
const $=id=>document.getElementById(id);
const names={orders:'주문',order_items:'주문 상세',stock_ledger:'재고 원장',order_events:'이벤트',order_state_history:'초기 상태 이력'};
const COMPANY='11111111-1111-1111-1111-111111111111';
const RAMEN='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa', COLA='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';
let busy=false, records=[];
function cell(row,value){const el=document.createElement('td');el.textContent=value??'—';row.append(el);}
function show(s){
  if(!s) return;
  $('source').textContent=s.source;
  $('current-price').textContent=s.current_price??'미조회';
  $('counts').textContent=Object.entries(s.counts).map(([k,v])=>`${names[k]} ${v}건`).join(' · ');
  $('stock').replaceChildren();for(const p of s.stock){const tr=document.createElement('tr');cell(tr,p.name);cell(tr,p.quantity);$('stock').append(tr);}
  $('orders').replaceChildren();for(const o of s.orders){const tr=document.createElement('tr');for(const key of ['order_id','status','name','quantity','price'])cell(tr,o[key]);$('orders').append(tr);}
  if(!s.orders.length){const tr=document.createElement('tr');cell(tr,'아직 주문이 없습니다.');$('orders').append(tr);}
}
function compare(o){
  if(!o.after){$('comparison').textContent='저장 후 조회 미확인. 결과를 다시 조회하세요.';return;}
  const lines=Object.entries(o.before.counts).map(([k,v])=>`${names[k]} ${v} → ${o.after.counts[k]}`);
  for(const p of o.before.stock){const after=o.after.stock.find(r=>r.product_id===p.product_id);lines.push(`${p.name} 재고 ${p.quantity} → ${after?.quantity??'미확인'}`);}
  $('comparison').textContent=lines.join(' / ');
}
async function run(label,path,options={}){
  if(busy)return;busy=true;$('work').setAttribute('aria-busy','true');document.querySelectorAll('button,input').forEach(e=>e.disabled=true);
  $('status').textContent=`${label} 진행 중`;$('error').textContent='';
  if(path==='/orders'){$('trace').textContent='이번 요청의 결과를 기다립니다.';$('comparison').textContent='이번 주문의 전후 값을 조회합니다.';}
  try{
    const r=await fetch(path,{...options,cache:'no-store'});const body=await r.json();
    $('status').textContent=`${label} · HTTP ${r.status}`;
    if(!r.ok)$('error').textContent=typeof body.detail==='string'?body.detail:'입력값을 확인하세요.';
    const o=body.observation;if(o){compare(o);show(o.after);$('trace').textContent=JSON.stringify(o.trace,null,2);if(!o.after)$('source').textContent='미확인 · 아래 표는 이전 조회값입니다.';}
    else if(body.after)show(body.after);else if(body.counts)show(body);
    else if(!r.ok)$('source').textContent='이번 결과 미확인 · 아래 표는 이전 조회값입니다.';
    records.push({action:label,http_status:r.status,...body});$('report').value=JSON.stringify(records,null,2);
  }catch{
    $('status').textContent=`${label} · 결과 미확인`;$('error').textContent='서버 연결과 DB 결과를 확인하세요. 주문은 자동 재전송하지 않습니다.';
    $('source').textContent='현재 표는 이전 조회값입니다.';$('comparison').textContent='이번 실행 결과 미확인';
    records.push({action:label,result:'Not Run: 통신 결과 미확인'});$('report').value=JSON.stringify(records,null,2);
  }finally{busy=false;$('work').setAttribute('aria-busy','false');document.querySelectorAll('button,input').forEach(e=>e.disabled=false);}
}
function post(label,path,body,headers={}){return run(label,path,{method:'POST',headers:{'Content-Type':'application/json',...headers},body:JSON.stringify(body)});}
function order(fail=false){
  if(!$('order-form').reportValidity())return;
  const items=[{product_id:RAMEN,quantity:Number($('ramen').value)},{product_id:COLA,quantity:Number($('cola').value)}];
  return post(fail?'두 번째 품목 저장 실패':'두 품목 정상 주문','/orders',{corp_id:COMPANY,items},fail?{'X-Lab-Fail-Second':'yes'}:{});
}
$('order-form').addEventListener('submit',e=>{e.preventDefault();order();});
$('fail').addEventListener('click',()=>order(true));
$('single').addEventListener('click',()=>post('신라면 1개 새 주문','/orders',{corp_id:COMPANY,items:[{product_id:RAMEN,quantity:1}]}));
$('refresh').addEventListener('click',()=>run('DB 재조회','/lab/snapshot'));
$('price-up').addEventListener('click',()=>post('현재 가격 변경','/lab/price',{price:6000}));
$('price-restore').addEventListener('click',()=>post('현재 가격 원복','/lab/price',{price:5000}));
$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('report').value);$('copy-status').textContent='실제 관찰 기록을 복사했습니다.';}catch{$('report-details').open=true;$('report').focus();$('report').select();$('copy-status').textContent='아래 선택된 기록을 Ctrl+C로 복사하세요.';}});
run('DB 조회','/lab/snapshot');

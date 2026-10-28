const $=id=>document.getElementById(id);
let session=sessionStorage.getItem('ch07-session');
let activeKey=sessionStorage.getItem('ch07-key')||crypto.randomUUID();
let last=JSON.parse(sessionStorage.getItem('ch07-last')||'null');
let busy=false;let observations=[];
function text(tag,value,parent){const el=document.createElement(tag);el.textContent=value;parent.append(el);return el;}
function remember(){sessionStorage.setItem('ch07-key',activeKey);sessionStorage.setItem('ch07-last',JSON.stringify(last));$('active-key').textContent=activeKey;}
function trace(steps,parent){
  for(const s of steps){const card=text('article','',parent);card.className='sql-step';text('h3',`${s.step}. ${s.phase}${s.error?' · '+s.error:''}`,card);text('p','호출한 구문과 전달값',card);text('pre',`${s.sql}\n전달값: ${JSON.stringify(s.parameters)}`,card);text('p','SQLite가 실제 실행한 SQL',card);text('pre',s.executed_sql.join('\n')||'실행 콜백 없음',card);if(s.error)text('pre',`${s.error_detail}\nSQLite 오류: ${s.sqlite_errorname}`,card);if(s.rows.length)text('pre',JSON.stringify(s.rows,null,2),card);if(s.affected_rows!==null)text('p',`영향받은 행: ${s.affected_rows}`,card);}
}
function show(r){
  $('request').textContent=`요청 ${r.request_id} · HTTP ${r.status_code} · ${r.outcome} · ${r.detail}`;
  $('error').textContent=r.status_code>=400?r.detail:'';$('trace').replaceChildren();
  if(r.cases){$('comparison').replaceChildren();for(const c of r.cases){const card=text('article','',$('comparison'));text('h3',c.label,card);text('p',`HTTP ${c.status_code} · ${c.detail}`,card);text('strong',`재고 ${c.snapshot.stock[0].qty} · 주문 ${c.snapshot.orders_count}건`,card);const section=text('div','',$('trace'));text('h3',c.label,section);trace(c.trace,section);}}
  else trace(r.trace,$('trace'));
  if(r.snapshot){const s=r.snapshot;$('observed').textContent=`요청 ${r.request_id}의 새 연결 조회`;$('stock-a').textContent=s.stock.find(p=>p.prod_code==='A001')?.qty??'—';$('stock-b').textContent=s.stock.find(p=>p.prod_code==='B001')?.qty??'—';$('sale-count').textContent=s.sales_count;$('sale-no').textContent=r.sale_no??'—';$('sales').replaceChildren();for(const row of s.sales){const tr=text('tr','',$('sales'));for(const key of ['id','prod_code','qty','request_key'])text('td',row[key],tr);}$('empty-sales').textContent=s.sales.length?'':'아직 판매 기록이 없습니다.';$('failure-state').textContent=s.failure_enabled?'저장 실패 장치: 켜짐':'저장 실패 장치: 꺼짐';}
}
async function send(action,fields={}){
  if(busy)return;busy=true;document.querySelectorAll('button,input,select').forEach(e=>e.disabled=true);$('copy-status').textContent='';$('request').textContent='요청 처리 중입니다.';$('trace').replaceChildren();
  try{const body={session,...fields};const r=await fetch('/api/'+action,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body),cache:'no-store'});const data=await r.json();if(data.status_code!==r.status||!Array.isArray(data.trace))throw Error('unexpected response');if(data.session){session=data.session;sessionStorage.setItem('ch07-session',session);}show(data);if(action==='reset'&&r.ok){observations=observations.filter(o=>o.action==='compare');last=null;activeKey=crypto.randomUUID();remember();}observations.push({action,input:body,response:data});$('report').value=JSON.stringify(observations,null,2);return data;}
  catch{$('error').textContent='서버 연결을 확인하세요. 결과 확인 전 새 키로 같은 판매를 보내지 마세요.';$('request').textContent='결과 미확인';$('observed').textContent='현재 표시값은 이전 조회입니다. 판매 상태를 다시 조회하세요.';$('trace').replaceChildren();}
  finally{busy=false;document.querySelectorAll('button,input,select').forEach(e=>e.disabled=false);}
}
function saleBody(){return {key:activeKey,product:$('product').value,quantity:Number($('sale-quantity').value)};}
$('compare-form').addEventListener('submit',e=>{e.preventDefault();if($('compare-form').reportValidity())send('compare',{initial:Number($('compare-stock').value),quantity:Number($('compare-quantity').value)});});
$('sale-form').addEventListener('submit',e=>{e.preventDefault();if(!$('sale-form').reportValidity())return;if(last&&last.key===activeKey){$('error').textContent='같은 요청 다시 보내기 또는 새 판매 시작을 사용하세요.';return;}last=saleBody();remember();send('sale',last);});
$('retry').addEventListener('click',()=>{if(!last){$('error').textContent='먼저 판매 요청을 보내세요.';return;}send('sale',last);});
$('new').addEventListener('click',()=>{activeKey=crypto.randomUUID();last=null;remember();$('request').textContent='새 판매 요청 키를 준비했습니다. DB는 초기화하지 않았습니다.';});
$('conflict').addEventListener('click',()=>{if(!last){$('error').textContent='먼저 판매 요청을 보내세요.';return;}if(!$('sale-form').reportValidity())return;send('sale',{...saleBody(),key:last.key});});
$('reset').addEventListener('click',()=>{if(!$('sale-stock').reportValidity())return;send('reset',{initial:Number($('sale-stock').value)});});
$('refresh').addEventListener('click',()=>send('state'));
for(const [id,enabled] of [['fail-on',true],['fail-off',false]])$(id).addEventListener('click',()=>send('failure',{enabled}));
$('copy').addEventListener('click',async()=>{try{await navigator.clipboard.writeText($('report').value);$('copy-status').textContent='실제 실행 결과를 복사했습니다.';}catch{$('report-details').open=true;$('report').focus();$('report').select();$('copy-status').textContent='아래 결과를 Ctrl+C로 복사하세요.';}});
for(const form of document.querySelectorAll('form'))form.addEventListener('invalid',()=>{$('request').textContent='입력 단계에서 중단 · 서버 요청 없음';$('trace').replaceChildren();},true);
remember();
async function start(){if(session){try{const r=await fetch('/api/state?session='+encodeURIComponent(session),{cache:'no-store'});const d=await r.json();if(r.ok){show(d);observations=[{action:'state',input:{session},response:d}];$('report').value=JSON.stringify(observations,null,2);return;}if(r.status!==404&&r.status!==422)throw Error();}catch{$('error').textContent='서버 연결을 확인한 뒤 새로고침하세요. 판매 상태는 초기화하지 않았습니다.';return;}}await send('session');}
start();

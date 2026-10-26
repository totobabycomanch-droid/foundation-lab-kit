import { createApp, ref, onMounted, onUnmounted } from '/vendor/vue.js';
import { OrderForm } from './order-form.js';
import { CompanyProbe } from './company-probe.js';
import {
  lastRequest, firstResponse, replayResponse, inFlight, repeatLastOrder, clearLastRequest,
} from './order-transport.js';

createApp({
  components: { OrderForm, CompanyProbe },
  setup() {
    const orders = ref([]);
    const observations = ref({ request_count: 0, pending_count: 0 });
    const error = ref('');
    const resetting = ref(false);
    const ready = ref(false);
    const replayError = ref('');
    const replayMessage = ref('');
    let timer;
    let stopped = false;

    async function refresh() {
      try {
        const [countsResponse, ordersResponse] = await Promise.all([
          fetch('/api/observations', { cache: 'no-store' }),
          fetch('/api/orders', { cache: 'no-store' }),
        ]);
        if (!countsResponse.ok || !ordersResponse.ok) throw new Error('관찰 결과를 읽지 못했습니다.');
        observations.value = await countsResponse.json();
        orders.value = await ordersResponse.json();
        error.value = '';
        ready.value = true;
      } catch (cause) {
        ready.value = false;
        error.value = `서버 연결을 확인하세요. ${cause.message}`;
      }
    }

    async function poll() {
      if (!resetting.value) await refresh();
      if (!stopped) timer = setTimeout(poll, 400);
    }

    async function reset() {
      resetting.value = true;
      try {
        const response = await fetch('/api/reset', { method: 'POST' });
        if (!response.ok) throw new Error('저장 요청이 끝난 뒤 초기화하세요.');
        clearLastRequest();
        replayError.value = '';
        replayMessage.value = '';
        await refresh();
      } catch (cause) {
        error.value = cause.message;
      } finally {
        resetting.value = false;
      }
    }

    async function repeat() {
      replayError.value = '';
      replayMessage.value = '';
      try {
        const response = await repeatLastOrder();
        if (!response.ok) throw new Error(`재전송 응답을 확인하세요. HTTP ${response.status}`);
        replayMessage.value = '같은 요청의 응답을 받았습니다.';
      } catch (cause) {
        replayError.value = cause.message;
      }
    }

    onMounted(poll);
    onUnmounted(() => { stopped = true; clearTimeout(timer); });
    return {
      orders, observations, error, reset, resetting, ready, repeat, replayError, replayMessage,
      lastRequest, firstResponse, replayResponse, inFlight,
    };
  },
  template: `
    <main aria-labelledby="title">
      <header><p class="eyebrow">CHAPTER 3</p><h1 id="title">작은 발주 등록 화면</h1>
        <p>AI로 기능을 만들고, 저장 결과를 직접 확인합니다.</p></header>
      <div class="layout">
        <section aria-labelledby="form-title"><h2 id="form-title">발주 등록</h2><OrderForm /></section>
        <section aria-labelledby="observe-title"><h2 id="observe-title">실습용 관찰 장치</h2>
          <p>서버가 받은 저장 요청과 DB에서 다시 읽은 목록입니다.</p>
          <p v-if="error" role="alert">{{ error }}</p>
          <p v-if="!ready && !error" role="status">관찰 결과를 읽는 중입니다.</p>
          <dl v-if="ready" class="metrics">
            <div><dt>요청 횟수</dt><dd data-testid="request-count">{{ observations.request_count }}</dd></div>
            <div><dt>처리 중 요청</dt><dd data-testid="pending-count">{{ observations.pending_count }}</dd></div>
            <div><dt>저장 건수</dt><dd data-testid="stored-count">{{ orders.length }}</dd></div>
          </dl>
          <div class="table-scroll"><table><caption>저장된 발주 목록</caption>
            <thead><tr><th scope="col">발주 ID</th><th scope="col">품명</th><th scope="col">수량</th></tr></thead>
            <tbody><tr v-for="order in orders" :key="order.id"><td>{{ order.id }}</td><td>{{ order.item_name }}</td><td>{{ order.quantity }}</td></tr></tbody>
          </table></div>
          <p v-if="ready && !orders.length">저장된 발주가 없습니다.</p>
          <div class="replay-panel" aria-labelledby="replay-title">
            <h3 id="replay-title">같은 요청 재전송</h3>
            <p>입력 폼과 별도로, 마지막 저장 요청의 키와 내용을 그대로 다시 보냅니다.</p>
            <p v-if="lastRequest" class="request-key">요청 키: <span data-testid="request-key">{{ lastRequest.key }}</span></p>
            <p v-if="lastRequest" class="request-key">전송한 내용: {{ lastRequest.body }}</p>
            <p>처음 응답의 발주 ID: <strong data-testid="first-order-id">{{ firstResponse?.id ?? '—' }}</strong></p>
            <p>재전송 응답의 발주 ID: <strong data-testid="replay-order-id">{{ replayResponse?.id ?? '—' }}</strong></p>
            <button class="secondary" type="button" :disabled="!ready || resetting || inFlight > 0 || observations.pending_count > 0 || !lastRequest" @click="repeat">같은 요청 다시 보내기</button>
            <p v-if="replayMessage" role="status">{{ replayMessage }}</p>
            <p v-if="replayError" role="alert">{{ replayError }}</p>
          </div>
          <button class="secondary" type="button" :disabled="!ready || resetting || inFlight > 0 || observations.pending_count > 0" @click="reset">실습 데이터 초기화</button>
        </section>
      </div>
      <CompanyProbe />
      <p class="footnote">저장 응답은 관찰을 위해 약 1.2초 기다립니다. 관찰 수치는 약 0.4초마다 갱신합니다.</p>
    </main>`,
}).mount('#app');

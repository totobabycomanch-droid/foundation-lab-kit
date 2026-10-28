import { createApp, ref, computed } from '/vendor/vue.js';
import { send } from './transport.js';
import { ApprovalAction } from './approval-action.js';

createApp({
  components: { ApprovalAction },
  setup() {
    const space = ref('main');
    const user = ref(null);
    const orders = ref([]);
    const selected = ref(null);
    const result = ref(null);
    const error = ref('');
    const notice = ref('실습 사용자를 선택하세요.');
    const busy = ref(false);
    const menuOpen = ref(false);
    const spaceLabel = computed(() => space.value === 'main' ? '본 실습' : '회사 경계 결함 실습');
    const prettyResult = computed(() => result.value ? JSON.stringify(result.value.body, null, 2) : '');

    function clearView() {
      user.value = null;
      orders.value = [];
      selected.value = null;
      result.value = null;
      error.value = '';
      menuOpen.value = false;
    }
    async function task(action) {
      if (busy.value) return;
      busy.value = true;
      error.value = '';
      try { await action(); }
      catch { error.value = '서버 연결을 확인한 뒤 다시 시도하세요.'; }
      finally { busy.value = false; }
    }
    async function loadOrders() {
      const response = await send(space.value, '/orders');
      if (response.status !== 200) {
        orders.value = [];
        selected.value = null;
        if (response.status === 401) user.value = null;
        throw new Error('Unable to observe orders');
      }
      orders.value = response.body;
      if (selected.value) {
        selected.value = orders.value.find(order => order.id === selected.value.id) ?? null;
      }
    }
    async function switchSpace(next) {
      if (busy.value) return;
      space.value = next;
      clearView();
      notice.value = '실습 사용자를 선택하세요.';
      await task(async () => {
        const response = await send(space.value, '/me');
        if (response.status === 200) {
          user.value = response.body;
          await loadOrders();
          notice.value = '이 공간에서 선택한 사용자로 접속했습니다.';
        }
      });
    }
    async function login(id) {
      await task(async () => {
        clearView();
        const response = await send(space.value, '/session', 'POST', { user_id: id });
        result.value = response;
        if (response.status === 200) {
          user.value = response.body;
          await loadOrders();
          notice.value = '발주를 선택해 상세 내용을 확인하세요.';
        }
      });
    }
    async function choose(id) {
      await task(async () => {
        selected.value = null;
        const response = await send(space.value, `/orders/${id}`);
        result.value = response;
        if (response.status === 200) selected.value = response.body;
      });
    }
    async function approve(id) {
      await task(async () => {
        result.value = await send(space.value, `/orders/${id}/approve`, 'POST');
        await loadOrders();
        notice.value = '실제 응답과 다시 조회한 발주 상태를 비교하세요.';
      });
    }
    async function reset() {
      await task(async () => {
        const response = await send(space.value, '/reset', 'POST');
        if (response.status === 200) {
          clearView();
          notice.value = '초기화했습니다. 시작 사용자와 발주를 선택하세요.';
        }
        result.value = response;
      });
    }
    async function refresh() {
      await task(async () => {
        const response = await send(space.value, '/me');
        if (response.status !== 200) {
          clearView();
          result.value = response;
          notice.value = '실습 사용자를 다시 선택하세요.';
          return;
        }
        user.value = response.body;
        await loadOrders();
      });
    }
    async function openMenu() {
      await task(async () => {
        if (!user.value) return;
        await loadOrders();
        menuOpen.value = true;
      });
    }
    switchSpace('main');
    return { space, user, orders, selected, result, error, notice, busy, spaceLabel,
      prettyResult, menuOpen, switchSpace, login, choose, approve, reset, refresh, openMenu };
  },
  template: `
    <header><p>Chapter 4</p><h1>발주 승인 실습</h1>
      <p>누가, 어느 회사의, 어떤 상태의 발주를 승인할 수 있을까요?</p></header>
    <nav aria-label="실습 공간">
      <button :disabled="busy" :aria-pressed="space === 'main'" @click="switchSpace('main')">본 실습</button>
      <button :disabled="busy" :aria-pressed="space === 'defect'" @click="switchSpace('defect')">회사 경계 결함 실습</button>
    </nav>
    <section aria-label="사용자 선택">
      <h2>{{ spaceLabel }}</h2>
      <div class="actions">
        <button :disabled="busy" @click="login('a_reader')">A회사 조회 담당자로 접속</button>
        <button :disabled="busy" @click="login('a_manager')">A회사 관리자로 접속</button>
        <button :disabled="busy" @click="login('b_manager')">B회사 관리자로 접속</button>
      </div>
      <p data-testid="current-user">현재 사용자: {{ user ? user.display_name + ' / 회사 ' + user.corp_id + ' / ' + user.role : '선택 안 됨' }}</p>
      <p role="status">{{ notice }}</p><p v-if="error" role="alert">{{ error }}</p>
      <button :disabled="busy" @click="reset">실습 데이터 초기화</button>
      <button :disabled="busy || !user" @click="refresh">상태 다시 조회</button>
      <button :disabled="busy || !user" @click="openMenu">발주 메뉴 열기</button>
    </section>
    <div class="columns">
      <section v-if="user && menuOpen" aria-label="발주 메뉴"><h2>발주 목록</h2>
        <p v-if="!orders.length">접속 후 자기 회사의 발주가 표시됩니다.</p>
        <table v-else><caption>서버 DB에서 조회한 발주</caption>
          <thead><tr><th>발주</th><th>상태</th><th>승인 처리 횟수</th><th>상세</th></tr></thead>
          <tbody><tr v-for="order in orders" :key="order.id" :data-order-id="order.id">
            <td>{{ order.id }} / {{ order.item_name }}</td>
            <td>{{ order.status === 'PENDING' ? '승인 대기' : '승인 완료' }}</td>
            <td>{{ order.approval_count }}</td>
            <td><button :disabled="busy" @click="choose(order.id)">{{ order.id }} 상세 조회</button></td>
          </tr></tbody>
        </table>
        <div v-if="selected" class="detail"><h3>발주 {{ selected.id }}</h3>
          <p>{{ selected.item_name }} / 수량 {{ selected.quantity }} / {{ selected.status }} / 승인 처리 횟수 {{ selected.approval_count }}</p>
          <approval-action v-if="space === 'main'" :user="user" :order="selected" :busy="busy" @approve="approve" />
          <button :disabled="busy" @click="approve(selected.id)">승인 요청 직접 보내기</button>
        </div>
        <div v-if="space === 'defect'" class="detail"><h3>회사 경계 확인</h3>
          <p>A회사 관리자로 접속한 뒤 2001번 발주에 요청을 보냅니다.</p>
          <button :disabled="busy || !user" @click="approve(2001)">B회사 발주 승인 요청 보내기</button>
        </div>
      </section>
      <section><h2>실제 서버 응답</h2>
        <p v-if="!result">요청을 보내면 응답이 표시됩니다.</p>
        <template v-else><p data-testid="http-status">HTTP {{ result.status }}</p><pre data-testid="response-body">{{ prettyResult }}</pre></template>
      </section>
    </div>`,
}).mount('#app');

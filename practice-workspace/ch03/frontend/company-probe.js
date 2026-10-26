import { ref, onMounted } from '/vendor/vue.js';

// This observation component displays the actual response, including failure bodies.
export const CompanyProbe = {
  setup() {
    const user = ref(null);
    const busy = ref(false);
    const error = ref('');
    const result = ref(null);

    async function readUser() {
      const response = await fetch('/api/lab/me', { cache: 'no-store' });
      if (response.status === 401) { user.value = null; return; }
      if (!response.ok) throw new Error('현재 테스트 사용자를 확인하지 못했습니다.');
      user.value = await response.json();
    }

    async function login(userId) {
      busy.value = true;
      error.value = '';
      result.value = null;
      user.value = null;
      try {
        const response = await fetch('/api/lab/login', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ user_id: userId }),
        });
        if (!response.ok) throw new Error('테스트 사용자 선택에 실패했습니다.');
        await readUser();
      } catch (cause) { error.value = cause.message; }
      finally { busy.value = false; }
    }

    async function query(orderId) {
      busy.value = true;
      error.value = '';
      result.value = null;
      try {
        const response = await fetch(`/api/lab/orders/${orderId}`, { cache: 'no-store' });
        result.value = { status: response.status, body: await response.text() };
        if (response.status === 401) user.value = null;
      } catch (cause) { error.value = cause.message; }
      finally { busy.value = false; }
    }

    onMounted(async () => {
      busy.value = true;
      try { await readUser(); }
      catch (cause) { error.value = cause.message; }
      finally { busy.value = false; }
    });
    return { user, busy, error, result, login, query };
  },
  template: `<section class="company-probe" aria-labelledby="company-title" :aria-busy="busy">
    <h2 id="company-title">회사별 조회 실습</h2>
    <p>조회용 발주 두 건과 테스트 사용자는 준비되어 있습니다. 위에서 저장한 발주와는 별도 데이터입니다.</p>
    <div class="probe-actions">
      <button class="secondary" type="button" :disabled="busy" @click="login('user_a')">A회사 사용자로 접속</button>
      <button class="secondary" type="button" :disabled="busy" @click="login('user_b')">B회사 사용자로 접속</button>
    </div>
    <p>서버에서 확인한 사용자: <strong data-testid="company-user">{{ user?.user_id ?? '선택 전' }}</strong></p>
    <p>현재 사용자 회사: <strong data-testid="company-name">{{ user?.corp_name ?? '선택 전' }}</strong></p>
    <div class="probe-actions">
      <button type="button" :disabled="busy || !user" @click="query(1001)">A회사 발주 조회</button>
      <button type="button" :disabled="busy || !user" @click="query(2001)">B회사 발주 조회</button>
    </div>
    <p v-if="error" role="alert">{{ error }}</p>
    <div v-if="result" class="query-result" role="status">
      <p>실제 응답 상태: <strong data-testid="company-status">{{ result.status }}</strong></p>
      <pre data-testid="company-body">{{ result.body }}</pre>
    </div>
  </section>`,
};

<template>
  <section aria-labelledby="orders-title" :aria-busy="loading">
    <div class="toolbar">
      <h2 id="orders-title">확인할 주문</h2>
      <button type="button" class="secondary" :disabled="loading || busyOrderId !== null" @click="loadOrders">
        {{ loading ? '조회 중...' : '현재 상태 다시 조회' }}
      </button>
    </div>
    <p v-if="loadError" role="alert" class="error">{{ loadError }}</p>
    <p v-if="loading" role="status">저장된 주문과 재고를 읽고 있습니다.</p>
    <p v-else-if="!loadError && orders.length === 0" role="status">준비된 주문이 없습니다. AI에게 실습 데이터 준비를 요청하세요.</p>
    <div class="orders">
      <article v-for="order in orders" :key="order.order_id" class="card" :aria-label="order.order_name">
        <h3>{{ order.order_name }}</h3>
        <p class="product">{{ order.product_name }}</p>
        <dl>
          <div><dt>주문 수량</dt><dd>{{ order.qty }}개</dd></div>
          <div><dt>현재 재고</dt><dd>{{ order.current_stock }}개</dd></div>
          <div><dt>주문 상태</dt><dd>{{ order.status === 'PAID' ? '승인 완료' : '승인 대기' }}</dd></div>
        </dl>
        <p v-if="messages[order.order_id]" :role="messages[order.order_id].kind === 'error' ? 'alert' : 'status'"
           :class="messages[order.order_id].kind">{{ messages[order.order_id].text }}</p>
        <button type="button" class="approve"
                :disabled="loading || Boolean(loadError) || busyOrderId !== null || order.status === 'PAID' || Boolean(pendingCheck[order.order_id])"
                :aria-busy="busyOrderId === order.order_id" @click="approveOrder(order)">
          {{ busyOrderId === order.order_id ? '처리 중...' : order.status === 'PAID' ? '승인 완료' : pendingCheck[order.order_id] ? '상태 확인 필요' : '주문 승인' }}
        </button>
      </article>
    </div>
  </section>
</template>

<script>
import axios from 'axios'

const api = axios.create({ baseURL: 'http://localhost:8000', timeout: 10000 })

export default {
  data() {
    return { orders: [], loading: false, loadError: '', busyOrderId: null, messages: {}, pendingCheck: {} }
  },
  mounted() { this.loadOrders() },
  methods: {
    async loadOrders() {
      if (this.loading) return false
      this.loading = true
      this.loadError = ''
      try {
        const response = await api.get('/orders')
        const items = response.data.items
        if (!Array.isArray(items) || items.some(order => !order.order_id || !order.order_name || !order.product_name ||
            !order.product_id || !Number.isInteger(order.qty) || order.qty < 1 ||
            !Number.isInteger(order.current_stock) || order.current_stock < 0 ||
            !['CREATED', 'PAID'].includes(order.status))) {
          throw new Error('invalid_order_response')
        }
        this.orders = items
        for (const [id, expectation] of Object.entries(this.pendingCheck)) {
          const order = items.find(item => item.order_id === id)
          if (order?.status === 'PAID') {
            this.messages[id] = { kind: 'success', text: '승인 완료 상태와 현재 재고를 다시 조회했습니다.' }
            delete this.pendingCheck[id]
          } else if (order?.status === 'CREATED' && expectation === 'unknown') {
            this.messages[id] = { kind: 'info', text: '현재 저장 상태는 승인 대기입니다. 다시 요청할 수 있습니다.' }
            delete this.pendingCheck[id]
          } else {
            this.messages[id] = { kind: 'error', text: '승인 결과를 저장 상태에서 확인하지 못했습니다. AI에게 조사를 요청하세요.' }
          }
        }
        return true
      } catch {
        this.loadError = '최신 주문 상태를 읽지 못했습니다. 연결을 확인하고 다시 조회하세요. 표시된 값이 있다면 이전 조회 결과입니다.'
        return false
      } finally {
        this.loading = false
      }
    },
    async approveOrder(order) {
      const id = order.order_id
      if (this.loading || this.loadError || this.busyOrderId !== null || order.status === 'PAID' || this.pendingCheck[id]) return
      this.busyOrderId = id
      delete this.messages[id]
      try {
        const response = await api.post('/orders/approve', { order_id: id, product_id: order.product_id, qty: order.qty })
        if (response.status !== 200 || response.data.status !== 'success') throw new Error('unconfirmed_response')
        this.pendingCheck[id] = 'success'
        const refreshed = await this.loadOrders()
        if (!refreshed) {
          this.messages[id] = { kind: 'error', text: '저장은 성공했지만 최신 상태를 읽지 못했습니다. 현재 상태를 다시 조회해 주세요.' }
        }
      } catch (error) {
        const status = error.response?.status
        if (status === 400 || status === 422) {
          const detail = error.response?.data?.detail
          this.messages[id] = { kind: 'error', text: typeof detail === 'string' ? detail : '요청 내용을 확인해 주세요.' }
          await this.loadOrders()
        } else {
          this.pendingCheck[id] = 'unknown'
          this.messages[id] = { kind: 'error', text: '처리 결과를 확인하지 못했습니다. 현재 상태를 다시 조회해 주세요.' }
          await this.loadOrders()
        }
      } finally {
        this.busyOrderId = null
      }
    },
  },
}
</script>

<style scoped>
.toolbar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
h2 { font-size: 1.125rem; }
.orders { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 22rem), 1fr)); gap: 1rem; }
.card { background: white; border: 1px solid #dee2e6; border-radius: .75rem; padding: 1.5rem; }
h3 { margin: 0 0 .5rem; font-size: 1.125rem; }
.product { color: #526779; margin-top: 0; }
dl { margin: 1.5rem 0; }
dl div { display: flex; justify-content: space-between; gap: 1rem; padding: .5rem 0; border-bottom: 1px solid #e7edf1; }
dd { margin: 0; font-weight: 600; }
button { font: inherit; border: 1px solid transparent; border-radius: .375rem; padding: .75rem 1rem; cursor: pointer; }
button:focus-visible { outline: 3px solid #243444; outline-offset: 3px; }
button:disabled { cursor: not-allowed; opacity: .65; }
.approve { width: 100%; background: #2c3e50; color: white; }
.secondary { background: white; border-color: #657583; color: #243444; }
.error, .success, .info { padding: .75rem; border-radius: .375rem; overflow-wrap: anywhere; line-height: 1.5; }
.error { background: #fff1f1; color: #991b1b; }
.success { background: #effaf3; color: #166534; }
.info { background: #eef5ff; color: #1e40af; }
</style>

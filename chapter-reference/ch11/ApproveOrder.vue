<template>
  <section class="order-card" aria-labelledby="order-title">
    <h2 id="order-title" class="order-title">주문 승인 관리 (UX 방어막 적용)</h2>
    <div class="order-detail-box">
      <p class="detail-text">주문 ID: {{ orderId }}</p>
      <p class="detail-text">상품 ID: {{ productId }}</p>
      <p class="detail-text">요청 수량: {{ quantity }}개</p>
      
      <!-- 1. 주문 성공 시 시각적 피드백 메시지 제공 -->
      <div v-if="isPaid" class="status-alert success-box" role="status">
        [완료] 주문 승인이 완료되었습니다. (재고가 차감됨)
      </div>
      
      <!-- 2. 예외 처리 시 화면 내부 에러 전파 메시지 제공 -->
      <div v-if="errorMessage" class="status-alert error-box" role="alert">
        [오류] 승인 실패: {{ errorMessage }}
      </div>

      <div class="button-container">
        <!-- 3. 요청 중이거나 이미 승인 완료(isPaid) 상태일 때 버튼 비활성화 -->
        <button
          type="button"
          @click="approveOrder" 
          class="btn-approve" 
          :disabled="isLoading || isPaid"
          :aria-busy="isLoading"
          :class="{ 'btn-loading': isLoading, 'btn-success': isPaid }"
        >
          <span v-if="isLoading">처리 중...</span>
          <span v-else-if="isPaid">승인 완료</span>
          <span v-else>주문 승인 API 호출</span>
        </button>
      </div>
    </div>
  </section>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      orderId: '00000000-0000-0000-0000-000000000001',
      productId: 'PROD-100',
      quantity: 3,
      isLoading: false,    // 로딩 잠금 상태 제어용 변수
      isPaid: false,       // 승인 완료 상태 제어용 변수
      errorMessage: ''     // 예외 전파용 변수
    };
  },
  methods: {
    async approveOrder() {
      // 현재 화면에서 요청 중이거나 완료됐다면 다시 호출하지 않습니다.
      if (this.isLoading || this.isPaid) return;
      // 로딩 활성화 및 이전 오류 초기화
      this.isLoading = true;
      this.errorMessage = '';
      
      try {
        const response = await axios.post('http://localhost:8000/orders/approve', {
          order_id: this.orderId,
          product_id: this.productId,
          qty: this.quantity
        });
        if (response.status === 200 && response.data.status === 'success') {
          this.isPaid = true;
        } else {
          this.errorMessage = '승인 완료 응답을 확인하지 못했습니다.';
        }
      } catch (error) {
        // 에러 메시지를 alert 창 대신 화면 컴포넌트 내부에 바인딩하여 안전하게 전파
        this.errorMessage = error.response?.data?.detail || '서버에 연결할 수 없습니다. 연결 상태를 확인하고 다시 시도하세요.';
      } finally {
        // 로딩만 해제합니다. 성공 뒤에는 isPaid로 버튼 잠금을 유지합니다.
        this.isLoading = false;
      }
    }
  }
};
</script>

<style scoped>
.order-card {
  max-width: 28rem;
  margin: 2rem auto;
  padding: 1.5rem;
  background-color: white;
  border-radius: 0.75rem;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
  font-family: sans-serif;
}
.order-title {
  font-size: 1.25rem;
  font-weight: bold;
  margin-bottom: 1rem;
  color: #111827;
  margin-top: 0;
}
.order-detail-box {
  border: 1px solid #e5e7eb;
  padding: 1rem;
  border-radius: 0.375rem;
}
.detail-text {
  overflow-wrap: anywhere;
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0.25rem 0;
}
.status-alert {
  overflow-wrap: anywhere;
  margin-top: 1rem;
  padding: 0.75rem;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}
.success-box {
  background-color: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}
.error-box {
  background-color: #fef2f2;
  color: #991b1b;
  border: 1px solid #fecaca;
}
.button-container {
  margin-top: 1rem;
  display: flex;
  gap: 0.5rem;
}
.btn-approve {
  width: 100%;
  padding: 0.75rem 1rem;
  color: white;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  background-color: #3b82f6;
  font-weight: 600;
  transition: background-color 0.2s;
}
.btn-approve:hover:not(:disabled) {
  background-color: #2563eb;
}
.btn-approve:focus-visible {
  outline: 3px solid #111827;
  outline-offset: 3px;
}
.btn-approve:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}
.btn-success {
  background-color: #10b981 !important;
}
</style>

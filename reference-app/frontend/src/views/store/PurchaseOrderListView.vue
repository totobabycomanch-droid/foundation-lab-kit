<template>
  <div class="purchase-layout">
    <Sidebar />
    
    <main class="main-content">
      <header class="content-header">
        <h1>본사로 발주 요청</h1>
        <div class="header-breadcrumb">가맹점 발주(주문) 관리(B100) &gt; 본사로 발주 요청(B110)</div>
      </header>

      <div class="view-container">
        <!-- 상단 검색 및 버튼 영역 -->
        <section class="search-action-section">
          <div class="search-area">
            <span class="search-label">발주일자</span>
            <input type="date" v-model="searchStartDate" class="date-input" />
            <span class="date-sep">~</span>
            <input type="date" v-model="searchEndDate" class="date-input" />
            <button class="btn-search" @click="fetchPurchaseOrders(1)">검색</button>
          </div>
          <div class="action-buttons">
            <button 
              class="btn-create" 
              @click="navigateToCreate"
            >발주서 작성</button>
          </div>
        </section>

        <!-- 발주서 목록 그리드 -->
        <section class="grid-section">
          <div class="grid-wrap">
            <div class="table-scroll">
              <table class="data-table">
                <thead>
                  <tr>
                    <th class="col-date">주문일자</th>
                    <th class="col-no">주문번호</th>
                    <th class="col-delivery">납기요청일</th>
                    <th class="col-vat">VAT</th>
                    <th class="col-status">주문상태</th>
                    <th class="col-date">발송일</th>
                    <th class="col-action">입고처리</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="order in purchaseOrders" :key="order.purchase_order_no" @click="navigateToEdit(order.purchase_order_no)" class="clickable-row">
                    <td class="col-date">{{ order.create_date }}</td>
                    <td class="col-no">{{ order.purchase_order_no }}</td>
                    <td class="col-delivery">{{ order.delivery_date }}</td>
                    <td class="col-vat">{{ order.vat_status }}</td>
                    <td class="col-status">
                      <span :class="['status-badge', 'status-' + order.order_status]">
                        {{ order.order_status_name }}
                      </span>
                      <div v-if="order.tracking_no" class="tracking-info">
                        {{ order.delivery_carrier }}: {{ order.tracking_no }}
                      </div>
                    </td>
                    <td class="col-date">{{ order.shipped_at || '-' }}</td>
                    <td class="col-action" @click.stop>
                      <button 
                        v-if="order.order_status === '40'" 
                        class="btn-confirm" 
                        @click="confirmReceipt(order)"
                      >입고확정</button>
                      <span v-else-if="order.order_status === '60'" class="txt-done">입고완료</span>
                      <span v-else>-</span>
                    </td>
                  </tr>
                  <tr v-if="purchaseOrders.length === 0">
                    <td colspan="10" class="no-data">발주 내역이 없습니다.</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- 페이징 영역 -->
            <div class="pagination-wrap">
              <div class="pagination">
                <button class="page-nav" :disabled="currentPage === 1" @click="fetchPurchaseOrders(1)">처음</button>
                <button class="page-nav" :disabled="currentPage === 1" @click="fetchPurchaseOrders(currentPage - 1)">이전</button>
                
                <button 
                  v-for="page in visiblePages" 
                  :key="page" 
                  :class="['page-num', { active: page === currentPage }]"
                  @click="fetchPurchaseOrders(page)"
                >
                  {{ page }}
                </button>

                <button class="page-nav" :disabled="currentPage === totalPages" @click="fetchPurchaseOrders(currentPage + 1)">다음</button>
                <button class="page-nav" :disabled="currentPage === totalPages" @click="fetchPurchaseOrders(totalPages)">끝</button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import Sidebar from '../../components/Sidebar.vue';
import { formatKstDate, oneMonthBefore } from '../../utils/kstDate.js';

const router = useRouter();

// 검색 조건
const searchStartDate = ref('');
const searchEndDate = ref('');

// 데이터 및 페이징
const purchaseOrders = ref([]);
const currentPage = ref(1);
const totalCount = ref(0);
const pageSize = 10;

const totalPages = computed(() => Math.ceil(totalCount.value / pageSize) || 1);

const visiblePages = computed(() => {
  const pages = [];
  let start = Math.max(1, currentPage.value - 4);
  let end = Math.min(totalPages.value, start + 9);
  if (end - start < 9) start = Math.max(1, end - 9);
  
  for (let i = start; i <= end; i++) {
    pages.push(i);
  }
  return pages;
});

const fetchPurchaseOrders = async (page = 1) => {
  try {
    const token = localStorage.getItem('token') || '';
    
    let url = `/api/v1/purchase_orders?page=${page}&page_size=${pageSize}&token=${token}`;
    if (searchStartDate.value) url += `&start_date=${searchStartDate.value}`;
    if (searchEndDate.value) url += `&end_date=${searchEndDate.value}`;

    const response = await fetch(url);
    const result = await response.json();

    if (response.ok) {
      purchaseOrders.value = result.data;
      totalCount.value = result.total_count;
      currentPage.value = page;
    } else {
      throw new Error(result.detail || '데이터를 불러오는데 실패했습니다.');
    }
  } catch (error) {
    console.error('Fetch Error:', error);
    alert(error.message);
  }
};

const confirmReceipt = async (order) => {
  if (!confirm('물품을 정상적으로 수령하셨습니까?\n확정 시 매장 재고에 즉시 반영됩니다.')) return;

  try {
    const token = localStorage.getItem('token') || '';
    const idempotencyKey = crypto.randomUUID();

    // 입고 전표 생성, 재고 반영, 발주 상태 변경(40->60), 감사 로그를
    // 서버가 fn_process_purchase_receipt RPC 한 트랜잭션으로 처리한다.
    const statusUpdateRes = await fetch(`/api/v1/purchase_orders/status_store?token=${token}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Idempotency-Key': idempotencyKey
        },
        body: JSON.stringify({
            purchase_order_no: order.purchase_order_no,
            status: '60'
        })
    });

    const statusResult = await statusUpdateRes.json();

    if (statusUpdateRes.ok) {
        alert('입고 확정 처리가 완료되었습니다. 재고가 업데이트되었습니다.');
        fetchPurchaseOrders(currentPage.value);
    } else {
        alert('입고 확정 처리에 실패했습니다: ' + (statusResult.detail || ''));
    }

  } catch (error) {
    console.error('Confirm Receipt Error:', error);
    alert(error.message);
  }
};

const navigateToCreate = () => {
  router.push('/store/purchase/order/register');
};

const navigateToEdit = (poNo) => {
  router.push(`/store/purchase/order/register/${poNo}`);
};

onMounted(() => {
  // 초기 날짜 설정 (최근 1개월)
  searchEndDate.value = formatKstDate();
  searchStartDate.value = oneMonthBefore(searchEndDate.value);
  
  fetchPurchaseOrders();
});
</script>

<style scoped>
.purchase-layout {
  display: flex;
  min-height: 100vh;
  background-color: #f8f9fa;
}

.main-content {
  margin-left: 240px;
  flex: 1;
  padding: 1.5rem;
  overflow-x: hidden;
}

.content-header {
  border-bottom: 2px solid #3498db;
  margin-bottom: 2rem;
  padding-bottom: 0.5rem;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.content-header h1 {
  margin: 0;
  color: #2980b9;
  font-size: 1.5rem;
  font-weight: 800;
}

.header-breadcrumb {
  font-size: 0.9rem;
  color: #7f8c8d;
  margin-top: 0.25rem;
}

.view-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.search-action-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
  padding: 1rem;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.search-area {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.search-label {
  font-weight: 600;
  font-size: 0.9rem;
  color: #495057;
}

.date-input {
  padding: 0.4rem 0.6rem;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 0.9rem;
}

.date-sep {
  color: #adb5bd;
}

.btn-search {
  padding: 0.4rem 1.2rem;
  background-color: #3498db;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-delete {
  padding: 0.4rem 1rem;
  background-color: white;
  color: #e74c3c;
  border: 1px solid #e74c3c;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.btn-delete:disabled {
  border-color: #dee2e6;
  color: #adb5bd;
  cursor: not-allowed;
}

.btn-create {
  padding: 0.4rem 1rem;
  background-color: #2c3e50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 600;
}

.grid-section {
  flex: 1;
}

.grid-wrap {
  background: white;
  border-radius: 8px;
  border: 1px solid #dee2e6;
  display: flex;
  flex-direction: column;
  min-height: 500px;
}

.table-scroll {
  flex: 1;
  overflow: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th, .data-table td {
  padding: 0.75rem 0.5rem;
  border-bottom: 1px solid #dee2e6;
  text-align: center;
  font-size: 0.85rem;
}

.data-table th {
  background-color: #f8f9fa;
  font-weight: 700;
  color: #495057;
  position: sticky;
  top: 0;
  z-index: 10;
}

.data-table tr:hover {
  background-color: #f1f3f5;
}

.clickable-row {
  cursor: pointer;
}

.col-check { width: 50px; }
.col-date { width: 110px; }
.col-no { width: 130px; }
.col-id { width: 120px; }
.col-name { min-width: 180px; text-align: left !important; }
.col-delivery { width: 110px; }
.col-dcode { width: 80px; }
.col-dname { width: 100px; }
.col-creator { width: 100px; }
.col-vat { width: 100px; }
.col-done { width: 100px; }

.status-badge {
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 700;
}

.status-10 { background-color: #ebf5ff; color: #007bff; border: 1px solid #007bff; }
.status-20 { background-color: #e6fffa; color: #38b2ac; border: 1px solid #38b2ac; }
.status-30 { background-color: #fffaf0; color: #dd6b20; border: 1px solid #dd6b20; }
.status-40 { background-color: #f0f5ff; color: #5a67d8; border: 1px solid #5a67d8; }
.status-50 { background-color: #e6ffed; color: #2f855a; border: 1px solid #2f855a; }
.status-60 { background-color: #edf2f7; color: #4a5568; border: 1px solid #4a5568; }

.tracking-info {
  font-size: 0.75rem;
  color: #7f8c8d;
  margin-top: 0.2rem;
}

.btn-confirm {
  padding: 0.3rem 0.6rem;
  background-color: #2c3e50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
}

.txt-done {
  color: #27ae60;
  font-weight: 700;
  font-size: 0.8rem;
}

.page-nav:disabled {
  background-color: #f8f9fa;
  color: #adb5bd;
  cursor: not-allowed;
}

/* 페이징 스타일 추가 */
.pagination-wrap {
  display: flex;
  justify-content: center;
  padding: 1.5rem 0;
  border-top: 1px solid #dee2e6;
}

.pagination {
  display: flex;
  gap: 0.4rem;
}

.page-nav, .page-num {
  padding: 0.4rem 0.8rem;
  border: 1px solid #dee2e6;
  background-color: white;
  color: #495057;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.85rem;
  font-weight: 500;
  transition: all 0.2s;
}

.page-num.active {
  background-color: #3498db;
  color: white;
  border-color: #3498db;
}

.page-num:hover:not(.active), .page-nav:hover:not(:disabled) {
  background-color: #f8f9fa;
  border-color: #cbd5e0;
}
</style>

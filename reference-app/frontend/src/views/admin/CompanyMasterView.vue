<template>
  <div class="company-layout">
    <Sidebar />
    
    <main class="main-content" aria-labelledby="company-master-title">
      <header class="content-header">
        <h1 id="company-master-title">가맹점 마스터 관리</h1>
        <div class="header-breadcrumb">기준정보관리 > 가맹점 마스터(A110)</div>
      </header>

      <section class="grid-container">
        <!-- 업체 리스트 -->
        <div class="grid-wrap list-grid">
          <div class="grid-header-actions">
            <div class="search-box">
              <label class="sr-only" for="company-search">가맹점명 또는 업체 ID 검색</label>
              <input id="company-search" type="search" v-model="searchQuery" placeholder="가맹점명/ID 검색" :disabled="isLoading" @keyup.enter="fetchCompanies">
              <button type="button" class="btn-search" :disabled="isLoading" @click="fetchCompanies">{{ isLoading ? '조회 중...' : '조회' }}</button>
            </div>
            <div class="button-group">
              <button type="button" class="btn-add" :disabled="isSaving" @click="addNewCompany">신규 등록</button>
            </div>
          </div>
          <p v-if="isLoading" class="sr-only" role="status">가맹점 목록을 불러오는 중입니다.</p>
          <div class="table-scroll">
            <table class="data-table" :aria-busy="isLoading">
              <caption class="sr-only">가맹점 목록</caption>
              <thead>
                <tr>
                  <th>구분</th>
                  <th>업체 ID</th>
                  <th>업체명</th>
                  <th>대표자</th>
                  <th>전화번호</th>
                </tr>
              </thead>
              <tbody>
                <tr 
                  v-for="corp in companies" 
                  :key="corp.corp_id"
                  :class="{ active: selectedCorpId === corp.corp_id }"
                  :aria-selected="selectedCorpId === corp.corp_id"
                  tabindex="0"
                  @click="selectCompany(corp)"
                  @keydown.enter="selectCompany(corp)"
                  @keydown.space.prevent="selectCompany(corp)"
                >
                  <td>
                    <span class="cat-badge cat-20">가맹점</span>
                  </td>
                  <td>{{ corp.corp_id }}</td>
                  <td>{{ corp.name_kr }}</td>
                  <td>{{ corp.ceo_name }}</td>
                  <td>{{ corp.tel_no }}</td>
                </tr>
                <tr v-if="!isLoading && companies.length === 0">
                  <td colspan="5" class="empty-cell">조회된 가맹점이 없습니다.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- 업체 상세 정보 -->
        <div class="grid-wrap detail-grid">
           <div class="grid-header-actions">
            <h3>업체 상세 정보</h3>
            <div class="button-group">
              <button type="button" class="btn-save" :disabled="isSaving" @click="saveCompany">{{ isSaving ? '저장 중...' : '저장' }}</button>
            </div>
          </div>
          <div class="detail-form">
            <div class="form-row">
              <div class="form-item">
                <label for="company-category">업체 구분</label>
                <input id="company-category" type="text" value="가맹점(Franchise)" readonly class="readonly">
              </div>
              <div class="form-item">
                <label for="company-id">업체 ID</label>
                <input id="company-id" type="text" v-model="detail.corp_id" required :readonly="!isNew" :class="{readonly: !isNew}">
              </div>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label for="company-name">업체명(KR)</label>
                <input id="company-name" type="text" v-model="detail.name_kr" required>
              </div>
              <div class="form-item">
                <label for="company-password">비밀번호</label>
                <input id="company-password" type="password" v-model="detail.password" :required="isNew" autocomplete="new-password" placeholder="신규 등록 또는 변경 시 입력">
              </div>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label for="company-ceo">대표자명</label>
                <input id="company-ceo" type="text" v-model="detail.ceo_name">
              </div>
              <div class="form-item">
                <label for="company-tel">전화번호</label>
                <input id="company-tel" type="tel" v-model="detail.tel_no" required>
              </div>
            </div>
            <div class="form-row">
              <div class="form-item">
                <label for="company-zip">우편번호</label>
                <div class="input-with-btn">
                  <input id="company-zip" type="text" v-model="detail.zip_code" readonly class="readonly">
                  <button type="button" class="btn-sub" @click="openPostcode">주소 검색</button>
                </div>
              </div>
            </div>
            <div class="form-row full">
              <div class="form-item">
                <label for="company-address1">주소</label>
                <input id="company-address1" type="text" v-model="detail.address1" placeholder="기본 주소" readonly class="readonly">
                <label class="sr-only" for="company-address2">상세 주소</label>
                <input id="company-address2" type="text" v-model="detail.address2" placeholder="상세 주소" class="address-detail">
              </div>
            </div>
          </div>
        </div>
      </section>
      <p v-if="statusMessage" class="feedback success" role="status">{{ statusMessage }}</p>
      <p v-if="errorMessage" class="feedback error" role="alert">{{ errorMessage }}</p>
    </main>

    <!-- 우편번호 검색 모달 -->
    <Postcode ref="postcodeRef" @select="onPostcodeSelect" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import Sidebar from '../../components/Sidebar.vue';
import Postcode from '../../components/Postcode.vue';

const companies = ref([]);
const searchQuery = ref('');
const selectedCorpId = ref(null);
const isNew = ref(false);
const isLoading = ref(false);
const isSaving = ref(false);
const statusMessage = ref('');
const errorMessage = ref('');

const detail = ref({
  corp_category: '20',
  corp_id: '',
  corp_code: 'AUTO',
  name_kr: '',
  password: '',
  ceo_name: '',
  tel_no: '',
  zip_code: '',
  address1: '',
  address2: ''
});

const postcodeRef = ref(null);

const openPostcode = () => {
  postcodeRef.value.open();
};

const onPostcodeSelect = (data) => {
  detail.value.zip_code = data.zipCode;
  detail.value.address1 = data.address1;
};

const responseError = async (response, fallback) => {
  const body = await response.json().catch(() => ({}));
  return body.detail || fallback;
};

const fetchCompanies = async () => {
  if (isLoading.value) return;
  isLoading.value = true;
  errorMessage.value = '';
  try {
    const token = localStorage.getItem('token') || '';
    const params = new URLSearchParams({
      search_query: searchQuery.value,
      category: '20'
    });
    const res = await fetch(`/api/v1/companies?${params}`, {
      headers: { Authorization: `Bearer ${token}` }
    });
    if (!res.ok) throw new Error(await responseError(res, '가맹점 목록을 불러오지 못했습니다.'));
    const data = await res.json();
    companies.value = Array.isArray(data) ? data : [];
  } catch (e) {
    companies.value = [];
    errorMessage.value = e.message || '가맹점 목록을 불러오지 못했습니다.';
  } finally {
    isLoading.value = false;
  }
};

const selectCompany = (corp) => {
  selectedCorpId.value = corp.corp_id;
  isNew.value = false;
  errorMessage.value = '';
  statusMessage.value = '';
  detail.value = { ...corp, password: '' }; // 비밀번호는 비워둠
};

const addNewCompany = () => {
    isNew.value = true;
    selectedCorpId.value = null;
    errorMessage.value = '';
    statusMessage.value = '';
    detail.value = {
        corp_category: '20',
        corp_id: '',
        corp_code: 'AUTO',
        name_kr: '',
        password: '',
        ceo_name: '',
        tel_no: '',
        zip_code: '',
        address1: '',
        address2: ''
    };
};

const saveCompany = async () => {
    if (isSaving.value) return;
    errorMessage.value = '';
    statusMessage.value = '';
    if (!detail.value.corp_id || !detail.value.name_kr || !detail.value.tel_no) {
        errorMessage.value = '업체 ID, 업체명과 전화번호를 입력해 주세요.';
        return;
    }

    try {
        const token = localStorage.getItem('token') || '';
        const payload = { ...detail.value };
        
        // 비밀번호가 입력된 경우에만 전송 (신규 가입 시 필수)
        if (payload.password) {
            // 평문 비밀번호 전송
        } else if (isNew.value) {
            errorMessage.value = '신규 등록 시 비밀번호는 필수입니다.';
            return;
        } else {
            // 수정 시 비밀번호가 없으면 기존 비밀번호 유지 (백엔드 로직에 따라 다름)
            delete payload.password;
        }

        payload.corp_category = '20';
        isSaving.value = true;
        const res = await fetch('/api/v1/companies', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              Authorization: `Bearer ${token}`
            },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(await responseError(res, '가맹점 저장에 실패했습니다.'));
        const wasNew = isNew.value;
        if (wasNew) addNewCompany();
        statusMessage.value = '가맹점 정보를 저장했습니다.';
        await fetchCompanies();
    } catch (e) {
        errorMessage.value = e.message || '가맹점 저장에 실패했습니다.';
    } finally {
        isSaving.value = false;
    }
};

onMounted(fetchCompanies);
</script>

<style scoped>
.company-layout { display: flex; min-height: 100vh; background: #f8f9fa; }
.main-content { margin-left: 240px; flex: 1; padding: 1.5rem; }
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

.grid-container { display: flex; gap: 1.5rem; height: calc(100vh - 150px); }
.grid-wrap { background: white; border-radius: 8px; border: 1px solid #dee2e6; display: flex; flex-direction: column; }
.list-grid { flex: 1; }
.detail-grid { width: 500px; }

.grid-header-actions { padding: 0.75rem 1rem; border-bottom: 1px solid #dee2e6; display: flex; justify-content: space-between; align-items: center; background: #f1f3f5; }
.search-box { display: flex; gap: 0.5rem; }
.search-box input { padding: 0.3rem 0.5rem; border: 1px solid #ced4da; border-radius: 4px; }
.btn-search, .btn-add, .btn-save { padding: 0.4rem 0.8rem; border-radius: 4px; font-weight: 600; cursor: pointer; border: none; }
.btn-search { background: #34495e; color: white; }
.btn-add { background: #3498db; color: white; }
.btn-save { background: #27ae60; color: white; }
.btn-sub { background: #95a5a6; color: white; padding: 0.3rem 0.6rem; font-size: 0.8rem; border-radius: 4px; cursor: pointer; border: none; white-space: nowrap; flex-shrink: 0; }

.input-with-btn { display: flex; gap: 0.5rem; align-items: center; }
.input-with-btn input { flex: 1; }

.table-scroll { flex: 1; overflow-y: auto; }
.data-table { width: 100%; border-collapse: collapse; }
.data-table th, .data-table td { padding: 0.6rem; border-bottom: 1px solid #dee2e6; text-align: center; font-size: 0.85rem; }
.data-table th { background: #f8f9fa; position: sticky; top: 0; }
.data-table tr:hover { background: #f8f9fa; cursor: pointer; }
.data-table tr.active { background: #e7f1ff; }

.cat-badge { padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: 700; color: white; }
.cat-10 { background: #e74c3c; } /* HQ */
.cat-20 { background: #3498db; } /* Store */
.cat-30 { background: #e67e22; } /* Supply */

.detail-form { padding: 1.5rem; display: flex; flex-direction: column; gap: 1rem; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.form-row.full { grid-template-columns: 1fr; }
.form-item { display: flex; flex-direction: column; gap: 0.4rem; }
.form-item label { font-size: 0.85rem; font-weight: 700; color: #495057; }
.form-item input, .form-item select { padding: 0.5rem; border: 1px solid #ced4da; border-radius: 4px; }
.form-item input.readonly { background: #f1f3f5; cursor: not-allowed; }
.address-detail { margin-top: 5px; }
.empty-cell { padding: 1.5rem; color: #6c757d; }
.feedback { margin: 1rem 0 0 0; padding: 0.75rem 1rem; border-radius: 4px; }
.feedback.success { background: #eaf7ee; color: #1e6b37; }
.feedback.error { background: #fdecec; color: #a12622; }
.sr-only { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; border: 0; }
button:disabled { cursor: not-allowed; opacity: 0.65; }
button:focus-visible, input:focus-visible, tr:focus-visible { outline: 3px solid #1f6feb; outline-offset: 2px; }
@media (max-width: 900px) {
  .main-content { margin-left: 0; padding: 1rem; }
  .grid-container { flex-direction: column; height: auto; }
  .detail-grid { width: 100%; }
  .table-scroll { overflow-x: auto; }
  .data-table { min-width: 680px; }
}
</style>

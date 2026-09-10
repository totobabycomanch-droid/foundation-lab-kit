import { expect, test } from '@playwright/test';

const hqUser = {
  user_id: 'day05-hq-user', corp_id: 'admin', corp_category: '10', corp_type: '0', role: 'MANAGER',
};

const jsonResponse = (route, body, status = 200) => route.fulfill({
  status, contentType: 'application/json', body: JSON.stringify(body),
});

const installHqSession = async (page) => {
  await page.route('**/mapjsapi/bundle/postcode/prod/postcode.v2.js', (route) => route.fulfill({
    status: 200,
    contentType: 'application/javascript',
    body: 'window.daum = window.daum || {};',
  }));
  await page.addInitScript((user) => {
    localStorage.setItem('token', 'day05-e2e-token');
    localStorage.setItem('user', JSON.stringify(user));
    localStorage.setItem('corp_id', user.corp_id);
    localStorage.setItem('bypass_tenant', 'admin');
  }, hqUser);
};

test('D05-E2E-00 redirects the removed self-registration page to HQ management', async ({ page }) => {
  await installHqSession(page);
  await page.route(/^https?:\/\/[^/]+\/api\//, (route) => jsonResponse(route, []));

  await page.goto('/register');

  await expect(page).toHaveURL(/\/admin\/company$/);
  await expect(page.getByRole('heading', { name: '가맹점 마스터 관리' })).toBeVisible();
});

test('D05-E2E-01 filters franchises, supports keyboard selection, and prevents duplicate save', async ({ page }) => {
  const requests = [];
  let listCalls = 0;
  await installHqSession(page);
  await page.route(/^https?:\/\/[^/]+\/api\//, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.pathname === '/api/v1/auth/permissions') return jsonResponse(route, []);
    if (url.pathname === '/api/v1/companies' && request.method() === 'GET') {
      listCalls += 1;
      requests.push({ method: 'GET', authorization: request.headers().authorization, category: url.searchParams.get('category'), queryToken: url.searchParams.get('token') });
      // Keep the initial loading state observable even on fast local machines.
      if (listCalls === 1) await new Promise((resolve) => setTimeout(resolve, 1000));
      return jsonResponse(route, [{ id: 'branch01-uuid', corp_id: 'branch01', corp_code: 'F001', corp_category: '20', name_kr: '가맹점01', ceo_name: '김가맹', tel_no: '02-3456-3456' }]);
    }
    if (url.pathname === '/api/v1/companies' && request.method() === 'POST') {
      requests.push({ method: 'POST', authorization: request.headers().authorization, queryToken: url.searchParams.get('token'), body: request.postDataJSON() });
      await new Promise((resolve) => setTimeout(resolve, 300));
      return jsonResponse(route, { status: 'success', data: [] });
    }
    return jsonResponse(route, { detail: `Unhandled Day 05 API: ${url.pathname}` }, 501);
  });

  await page.goto('/admin/company');
  await expect(page.getByRole('status').filter({ hasText: '가맹점 목록을 불러오는 중입니다.' })).toBeVisible();
  await expect(page.getByRole('table', { name: '가맹점 목록' })).toBeVisible();
  await page.getByRole('row', { name: /branch01/ }).press('Enter');
  await expect(page.getByLabel('업체 ID', { exact: true })).toHaveValue('branch01');
  await expect(page.getByLabel('업체 구분')).toHaveValue('가맹점(Franchise)');

  await page.getByRole('button', { name: '신규 등록' }).click();
  await page.getByLabel('업체 ID', { exact: true }).fill('branch02');
  await page.getByLabel('업체명(KR)').fill('가맹점02');
  await page.getByLabel('비밀번호').fill('1234!');
  await page.getByLabel('전화번호').fill('02-3456-3457');
  await page.getByRole('button', { name: '저장' }).click();
  await expect(page.getByRole('button', { name: '저장 중...' })).toBeDisabled();
  await page.getByRole('button', { name: '저장 중...' }).click({ force: true });
  await expect(page.getByRole('status').filter({ hasText: '가맹점 정보를 저장했습니다.' })).toBeVisible();

  const writes = requests.filter((item) => item.method === 'POST');
  expect(writes).toHaveLength(1);
  expect(writes[0]).toMatchObject({ authorization: 'Bearer day05-e2e-token', queryToken: null });
  expect(writes[0].body).toMatchObject({ corp_id: 'branch02', corp_category: '20' });
  expect(requests.filter((item) => item.method === 'GET').every((item) => item.authorization === 'Bearer day05-e2e-token' && item.category === '20' && item.queryToken === null)).toBe(true);
});

test('D05-E2E-02 keeps supplier input after a visible server error', async ({ page }) => {
  const requests = [];
  await installHqSession(page);
  await page.route(/^https?:\/\/[^/]+\/api\//, async (route) => {
    const request = route.request();
    const url = new URL(request.url());
    if (url.pathname === '/api/v1/auth/permissions') return jsonResponse(route, []);
    if (url.pathname === '/api/v1/companies' && request.method() === 'GET') {
      requests.push({ method: 'GET', authorization: request.headers().authorization, category: url.searchParams.get('category'), queryToken: url.searchParams.get('token') });
      return jsonResponse(route, []);
    }
    if (url.pathname === '/api/v1/companies' && request.method() === 'POST') {
      requests.push({ method: 'POST', authorization: request.headers().authorization, queryToken: url.searchParams.get('token'), body: request.postDataJSON() });
      return jsonResponse(route, { detail: '동일한 공급사 ID가 이미 있습니다.' }, 409);
    }
    return jsonResponse(route, { detail: `Unhandled Day 05 API: ${url.pathname}` }, 501);
  });

  await page.goto('/admin/supplier');
  await expect(page.getByRole('table', { name: '공급사 목록' })).toBeVisible();
  await expect(page.getByText('조회된 공급사가 없습니다.')).toBeVisible();
  await expect(page.getByLabel('업체 구분')).toHaveValue('공급사(Supplier)');
  await page.getByRole('button', { name: '신규 등록' }).click();
  await page.getByLabel('업체 ID', { exact: true }).fill('supplier_01');
  await page.getByLabel('공급사명(KR)').fill('푸다닥');
  await page.getByLabel('비밀번호').fill('supplier01!');
  await page.getByLabel('전화번호').fill('02-4567-4567');
  await page.getByRole('button', { name: '저장' }).click();

  await expect(page.getByRole('alert')).toContainText('동일한 공급사 ID가 이미 있습니다.');
  await expect(page.getByLabel('업체 ID', { exact: true })).toHaveValue('supplier_01');
  const write = requests.find((item) => item.method === 'POST');
  expect(write).toMatchObject({ authorization: 'Bearer day05-e2e-token', queryToken: null });
  expect(write.body).toMatchObject({ corp_id: 'supplier_01', corp_category: '30' });
  expect(requests.find((item) => item.method === 'GET').category).toBe('30');
});

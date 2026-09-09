import { createRouter, createWebHistory } from 'vue-router';
import CompanyMasterView from '../views/admin/CompanyMasterView.vue';
import SupplierRegistrationView from '../views/admin/SupplierRegistrationView.vue';
import PurchaseOrderListView from '../views/store/PurchaseOrderListView.vue';

const routes = [
  { path: '/', redirect: '/admin/company' },
  { path: '/admin/company', component: CompanyMasterView },
  { path: '/admin/supplier', component: SupplierRegistrationView },
  { path: '/store/purchase/order', component: PurchaseOrderListView },
  { path: '/:pathMatch(.*)*', redirect: '/admin/company' },
];

export default createRouter({ history: createWebHistory(), routes });


<template>
  <main class="page">
    <header>
      <p class="eyebrow">Chapter 11</p>
      <h1>주문 승인</h1>
      <p>주문을 승인하고 저장된 주문 상태와 현재 재고를 확인합니다.</p>
    </header>
    <ApproveOrder />
  </main>
</template>

<script>
import ApproveOrder from './components/ApproveOrder.vue'

export default { components: { ApproveOrder } }
</script>

<style>
body { margin: 0; background: #f8f9fa; color: #243444; font-family: system-ui, sans-serif; }
* { box-sizing: border-box; }
.page { max-width: 60rem; margin: auto; padding: 2rem 1rem; }
.eyebrow { color: #526779; font-size: .875rem; }
h1 { margin: .25rem 0; }
header { margin-bottom: 1.5rem; }
</style>

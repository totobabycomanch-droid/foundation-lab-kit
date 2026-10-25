<template>
  <!-- Tailwind CSS가 없어도 깔끔하게 배경과 여백이 들어가도록 인라인 스타일을 적용했습니다 -->
  <div style="min-height: 100vh; background-color: #f3f4f6; padding: 2.5rem 0;">
    <!-- 화면 중앙에 실습 버튼 컴포넌트 출력 -->
    <ApproveOrder />
  </div>
</template>

<script>
import ApproveOrder from './components/ApproveOrder.vue';

export default {
  components: {
    ApproveOrder
  }
}
</script>

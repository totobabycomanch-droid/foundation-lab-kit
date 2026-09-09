<script setup>
import { defineExpose } from 'vue';

const open = () => {
  throw new Error('주소 검색은 Chapter 3 조사 범위에서 실행하지 않습니다.');
};

defineExpose({ open });
</script>

<template><span hidden /></template>


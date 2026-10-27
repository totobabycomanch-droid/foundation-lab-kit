// Learner workspace: exercise 2 adds the confirmed role policy and explanation.
export const ApprovalAction = {
  props: { user: Object, order: Object, busy: Boolean },
  emits: ['approve'],
  template: `<button :disabled="busy" @click="$emit('approve', order.id)">발주 승인</button>`,
};

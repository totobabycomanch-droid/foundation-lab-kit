import { ref, readonly } from '/vendor/vue.js';

// Fixed lab instrument: retain the bytes and key that actually leave the form.
const requestState = ref(null);
const firstState = ref(null);
const replayState = ref(null);
const flightState = ref(0);
export const lastRequest = readonly(requestState);
export const firstResponse = readonly(firstState);
export const replayResponse = readonly(replayState);
export const inFlight = readonly(flightState);

async function transmit(snapshot, replay) {
  flightState.value += 1;
  try {
    const response = await fetch('/api/orders', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Idempotency-Key': snapshot.key },
      body: snapshot.body,
    });
    const body = await response.clone().json().catch(() => null);
    if (requestState.value?.key === snapshot.key) {
      const result = { status: response.status, id: response.ok ? body?.id ?? null : null };
      if (replay) replayState.value = result;
      else firstState.value = result;
    }
    return response;
  } finally {
    flightState.value -= 1;
  }
}

export function sendOrder(order) {
  const snapshot = { key: crypto.randomUUID(), body: JSON.stringify(order) };
  requestState.value = snapshot;
  firstState.value = null;
  replayState.value = null;
  return transmit(snapshot, false);
}

export function repeatLastOrder() {
  if (!requestState.value) throw new Error('먼저 발주를 한 번 저장하세요.');
  replayState.value = null;
  return transmit({ ...requestState.value }, true);
}

export function clearLastRequest() {
  requestState.value = null;
  firstState.value = null;
  replayState.value = null;
}

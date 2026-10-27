// Fixed observer: always show the actual HTTP response, including errors.
export async function send(space, path, method = 'GET', data) {
  const response = await fetch(`/api/${space}${path}`, {
    method,
    credentials: 'same-origin',
    cache: 'no-store',
    headers: data === undefined ? {} : { 'Content-Type': 'application/json' },
    ...(data === undefined ? {} : { body: JSON.stringify(data) }),
  });
  return { status: response.status, body: await response.json() };
}

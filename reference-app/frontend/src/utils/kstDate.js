export const formatKstDate = (value = new Date()) => {
  const parts = new Intl.DateTimeFormat('en-US', {
    timeZone: 'Asia/Seoul',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit'
  }).formatToParts(value);
  const dateParts = Object.fromEntries(parts.map(part => [part.type, part.value]));
  return `${dateParts.year}-${dateParts.month}-${dateParts.day}`;
};

export const oneMonthBefore = (dateText) => {
  const [year, month, day] = dateText.split('-').map(Number);
  const previousMonthLastDay = new Date(Date.UTC(year, month - 1, 0)).getUTCDate();
  return new Date(
    Date.UTC(year, month - 2, Math.min(day, previousMonthLastDay))
  ).toISOString().slice(0, 10);
};

export const daysBefore = (dateText, days) => {
  const [year, month, day] = dateText.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day - days)).toISOString().slice(0, 10);
};

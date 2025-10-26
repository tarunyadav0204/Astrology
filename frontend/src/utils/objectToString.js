export const safeRender = (value) => {
  if (typeof value === 'object' && value !== null) {
    if (value.hasOwnProperty('score') && value.hasOwnProperty('grade')) {
      return `${value.grade} (${value.score})`;
    }
    return JSON.stringify(value);
  }
  return String(value);
};
const CTRL_EXCEPT_NL_TAB = /[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]/g;
const MAX_SUBJECT = 200;
const MAX_BODY = 8000;

export function sanitizeSupportSubject(raw) {
  if (raw == null) return '';
  let s = String(raw).replace(/\x00/g, '');
  s = s.replace(CTRL_EXCEPT_NL_TAB, '');
  s = s.split(/\s+/).join(' ');
  if (s.length > MAX_SUBJECT) s = s.slice(0, MAX_SUBJECT);
  return s.trim();
}

export function sanitizeSupportBody(raw) {
  if (raw == null) return '';
  let s = String(raw).replace(/\x00/g, '');
  s = s.replace(CTRL_EXCEPT_NL_TAB, '');
  if (s.length > MAX_BODY) s = s.slice(0, MAX_BODY);
  return s.trim();
}

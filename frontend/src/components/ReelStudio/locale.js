// Match the mobile language names as well as browser language codes.
export function studioLanguage() {
  const raw=(localStorage.getItem('language') || localStorage.getItem('nextChapterLanguage') || navigator.language || 'en').toLowerCase().split('-')[0];
  return ({english:'en',hindi:'hi',tamil:'ta',telugu:'te',gujarati:'gu',marathi:'mr',german:'de',french:'fr',russian:'ru',chinese:'zh',spanish:'es'})[raw] || raw;
}

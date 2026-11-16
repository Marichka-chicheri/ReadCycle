// Same list as backend/src/common/genres.py — change both together, never rename a code.
export const GENRES = [
  ['classic', 'Класика'],
  ['modern', 'Сучасна проза'],
  ['fantasy', 'Фентезі'],
  ['scifi', 'Наукова фантастика'],
  ['detective', 'Детектив'],
  ['thriller', 'Трилер'],
  ['horror', 'Жахи'],
  ['romance', 'Любовний роман'],
  ['historical', 'Історичний роман'],
  ['young_adult', 'Young Adult'],
  ['poetry', 'Поезія'],
  ['drama', 'Драматургія'],
  ['children', 'Дитяча'],
  ['comics', 'Комікси і графічні романи'],
  ['nonfiction', 'Нон-фікшн'],
  ['biography', 'Біографії та мемуари'],
  ['history', 'Історія'],
  ['philosophy', 'Філософія'],
  ['psychology', 'Психологія'],
  ['science', 'Наука і техніка'],
  ['business', 'Бізнес і саморозвиток'],
  ['religion', 'Релігія і духовність'],
  ['textbook', 'Навчальна література'],
  ['other', 'Інше'],
];

const LABELS = Object.fromEntries(GENRES);
export const genreLabel = (code) => LABELS[code] || code;

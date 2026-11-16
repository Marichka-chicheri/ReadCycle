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

// Same list as backend/src/common/languages.py.
export const LANGUAGES = [
  ['uk', 'Українська'],
  ['en', 'Англійська'],
  ['pl', 'Польська'],
  ['de', 'Німецька'],
  ['fr', 'Французька'],
  ['es', 'Іспанська'],
  ['it', 'Італійська'],
  ['other', 'Інша'],
];
const LANGUAGE_LABELS = Object.fromEntries(LANGUAGES);
export const languageLabel = (code) => LANGUAGE_LABELS[code] || code;

// What the owner wants for a book (backend/src/domain/book.py OFFERS).
export const OFFERS = [
  ['exchange', 'Обміняю', 'хочу щось натомість'],
  ['give', 'Віддам', 'безкоштовно, просто забери'],
];
export const offerLabel = (code) => OFFERS.find(([c]) => c === code)?.[1] || code;

import { GENRES, LANGUAGES } from '../genres.js';

const OFFER_TABS = [
  ['', 'Усі'],
  ['exchange', 'Обміняю'],
  ['give', 'Віддам'],
];

// Filter bar above the oak cabinet: text search, genre, language and offer type.
export default function CatalogFilters({ value, onChange, total }) {
  const set = (key) => (e) => onChange({ ...value, [key]: e.target.value });
  const active = value.q || value.genre || value.language || value.offer;

  return (
    <div className="filters">
      <label className="filters__search">
        <span className="visually-hidden">Пошук</span>
        <svg
          width="18"
          height="18"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.8"
        >
          <circle cx="11" cy="11" r="7" />
          <path d="m20 20-3.5-3.5" />
        </svg>
        <input
          type="search"
          value={value.q}
          onChange={set('q')}
          placeholder="Назва або автор"
          maxLength={100}
        />
      </label>
      <select value={value.genre} onChange={set('genre')} aria-label="Жанр">
        <option value="">Усі жанри</option>
        {GENRES.map(([code, label]) => (
          <option key={code} value={code}>
            {label}
          </option>
        ))}
      </select>
      <select value={value.language} onChange={set('language')} aria-label="Мова">
        <option value="">Будь-яка мова</option>
        {LANGUAGES.map(([code, label]) => (
          <option key={code} value={code}>
            {label}
          </option>
        ))}
      </select>
      <div className="segmented" role="radiogroup" aria-label="Тип">
        {OFFER_TABS.map(([code, label]) => (
          <button
            key={code || 'all'}
            type="button"
            role="radio"
            aria-checked={value.offer === code}
            className={value.offer === code ? 'on' : ''}
            onClick={() => onChange({ ...value, offer: code })}
          >
            {label}
          </button>
        ))}
      </div>
      <div className="filters__meta">
        {total !== null && <span>Знайдено: {total}</span>}
        {active && (
          <button
            type="button"
            className="link"
            onClick={() => onChange({ q: '', genre: '', language: '', offer: '' })}
          >
            Скинути
          </button>
        )}
      </div>
    </div>
  );
}

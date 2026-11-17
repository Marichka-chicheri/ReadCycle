import { GENRES, LANGUAGES } from '../genres.js';

const OFFER_TABS = [
  ['', 'Усі'],
  ['exchange', 'Обміняю'],
  ['give', 'Віддам'],
];

// Filters built into the oak cabinet: engraved-looking fields on a dark wood rail.
export default function CatalogFilters({ value, onChange, total }) {
  const set = (key) => (e) => onChange({ ...value, [key]: e.target.value });
  const active = value.q || value.genre || value.language || value.offer;

  return (
    <div className="rail">
      <label className="rail__field rail__field--search">
        <span className="rail__label">Пошук</span>
        <input
          type="search"
          value={value.q}
          onChange={set('q')}
          placeholder="назва або автор"
          maxLength={100}
        />
      </label>
      <label className="rail__field">
        <span className="rail__label">Жанр</span>
        <select value={value.genre} onChange={set('genre')}>
          <option value="">усі</option>
          {GENRES.map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <label className="rail__field">
        <span className="rail__label">Мова</span>
        <select value={value.language} onChange={set('language')}>
          <option value="">будь-яка</option>
          {LANGUAGES.map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
      </label>
      <div className="rail__field">
        <span className="rail__label">Тип</span>
        <div className="rail__tabs" role="radiogroup" aria-label="Тип">
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
      </div>
      <div className="rail__meta">
        {total !== null && <span>{total} в шафі</span>}
        {active && (
          <button
            type="button"
            onClick={() => onChange({ q: '', genre: '', language: '', offer: '' })}
          >
            скинути
          </button>
        )}
      </div>
    </div>
  );
}

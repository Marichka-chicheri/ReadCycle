import { useState } from 'react';
import { GENRES, LANGUAGES } from '../genres.js';

const KINDS = [
  ['book', 'Конкретна книга', 'знаю назву'],
  ['genre', 'Щось із жанру', 'відкрита до пропозицій'],
];

const EMPTY = { kind: 'book', title: '', author: '', genre: '', language: '', note: '' };

// Add / edit a wishlist entry: either a specific book, or "anything in this genre".
export default function WishForm({
  initial,
  submitLabel = 'Додати в каталог',
  onSubmit,
  secondary,
}) {
  const [data, setData] = useState({ ...EMPTY, ...initial });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (key) => (e) => setData((d) => ({ ...d, [key]: e.target.value }));
  const err = (key) => errors[key] && <span className="field-error">{errors[key]}</span>;
  const isBook = data.kind === 'book';

  const submit = async (e) => {
    e.preventDefault();
    setErrors({});
    setMessage('');
    setBusy(true);
    try {
      await onSubmit(data);
    } catch (error) {
      setErrors(error.fields || {});
      setMessage(error.fields && Object.keys(error.fields).length ? '' : error.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <form onSubmit={submit} className="profile-form" noValidate>
      <div className="offer-toggle" role="radiogroup">
        {KINDS.map(([code, label, hint]) => (
          <button
            key={code}
            type="button"
            role="radio"
            aria-checked={data.kind === code}
            className={`offer-option${data.kind === code ? ' offer-option--on' : ''}`}
            onClick={() => setData((d) => ({ ...d, kind: code }))}
          >
            <strong>{label}</strong>
            <small>{hint}</small>
          </button>
        ))}
      </div>

      {isBook && (
        <>
          <label>
            Назва
            <input value={data.title} onChange={set('title')} maxLength={150} autoFocus />
            {err('title')}
          </label>
          <label>
            <span>
              Автор <span className="optional">необов'язково</span>
            </span>
            <input value={data.author} onChange={set('author')} maxLength={100} />
            {err('author')}
          </label>
        </>
      )}

      <div className="row-2">
        <label>
          <span>Жанр {isBook && <span className="optional">необов'язково</span>}</span>
          <select value={data.genre} onChange={set('genre')}>
            <option value="">{isBook ? '—' : 'Оберіть жанр'}</option>
            {GENRES.map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
          {err('genre')}
        </label>
        <label>
          Мова
          <select value={data.language} onChange={set('language')}>
            <option value="">Будь-яка</option>
            {LANGUAGES.map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
          {err('language')}
        </label>
      </div>

      <label>
        <span>
          Примітка <span className="optional">необов'язково</span>
        </span>
        <textarea
          rows={2}
          maxLength={300}
          value={data.note}
          onChange={set('note')}
          placeholder={isBook ? 'Будь-яке видання, можна вживану…' : 'Щось легке на зиму…'}
        />
        {err('note')}
      </label>

      {(errors.kind || message) && <p className="error">{errors.kind || message}</p>}
      <div className="form-actions">
        <button disabled={busy}>{busy ? 'Зберігаємо…' : submitLabel}</button>
        {secondary}
      </div>
    </form>
  );
}

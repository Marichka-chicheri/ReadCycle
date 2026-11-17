import { useState } from 'react';
import { GENRES, LANGUAGES, OFFERS } from '../genres.js';
import BookLookup from './BookLookup.jsx';
import CoverPicker from './CoverPicker.jsx';

const EMPTY = {
  title: '',
  author: '',
  language: 'uk',
  genre: '',
  offer: 'exchange',
  description: '',
  year: '',
  isbn: '',
  cover_key: '',
  cover_url: '',
  cover_src: '',
};

// Add / edit a book on the user's shelf. Server-side validation messages appear under each field.
export default function BookForm({
  initial,
  submitLabel = 'Поставити на полицю',
  onSubmit,
  secondary,
}) {
  const [data, setData] = useState({ ...EMPTY, ...initial });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [filledFrom, setFilledFrom] = useState('');
  const isNew = !initial?.book_id;

  // Fill the form from a catalogue match; keep what the catalogue does not know
  // and never replace a photo the user uploaded.
  const fill = (b) => {
    setData((d) => ({
      ...d,
      title: b.title || d.title,
      author: b.author || d.author,
      year: b.year || d.year,
      isbn: b.isbn || d.isbn,
      language: b.language || d.language,
      genre: b.genre || d.genre,
      ...(b.cover_url && !d.cover_key ? { cover_url: b.cover_url, cover_src: b.cover_url } : {}),
    }));
    setFilledFrom(b.source);
    setErrors({});
  };

  const set = (key) => (e) => setData((d) => ({ ...d, [key]: e.target.value }));
  const err = (key) => errors[key] && <span className="field-error">{errors[key]}</span>;

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
      {isNew && <BookLookup onPick={fill} />}
      {filledFrom && (
        <p className="ok">
          Заповнено з {filledFrom}. Перевір назву, жанр і мову: каталоги іноді помиляються.
        </p>
      )}
      <label>
        Назва
        <input value={data.title} onChange={set('title')} maxLength={150} />
        {err('title')}
      </label>
      <label>
        Автор
        <input value={data.author} onChange={set('author')} maxLength={100} />
        {err('author')}
      </label>
      <CoverPicker
        title={data.title}
        author={data.author}
        value={data}
        onChange={(cover) => setData((d) => ({ ...d, ...cover }))}
        error={errors.cover}
      />
      <div className="row-2">
        <label>
          Жанр
          <select value={data.genre} onChange={set('genre')}>
            <option value="" disabled>
              Оберіть жанр
            </option>
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
            {LANGUAGES.map(([code, label]) => (
              <option key={code} value={code}>
                {label}
              </option>
            ))}
          </select>
          {err('language')}
        </label>
      </div>
      <div className="row-2">
        <label>
          <span>
            Рік видання <span className="optional">необов'язково</span>
          </span>
          <input
            inputMode="numeric"
            value={data.year}
            onChange={set('year')}
            maxLength={4}
            placeholder="2019"
          />
          {err('year')}
        </label>
        <label>
          <span>
            ISBN <span className="optional">необов'язково</span>
          </span>
          <input value={data.isbn} onChange={set('isbn')} maxLength={17} placeholder="978-…" />
          {err('isbn')}
        </label>
      </div>
      <div className="label">
        Що з нею зробити
        <div className="offer-toggle" role="radiogroup">
          {OFFERS.map(([code, label, hint]) => (
            <button
              key={code}
              type="button"
              role="radio"
              aria-checked={data.offer === code}
              className={`offer-option${data.offer === code ? ' offer-option--on' : ''}`}
              onClick={() => setData((d) => ({ ...d, offer: code }))}
            >
              <strong>{label}</strong>
              <small>{hint}</small>
            </button>
          ))}
        </div>
        {err('offer')}
      </div>
      <label>
        <span>
          Короткий опис <span className="optional">необов'язково</span>
        </span>
        <textarea
          rows={3}
          maxLength={1000}
          value={data.description}
          onChange={set('description')}
          placeholder="Стан книги, видання, чому радиш…"
        />
        {err('description')}
      </label>
      {message && <p className="error">{message}</p>}
      <div className="form-actions">
        <button disabled={busy}>{busy ? 'Зберігаємо…' : submitLabel}</button>
        {secondary}
      </div>
    </form>
  );
}

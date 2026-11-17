import { useState } from 'react';
import { lookupBooks } from '../coverSearch.js';
import { genreLabel, languageLabel } from '../genres.js';
import BookCover from './BookCover.jsx';

// "Find the book" at the top of the add-book form: search the catalogues by title, author or
// ISBN and fill the form from the chosen edition (onPick gets one result).
export default function BookLookup({
  onPick,
  label = 'Знайти книгу й заповнити форму',
  placeholder = 'Назва, автор або ISBN зі зворотного боку книги',
}) {
  const [q, setQ] = useState('');
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [noGoogle, setNoGoogle] = useState(false);

  const search = async () => {
    if (!q.trim()) return;
    setBusy(true);
    setError('');
    try {
      const { books, google } = await lookupBooks(q);
      setResults(books);
      setNoGoogle(!google);
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="lookup">
      <span className="label-text">{label}</span>
      <div className="cover-search">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              e.preventDefault(); // don't submit the book form
              search();
            }
          }}
          placeholder={placeholder}
          maxLength={150}
          autoFocus
        />
        <button type="button" className="btn--small" onClick={search} disabled={busy || !q.trim()}>
          {busy ? 'Шукаємо…' : 'Знайти'}
        </button>
      </div>
      {error && <span className="field-error">{error}</span>}
      {results && noGoogle && (
        <span className="muted cover-picker__status">
          Google Books не підключено (немає ключа), тому шукаємо лише в Open Library, де майже немає
          українських видань.
        </span>
      )}

      {results && (
        <ul className="lookup__results">
          {results.length === 0 && (
            <li className="muted">Нічого не знайшлося. Заповни форму вручну нижче.</li>
          )}
          {results.map((b, i) => (
            <li key={`${b.source}-${i}`}>
              <button
                type="button"
                className="lookup__item"
                onClick={() => {
                  onPick(b);
                  setResults(null);
                }}
              >
                <span className="lookup__cover">
                  <BookCover title={b.title} author={b.author} src={b.cover_url} size="mini" />
                </span>
                <span className="lookup__text">
                  <strong>{b.title}</strong>
                  <span>{b.author || 'автор невідомий'}</span>
                  <small>
                    {[
                      b.year,
                      b.language && languageLabel(b.language),
                      b.genre && genreLabel(b.genre),
                      b.source,
                    ]
                      .filter(Boolean)
                      .join(' · ')}
                  </small>
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

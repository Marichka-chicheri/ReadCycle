import { useRef, useState } from 'react';
import { searchCovers } from '../coverSearch.js';
import { uploadPhoto } from '../photos.js';
import BookCover from './BookCover.jsx';

// Cover of a book in the add/edit form: find one by title & author, upload a photo, or keep
// the drawn cloth cover. `value` = { cover_key, cover_url, cover_src }; onChange gets the same.
export default function CoverPicker({ title, author, value, onChange, error }) {
  const [results, setResults] = useState(null);
  const [status, setStatus] = useState('');
  const [busy, setBusy] = useState(false);
  const fileInput = useRef(null);
  const hasCover = Boolean(value.cover_key || value.cover_url);

  const search = async () => {
    setBusy(true);
    setStatus('Шукаємо обкладинки…');
    try {
      const found = await searchCovers(title, author);
      setResults(found);
      setStatus(found.length ? 'Обери обкладинку, що підходить' : '');
    } catch {
      setStatus('Пошук зараз недоступний, спробуй пізніше або завантаж фото');
    } finally {
      setBusy(false);
    }
  };

  const upload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setBusy(true);
    setStatus('Завантажуємо фото…');
    try {
      const { key, preview } = await uploadPhoto('cover', file);
      onChange({ cover_key: key, cover_url: '', cover_src: preview });
      setResults(null);
      setStatus('');
    } catch (err) {
      setStatus(err.message);
    } finally {
      setBusy(false);
    }
  };

  const pick = (c) => {
    onChange({ cover_key: '', cover_url: c.src, cover_src: c.src });
    setResults(null);
    setStatus('');
  };

  return (
    <div className="cover-picker">
      <div className="cover-picker__row">
        <div className="cover-picker__preview">
          <BookCover title={title || 'Назва'} author={author} src={value.cover_src} />
        </div>
        <div className="cover-picker__actions">
          <span className="label-text">Обкладинка</span>
          <button
            type="button"
            className="btn--ghost btn--small"
            onClick={search}
            disabled={busy || !title.trim()}
            title={title.trim() ? '' : 'Спершу впиши назву'}
          >
            Знайти за назвою
          </button>
          <button
            type="button"
            className="btn--ghost btn--small"
            onClick={() => fileInput.current?.click()}
            disabled={busy}
          >
            Завантажити фото
          </button>
          <input ref={fileInput} type="file" accept="image/*" hidden onChange={upload} />
          {hasCover && (
            <button
              type="button"
              className="link"
              onClick={() => onChange({ cover_key: '', cover_url: '', cover_src: '' })}
            >
              Прибрати, лишити палітурку
            </button>
          )}
          {status && <span className="muted cover-picker__status">{status}</span>}
          {error && <span className="field-error">{error}</span>}
        </div>
      </div>

      {results && (
        <div className="cover-results">
          {results.length === 0 ? (
            <p className="muted">
              Нічого не знайшлося. Спробуй уточнити назву, або сфотографуй свій примірник.
            </p>
          ) : (
            results.map((c) => (
              <button
                key={c.src}
                type="button"
                className={`cover-result${value.cover_url === c.src ? ' cover-result--on' : ''}`}
                onClick={() => pick(c)}
                title={[c.title, c.author, c.year].filter(Boolean).join(' · ')}
              >
                <img src={c.src} alt={c.title} loading="lazy" />
                <small>{c.year || c.source}</small>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
}

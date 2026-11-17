import { useRef, useState } from 'react';
import { uploadPhoto } from '../photos.js';

// Profile photo in the form: an oval portrait frame, "upload" and "remove".
// value = { avatar_key, avatar_src }; onChange gets the same shape.
export default function AvatarField({ name, value, onChange, error }) {
  const [busy, setBusy] = useState(false);
  const [status, setStatus] = useState('');
  const fileInput = useRef(null);

  const upload = async (e) => {
    const file = e.target.files?.[0];
    e.target.value = '';
    if (!file) return;
    setBusy(true);
    setStatus('Завантажуємо…');
    try {
      const { key, preview } = await uploadPhoto('avatar', file);
      onChange({ avatar_key: key, avatar_src: preview });
      setStatus('');
    } catch (err) {
      setStatus(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="avatar-field">
      <Portrait src={value.avatar_src} name={name} />
      <div className="avatar-field__actions">
        <span className="label-text">
          Фото профілю <span className="optional">необов'язково</span>
        </span>
        <div className="form-actions">
          <button
            type="button"
            className="btn--ghost btn--small"
            onClick={() => fileInput.current?.click()}
            disabled={busy}
          >
            {value.avatar_key ? 'Змінити фото' : 'Завантажити фото'}
          </button>
          {value.avatar_key && (
            <button
              type="button"
              className="link"
              onClick={() => onChange({ avatar_key: '', avatar_src: '' })}
            >
              Прибрати
            </button>
          )}
        </div>
        <input ref={fileInput} type="file" accept="image/*" hidden onChange={upload} />
        {status && <span className="muted">{status}</span>}
        {error && <span className="field-error">{error}</span>}
      </div>
    </div>
  );
}

// An oval portrait in a thin double frame, or an empty frame with the initial.
export function Portrait({ src, name = '', size = 'md' }) {
  return (
    <span className={`portrait portrait--${size}`}>
      {src ? (
        <img src={src} alt={name} />
      ) : (
        <span className="portrait__empty">{name.trim()[0]?.toUpperCase() || '·'}</span>
      )}
    </span>
  );
}

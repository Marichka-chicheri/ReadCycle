import { useState } from 'react';
import GenrePicker from './GenrePicker.jsx';

const EMPTY = {
  display_name: '',
  telegram: '',
  phone: '',
  age: '',
  about: '',
  favorite_genres: [],
};

// Profile form, split into two sections so onboarding can show them as two steps:
//   'contacts' — name/nickname + Telegram/phone (required)
//   'about'    — age, a few words, favourite genres (optional)
// It always submits every editable field (PUT /profile replaces them all), including the ones
// of a hidden section, taken from `initial`.
export default function ProfileForm({
  initial,
  sections = ['contacts', 'about'],
  submitLabel = 'Зберегти',
  onSubmit,
  secondary,
}) {
  const [data, setData] = useState({ ...EMPTY, ...stripNulls(initial) });
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);

  const set = (key) => (e) => setData((d) => ({ ...d, [key]: e.target.value }));

  const submit = async (e) => {
    e.preventDefault();
    setErrors({});
    setMessage('');
    setBusy(true);
    try {
      await onSubmit({ ...data, age: data.age === '' ? null : Number(data.age) });
    } catch (err) {
      setErrors(err.fields || {});
      setMessage(err.fields && Object.keys(err.fields).length ? '' : err.message);
    } finally {
      setBusy(false);
    }
  };

  const err = (key) => errors[key] && <span className="field-error">{errors[key]}</span>;

  return (
    <form onSubmit={submit} className="profile-form" noValidate>
      {sections.includes('contacts') && (
        <fieldset>
          <label>
            Ім'я або нік
            <input
              value={data.display_name}
              onChange={set('display_name')}
              placeholder="Як тебе підписати на полиці"
              maxLength={60}
              autoFocus
            />
            {err('display_name')}
          </label>
          <div className={`contacts${errors.contacts ? ' contacts--error' : ''}`}>
            <p className="contacts__hint">Контакти для обміну: вкажи хоча б один</p>
            <div className="row-2">
              <label>
                Telegram
                <span className="input-prefix">
                  <span>@</span>
                  <input
                    value={data.telegram}
                    onChange={set('telegram')}
                    placeholder="nickname"
                    autoComplete="off"
                  />
                </span>
                {err('telegram')}
              </label>
              <label>
                Телефон
                <input
                  type="tel"
                  value={data.phone}
                  onChange={set('phone')}
                  placeholder="+380 97 123 45 67"
                />
                {err('phone')}
              </label>
            </div>
            {err('contacts')}
          </div>
        </fieldset>
      )}

      {sections.includes('about') && (
        <fieldset>
          <div className="row-2 row-2--narrow">
            <label>
              Вік
              <input
                type="number"
                min={14}
                max={99}
                value={data.age}
                onChange={set('age')}
                placeholder="—"
              />
              {err('age')}
            </label>
          </div>
          <label>
            Кілька слів про себе
            <textarea
              rows={4}
              maxLength={600}
              value={data.about}
              onChange={set('about')}
              placeholder="Що любиш читати, що шукаєш, як зручніше зустрітися на кампусі…"
            />
            {err('about')}
          </label>
          <div className="label">
            Улюблені жанри
            <GenrePicker
              value={data.favorite_genres}
              onChange={(favorite_genres) => setData((d) => ({ ...d, favorite_genres }))}
            />
            {err('favorite_genres')}
          </div>
        </fieldset>
      )}

      {message && <p className="error">{message}</p>}
      <div className="form-actions">
        <button disabled={busy}>{busy ? 'Зберігаємо…' : submitLabel}</button>
        {secondary}
      </div>
    </form>
  );
}

function stripNulls(obj = {}) {
  return Object.fromEntries(Object.entries(obj || {}).filter(([, v]) => v !== null));
}

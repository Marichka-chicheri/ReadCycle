import { useState } from 'react';
import { Shelf } from '../components/Bookshelf.jsx';
import ProfileForm from '../components/ProfileForm.jsx';
import { genreLabel } from '../genres.js';
import { useProfile } from '../ProfileContext.jsx';

function initials(name = '') {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0].toUpperCase())
    .join('');
}

function Contacts({ profile }) {
  return (
    <ul className="contact-list">
      {profile.telegram && (
        <li>
          <span>Telegram</span>
          <a href={`https://t.me/${profile.telegram}`} target="_blank" rel="noreferrer">
            @{profile.telegram}
          </a>
        </li>
      )}
      {profile.phone && (
        <li>
          <span>Телефон</span>
          <a href={`tel:${profile.phone}`}>{profile.phone}</a>
        </li>
      )}
      <li>
        <span>Пошта</span>
        {profile.email}
      </li>
    </ul>
  );
}

// The signed-in user's own profile: identity card, details, and (from stage 3) their shelves.
export default function Profile() {
  const { profile, save } = useProfile();
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);

  return (
    <section className="profile">
      <div className="profile__top">
        <aside className="card card--wine identity">
          <div className="monogram" aria-hidden="true">
            {initials(profile.display_name)}
          </div>
          <h1>{profile.display_name}</h1>
          {profile.age && <p className="identity__meta">{profile.age} р.</p>}
          <Contacts profile={profile} />
        </aside>

        <div className="card profile__details">
          {editing ? (
            <>
              <span className="eyebrow">Редагування профілю</span>
              <ProfileForm
                initial={profile}
                onSubmit={async (data) => {
                  await save(data);
                  setEditing(false);
                  setSaved(true);
                }}
                secondary={
                  <button type="button" className="btn--ghost" onClick={() => setEditing(false)}>
                    Скасувати
                  </button>
                }
              />
            </>
          ) : (
            <>
              <div className="profile__head">
                <span className="eyebrow">Про мене</span>
                <button
                  className="btn--ghost btn--small"
                  onClick={() => {
                    setSaved(false);
                    setEditing(true);
                  }}
                >
                  Редагувати
                </button>
              </div>
              {saved && <p className="ok">Профіль збережено.</p>}
              {profile.about ? (
                <p className="profile__about">{profile.about}</p>
              ) : (
                <p className="muted">
                  Тут поки порожньо. Додай кілька слів про себе: що любиш читати, що шукаєш.
                </p>
              )}
              <span className="eyebrow">Улюблені жанри</span>
              {profile.favorite_genres.length ? (
                <div className="chips">
                  {profile.favorite_genres.map((g) => (
                    <span key={g} className="chip chip--static">
                      {genreLabel(g)}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="muted">Ще не обрано.</p>
              )}
            </>
          )}
        </div>
      </div>

      <div className="section-head">
        <h2>Моя полиця</h2>
        <span className="muted">Книги, які готова віддати або обміняти</span>
      </div>
      <div className="wall">
        <div className="wall-shelves">
          <Shelf variant="wall" empty="Скоро тут з’являться твої книги" />
        </div>
      </div>
    </section>
  );
}

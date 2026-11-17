import { genreLabel } from '../genres.js';
import { Portrait } from './AvatarField.jsx';

// The ex-libris card: photo (if any), name, age, a fleuron and contacts.
export function IdentityCard({ profile }) {
  return (
    <aside className="card identity">
      {profile.avatar_src && (
        <Portrait src={profile.avatar_src} name={profile.display_name} size="lg" />
      )}
      <h1>{profile.display_name}</h1>
      {profile.age && <p className="identity__meta">{profile.age} р.</p>}
      <span className="identity__fleuron" aria-hidden="true">
        ❦
      </span>
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
          <a href={`mailto:${profile.email}`}>{profile.email}</a>
        </li>
      </ul>
    </aside>
  );
}

// "About me" text and favourite genres. `emptyAbout` is shown when there is no text.
export function AboutBlock({ profile, emptyAbout, title = 'Про мене', action }) {
  return (
    <>
      <div className="profile__head">
        <span className="eyebrow">{title}</span>
        {action}
      </div>
      {profile.about ? (
        <p className="profile__about">{profile.about}</p>
      ) : (
        <p className="muted">{emptyAbout}</p>
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
  );
}

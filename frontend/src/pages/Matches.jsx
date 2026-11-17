import { useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { Portrait } from '../components/AvatarField.jsx';
import BookCover from '../components/BookCover.jsx';
import { genreLabel } from '../genres.js';

const KINDS = {
  mutual: { label: 'Взаємний обмін', subject: 'взаємний обмін' },
  for_me: { label: 'Має для тебе', subject: 'книга з твого вішліста' },
  for_them: { label: 'Шукає твоє', subject: 'шукає книгу з твоєї полиці' },
};

const TODAY = new Date().toLocaleDateString('uk-UA', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
});

function reasonText(m) {
  const base = m.by === 'title' ? 'з вішліста' : `жанр: ${genreLabel(m.wish.genre).toLowerCase()}`;
  return m.book.offer === 'give' ? `${base}; віддає безкоштовно` : base;
}

// One book in the letter: a small cover "pasted" on the page with tape, and a typed line.
function LetterLine({ m }) {
  return (
    <li>
      <span className="letter__photo">
        <BookCover title={m.book.title} author={m.book.author} src={m.book.cover_src} size="mini" />
      </span>
      <span className="letter__text">
        <span className="letter__book">{m.book.title}</span>
        {m.book.author && <span className="letter__author">{m.book.author}</span>}
        <span className={`letter__reason${m.book.offer === 'give' ? ' letter__reason--free' : ''}`}>
          {reasonText(m)}
        </span>
      </span>
    </li>
  );
}

// A match, typed like a letter on a typewriter.
function MatchCard({ match }) {
  const { user } = match;
  return (
    <article className="letter">
      <p className="letter__date">ReadCycle, {TODAY}</p>
      {user.avatar_src && (
        <span className="letter__portrait">
          <Portrait src={user.avatar_src} name={user.display_name} size="sm" />
        </span>
      )}
      <p className="letter__meta">
        Від: <strong>{user.display_name}</strong>
        <br />
        Тема: {KINDS[match.kind].subject}
      </p>
      {user.about && <p className="letter__about">«{user.about}»</p>}

      {match.they_have.length > 0 && (
        <>
          <p className="letter__heading">Має для тебе:</p>
          <ul className="letter__list">
            {match.they_have.map((m) => (
              <LetterLine key={m.book.book_id} m={m} />
            ))}
          </ul>
        </>
      )}
      {match.they_want.length > 0 && (
        <>
          <p className="letter__heading">Шукає з твоєї полиці:</p>
          <ul className="letter__list">
            {match.they_want.map((m) => (
              <LetterLine key={m.book.book_id} m={m} />
            ))}
          </ul>
        </>
      )}

      <Link to={`/u/${user.user_id}`} className="letter__link">
        → профіль і контакти
      </Link>
    </article>
  );
}

// "Find an exchange": runs the matching on demand and lists people, best matches first.
export default function Matches() {
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  const search = async () => {
    setBusy(true);
    setError('');
    try {
      setResult(await api('/matches'));
    } catch (e) {
      setError(e.message);
    } finally {
      setBusy(false);
    }
  };

  const nothingToMatch = result && result.my_books === 0 && result.my_wishes === 0;
  const groups = result
    ? ['mutual', 'for_me', 'for_them']
        .map((k) => [k, result.matches.filter((m) => m.kind === k)])
        .filter(([, list]) => list.length)
    : [];

  return (
    <section className="matches">
      <header className="page-intro">
        <span className="eyebrow">Обмін</span>
        <h1>З ким помінятися книгами</h1>
        <p>
          ReadCycle порівнює твою полицю та вішліст з полицями й вішлістами інших студентів: спершу
          ті, з ким можливий взаємний обмін, далі ті, у кого є книга для тебе, і ті, кому потрібна
          твоя.
        </p>
        <button className="match-button" onClick={search} disabled={busy}>
          {busy ? 'Шукаємо…' : result ? 'Шукати знову' : 'Знайти обмін'}
        </button>
      </header>

      {error && <p className="error">Не вдалося знайти збіги: {error}</p>}

      {nothingToMatch && (
        <div className="card narrow">
          <p>Щоб знайти пару, додай хоча б одну книгу на полицю або картку у вішліст.</p>
          <Link to="/profile" className="btn" style={{ alignSelf: 'flex-start' }}>
            До моєї полиці
          </Link>
        </div>
      )}

      {result && !nothingToMatch && result.matches.length === 0 && (
        <div className="card narrow">
          <p>
            Поки що збігів немає. Додай більше книг або бажань, наприклад загальне «щось із жанру»,
            і зазирни пізніше: нові книги з'являються щодня.
          </p>
        </div>
      )}

      {groups.map(([kind, list]) => (
        <div key={kind} className="match-group">
          <div className="section-head">
            <h2>{KINDS[kind].label}</h2>
            <span className="muted">{list.length}</span>
          </div>
          <div className="letters">
            {list.map((m) => (
              <MatchCard key={m.user.user_id} match={m} />
            ))}
          </div>
        </div>
      ))}
    </section>
  );
}

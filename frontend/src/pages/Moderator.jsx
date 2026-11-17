import { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';
import { useDialogs } from '../components/Dialogs.jsx';
import { REPORT_REASONS } from '../genres.js';

const reasonLabel = (code) => REPORT_REASONS.find(([c]) => c === code)?.[1] || code;
const day = (iso) => (iso ? new Date(iso).toLocaleDateString('uk-UA') : '');

// Moderator page: open complaints (most complained first) and suspended accounts.
// Reachable only for emails on the server's moderator list; the API checks it on every call.
export default function Moderator() {
  const [tab, setTab] = useState('reports');
  return (
    <section className="profile">
      <div className="section-head">
        <h2>Модерація</h2>
        <span className="muted">Скарги студентів і заблоковані акаунти</span>
      </div>
      <div className="mod-tabs" role="tablist">
        <button
          role="tab"
          aria-selected={tab === 'reports'}
          className={tab === 'reports' ? '' : 'btn--ghost'}
          onClick={() => setTab('reports')}
        >
          Скарги
        </button>
        <button
          role="tab"
          aria-selected={tab === 'bans'}
          className={tab === 'bans' ? '' : 'btn--ghost'}
          onClick={() => setTab('bans')}
        >
          Заблоковані
        </button>
      </div>
      {tab === 'reports' ? <Reports /> : <Bans />}
    </section>
  );
}

function Reports() {
  const [groups, setGroups] = useState(null);
  const [error, setError] = useState('');
  const { confirm, notify } = useDialogs();

  const load = useCallback(
    () =>
      api('/mod/reports')
        .then((r) => setGroups(r.groups))
        .catch((e) => setError(e.message)),
    [],
  );
  useEffect(() => {
    load();
  }, [load]);

  // `ask`: { title, message, confirmLabel } of the confirmation dialog
  const resolve = async (g, action, ask) => {
    if (!(await confirm({ danger: action !== 'dismiss', ...ask }))) return;
    try {
      await api('/mod/reports/resolve', {
        method: 'POST',
        body: JSON.stringify({ target_type: g.target_type, target_id: g.target_id, action }),
      });
      await load();
    } catch (e) {
      notify(`Не вдалося: ${e.message}`);
    }
  };

  if (error) return <p className="error">{error}</p>;
  if (!groups) return <p className="loading">Завантажуємо скарги…</p>;
  if (!groups.length) return <p className="card mod-empty">Нових скарг немає.</p>;

  return (
    <div className="mod-groups">
      {groups.map((g) => {
        const isBook = g.target_type === 'book';
        return (
          <article key={`${g.target_type}:${g.target_id}`} className="card mod-group">
            <header className="mod-group__head">
              <div>
                <span className="eyebrow">{isBook ? 'Книга' : 'Користувач'}</span>
                <h3>{isBook ? `«${g.title}»` : g.owner_name}</h3>
                <p className="muted">
                  {isBook && (
                    <>
                      З полиці: <Link to={`/u/${g.owner_id}`}>{g.owner_name}</Link> ·{' '}
                    </>
                  )}
                  {!isBook && <Link to={`/u/${g.owner_id}`}>Відкрити профіль</Link>}
                  {g.owner_banned && <strong className="mod-banned"> · акаунт заблоковано</strong>}
                </p>
              </div>
              <span className="mod-count" title="Скарг">
                {g.count}
              </span>
            </header>
            <ul className="mod-reasons">
              {g.reports.map((r, i) => (
                <li key={i}>
                  <strong>{reasonLabel(r.reason)}</strong>{' '}
                  <span className="muted">{day(r.created_at)}</span>
                  {r.comment && <p>{r.comment}</p>}
                </li>
              ))}
            </ul>
            <div className="form-actions">
              <button
                className="btn--ghost btn--small"
                onClick={() =>
                  resolve(g, 'dismiss', {
                    title: `Зняти всі скарги на «${g.owner_name}»?`,
                    message: 'Зі списку зникнуть усі скарги на цього студента і на його книги.',
                    confirmLabel: 'Зняти скарги',
                  })
                }
              >
                Зняти скарги
              </button>
              {isBook && g.book_exists && (
                <button
                  className="btn--small"
                  onClick={() =>
                    resolve(g, 'remove_book', {
                      title: `Видалити «${g.title}» з полиці?`,
                      message: 'Книга зникне в усіх, скарги на неї закриються.',
                      confirmLabel: 'Видалити книгу',
                    })
                  }
                >
                  Видалити книгу
                </button>
              )}
              {!g.owner_banned && (
                <button
                  className="btn--small"
                  onClick={() =>
                    resolve(g, 'ban_user', {
                      title: `Заблокувати акаунт «${g.owner_name}»?`,
                      message:
                        'Книги й профіль зникнуть для всіх, змінювати щось студент не зможе. Усі скарги на нього закриються. Розблокувати можна у вкладці «Заблоковані».',
                      confirmLabel: 'Заблокувати',
                    })
                  }
                >
                  Заблокувати акаунт
                </button>
              )}
            </div>
          </article>
        );
      })}
    </div>
  );
}

function Bans() {
  const [bans, setBans] = useState(null);
  const [error, setError] = useState('');
  const { confirm, notify } = useDialogs();

  useEffect(() => {
    api('/mod/bans')
      .then((r) => setBans(r.bans))
      .catch((e) => setError(e.message));
  }, []);

  const unban = async (b) => {
    if (
      !(await confirm({ title: `Розблокувати «${b.display_name}»?`, confirmLabel: 'Розблокувати' }))
    )
      return;
    try {
      await api(`/mod/bans/${encodeURIComponent(b.user_id)}`, { method: 'DELETE' });
      setBans((list) => list.filter((x) => x.user_id !== b.user_id));
    } catch (e) {
      notify(`Не вдалося: ${e.message}`);
    }
  };

  if (error) return <p className="error">{error}</p>;
  if (!bans) return <p className="loading">Завантажуємо…</p>;
  if (!bans.length) return <p className="card mod-empty">Заблокованих акаунтів немає.</p>;

  return (
    <ul className="card mod-list">
      {bans.map((b) => (
        <li key={b.user_id} className="mod-row">
          <span>
            <Link to={`/u/${b.user_id}`}>{b.display_name}</Link>
            <span className="muted">
              {' '}
              · {day(b.created_at)}
              {b.reason && ` · ${b.reason}`}
            </span>
          </span>
          <button className="btn--ghost btn--small" onClick={() => unban(b)}>
            Розблокувати
          </button>
        </li>
      ))}
    </ul>
  );
}

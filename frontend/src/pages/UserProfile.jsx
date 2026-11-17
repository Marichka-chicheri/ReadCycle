import { useEffect, useState } from 'react';
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom';
import { api } from '../api.js';
import BookDetails from '../components/BookDetails.jsx';
import { Shelf, chunk } from '../components/Bookshelf.jsx';
import CatalogCard from '../components/CatalogCard.jsx';
import { AboutBlock, IdentityCard } from '../components/Identity.jsx';
import Modal from '../components/Modal.jsx';
import ReportForm from '../components/ReportForm.jsx';
import { useProfile } from '../ProfileContext.jsx';

const PER_SHELF = 18;

// Another student's profile: contacts, their shelf and their wishlist (read-only).
export default function UserProfile() {
  const { id } = useParams();
  const { profile: me } = useProfile();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [open, setOpen] = useState(null);
  const [reporting, setReporting] = useState(false);

  useEffect(() => {
    setData(null);
    setError('');
    api(`/users/${encodeURIComponent(id)}`)
      .then(setData)
      .catch((e) => setError(e.status === 404 ? 'Такого профілю немає.' : e.message));
  }, [id]);

  if (me && id === me.user_id) return <Navigate to="/profile" replace />;
  if (error)
    return (
      <div className="card narrow">
        <p className="error">{error}</p>
        <Link to="/">← До шафи</Link>
      </div>
    );
  if (!data) return <p className="loading">Відкриваємо профіль…</p>;

  const { profile, books, wishes } = data;
  const shelves = books.length ? chunk(books, PER_SHELF) : [[]];

  return (
    <section className="profile">
      <button
        type="button"
        className="back-link"
        onClick={() => (window.history.length > 1 ? navigate(-1) : navigate('/'))}
      >
        ← Назад
      </button>
      <div className="profile__top">
        <IdentityCard profile={profile} />
        <div className="card profile__details">
          <AboutBlock profile={profile} emptyAbout="Про себе нічого не написано." />
          <p className="contact-hint">
            Напиши в Telegram, подзвони чи надішли листа: домовтеся, які книги обміняти і де
            зустрітися на кампусі.
          </p>
        </div>
      </div>

      <div className="section-head">
        <h2>Полиця</h2>
        <span className="muted">Книги, які віддає або обмінює</span>
      </div>
      <div className="wall">
        <div className="wall-shelves">
          {shelves.map((row, i) => (
            <Shelf
              key={i}
              variant="wall"
              books={row}
              empty="Поки що полиця порожня"
              onBookClick={(book) => setOpen(book)}
            />
          ))}
        </div>
      </div>

      <div className="section-head section-head--spaced">
        <h2>Вішліст</h2>
        <span className="muted">Що шукає</span>
      </div>
      <div className="drawer">
        <div className="drawer__bed">
          {wishes.length ? (
            wishes.map((w, i) => <CatalogCard key={w.wish_id} wish={w} number={i + 1} />)
          ) : (
            <p className="drawer__empty">Вішліст порожній</p>
          )}
        </div>
        <div className="drawer__front">
          <span className="drawer__label">Вішліст</span>
          <span className="drawer__pull" aria-hidden="true" />
        </div>
      </div>

      <p className="report-footer">
        <button type="button" className="link report-link" onClick={() => setReporting(true)}>
          Поскаржитись на цього користувача
        </button>
      </p>

      {open && (
        <Modal onClose={() => setOpen(null)} wide>
          <BookDetails book={open} />
        </Modal>
      )}

      {reporting && (
        <Modal title="Скарга на користувача" onClose={() => setReporting(false)}>
          <ReportForm
            subject={profile.display_name}
            target={{ target_type: 'user', target_id: id }}
            onDone={() => setReporting(false)}
          />
        </Modal>
      )}
    </section>
  );
}

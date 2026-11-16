import { useEffect, useState } from 'react';
import { api } from '../api.js';
import CatalogCard from './CatalogCard.jsx';
import Modal from './Modal.jsx';
import WishForm from './WishForm.jsx';

// The user's wishlist in the profile: an oak card-catalogue drawer full of typed cards.
export default function Wishlist() {
  const [wishes, setWishes] = useState(null);
  const [error, setError] = useState('');
  // dialog: null | { mode: 'add' } | { mode: 'edit', wish }
  const [dialog, setDialog] = useState(null);

  useEffect(() => {
    api('/my/wishes')
      .then(({ wishes }) => setWishes(wishes))
      .catch((e) => setError(e.message));
  }, []);

  const close = () => setDialog(null);

  const add = async (data) => {
    const { wish } = await api('/my/wishes', { method: 'POST', body: JSON.stringify(data) });
    setWishes((list) => [...list, wish]);
    close();
  };

  const update = async (data) => {
    const { wish } = await api(`/my/wishes/${dialog.wish.wish_id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    setWishes((list) => list.map((w) => (w.wish_id === wish.wish_id ? wish : w)));
    close();
  };

  const remove = async (wish) => {
    try {
      await api(`/my/wishes/${wish.wish_id}`, { method: 'DELETE' });
      setWishes((list) => list.filter((w) => w.wish_id !== wish.wish_id));
      close();
    } catch (e) {
      window.alert(`Не вдалося видалити: ${e.message}`);
    }
  };

  return (
    <>
      <div className="section-head section-head--spaced">
        <h2>Вішліст</h2>
        <span className="muted">Книги, які шукаю, або жанри, з яких радо щось візьму</span>
      </div>

      {error && <p className="error">Не вдалося завантажити вішліст: {error}</p>}

      <div className="drawer">
        <div className="drawer__bed">
          {wishes?.map((w, i) => (
            <CatalogCard
              key={w.wish_id}
              wish={w}
              number={i + 1}
              onClick={() => setDialog({ mode: 'edit', wish: w })}
            />
          ))}
          {wishes !== null && (
            <button
              type="button"
              className="catalog-card catalog-card--new"
              onClick={() => setDialog({ mode: 'add' })}
            >
              <span className="catalog-card__plus">+</span>
              <span>Нова картка</span>
            </button>
          )}
        </div>
        <div className="drawer__front">
          <span className="drawer__label">Вішліст</span>
          <span className="drawer__pull" aria-hidden="true" />
        </div>
      </div>

      {dialog?.mode === 'add' && (
        <Modal title="Нова картка у вішлісті" onClose={close}>
          <WishForm onSubmit={add} />
        </Modal>
      )}
      {dialog?.mode === 'edit' && (
        <Modal title="Картка вішліста" onClose={close}>
          <WishForm
            initial={dialog.wish}
            submitLabel="Зберегти"
            onSubmit={update}
            secondary={
              <button type="button" className="btn--ghost" onClick={() => remove(dialog.wish)}>
                Видалити картку
              </button>
            }
          />
        </Modal>
      )}
    </>
  );
}

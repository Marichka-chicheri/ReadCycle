import { useEffect, useState } from 'react';
import { api } from '../api.js';
import BookDetails from './BookDetails.jsx';
import BookForm from './BookForm.jsx';
import { Shelf, chunk } from './Bookshelf.jsx';
import Modal from './Modal.jsx';

const PER_SHELF = 18;

// The user's own library in the profile: wall shelves with their books, add / view / edit / delete.
export default function MyShelf() {
  const [books, setBooks] = useState(null);
  const [error, setError] = useState('');
  // dialog: null | { mode: 'add' } | { mode: 'view', book } | { mode: 'edit', book }
  const [dialog, setDialog] = useState(null);

  const load = () =>
    api('/my/books')
      .then(({ books }) => setBooks(books))
      .catch((e) => setError(e.message));

  useEffect(() => {
    load();
  }, []);

  const close = () => setDialog(null);

  const add = async (data) => {
    const { book } = await api('/my/books', { method: 'POST', body: JSON.stringify(data) });
    setBooks((list) => [...list, book]);
    close();
  };

  const update = async (data) => {
    const { book } = await api(`/my/books/${dialog.book.book_id}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    });
    setBooks((list) => list.map((b) => (b.book_id === book.book_id ? book : b)));
    setDialog({ mode: 'view', book });
  };

  const remove = async (book) => {
    if (!window.confirm(`Прибрати «${book.title}» з полиці?`)) return;
    try {
      await api(`/my/books/${book.book_id}`, { method: 'DELETE' });
      setBooks((list) => list.filter((b) => b.book_id !== book.book_id));
      close();
    } catch (e) {
      window.alert(`Не вдалося видалити: ${e.message}`);
    }
  };

  const shelves = books && books.length ? chunk(books, PER_SHELF) : [[]];
  const giveCount = books?.filter((b) => b.offer === 'give').length || 0;

  return (
    <>
      <div className="section-head">
        <h2>Моя полиця</h2>
        <span className="muted">
          {books === null
            ? 'Завантаження…'
            : `${books.length} ${plural(books.length, 'книга', 'книги', 'книг')}` +
              (giveCount ? ` · ${giveCount} віддаю безкоштовно` : '')}
        </span>
        <button
          className="btn--cream section-head__action"
          onClick={() => setDialog({ mode: 'add' })}
        >
          + Додати книгу
        </button>
      </div>

      {error && <p className="error">Не вдалося завантажити книги: {error}</p>}

      <div className="wall">
        <div className="wall-shelves">
          {shelves.map((row, i) => (
            <Shelf
              key={i}
              variant="wall"
              books={row}
              empty={
                books === null ? '' : 'Тут поки порожньо. Додай першу книгу, яку готова віддати.'
              }
              onBookClick={(book) => setDialog({ mode: 'view', book })}
            />
          ))}
        </div>
        {books?.length > 0 && (
          <p className="wall__legend">
            <span className="legend-ribbon" aria-hidden="true" /> закладка — віддаю безкоштовно ·
            натисни на корінець, щоб відкрити книгу
          </p>
        )}
      </div>

      {dialog?.mode === 'add' && (
        <Modal title="Нова книга на полиці" onClose={close}>
          <BookForm onSubmit={add} />
        </Modal>
      )}

      {dialog?.mode === 'edit' && (
        <Modal title="Редагувати книгу" onClose={close}>
          <BookForm
            initial={dialog.book}
            submitLabel="Зберегти"
            onSubmit={update}
            secondary={
              <button
                type="button"
                className="btn--ghost"
                onClick={() => setDialog({ mode: 'view', book: dialog.book })}
              >
                Скасувати
              </button>
            }
          />
        </Modal>
      )}

      {dialog?.mode === 'view' && (
        <Modal onClose={close} wide>
          <BookDetails book={dialog.book}>
            <button onClick={() => setDialog({ mode: 'edit', book: dialog.book })}>
              Редагувати
            </button>
            <button className="btn--ghost" onClick={() => remove(dialog.book)}>
              Прибрати з полиці
            </button>
          </BookDetails>
        </Modal>
      )}
    </>
  );
}

function plural(n, one, few, many) {
  const m10 = n % 10;
  const m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return one;
  if (m10 >= 2 && m10 <= 4 && (m100 < 12 || m100 > 14)) return few;
  return many;
}

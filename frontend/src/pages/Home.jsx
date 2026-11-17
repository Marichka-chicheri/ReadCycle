import { useEffect, useMemo, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../api.js';
import BookDetails from '../components/BookDetails.jsx';
import { Cabinet, Shelf, chunk } from '../components/Bookshelf.jsx';
import CatalogFilters from '../components/CatalogFilters.jsx';
import Modal from '../components/Modal.jsx';

const PER_SHELF = 20;
const MIN_SHELVES = 3; // an almost empty cabinet still looks like a cabinet
const KEYS = ['genre', 'language', 'offer'];

// Main page: everyone else's books in a big oak cabinet, with filters.
// The select filters live in the URL (?genre=fantasy&offer=give) so a view can be bookmarked;
// the search text is local and debounced.
export default function Home() {
  const [params, setParams] = useSearchParams();
  const filters = useMemo(
    () => Object.fromEntries(KEYS.map((k) => [k, params.get(k) || ''])),
    [params],
  );
  const [result, setResult] = useState(null); // { books, total }
  const [error, setError] = useState('');
  const [open, setOpen] = useState(null);

  // Debounce typing in the search box; selects apply at once.
  const [q, setQ] = useState('');
  const [debouncedQ, setDebouncedQ] = useState('');
  useEffect(() => {
    const t = setTimeout(() => setDebouncedQ(q.trim()), 300);
    return () => clearTimeout(t);
  }, [q]);

  useEffect(() => {
    const query = new URLSearchParams();
    if (debouncedQ) query.set('q', debouncedQ);
    for (const k of KEYS) if (filters[k]) query.set(k, filters[k]);
    let cancelled = false;
    setError('');
    api(`/books${query.toString() ? `?${query}` : ''}`)
      .then((r) => !cancelled && setResult(r))
      .catch((e) => !cancelled && setError(e.message));
    return () => {
      cancelled = true;
    };
  }, [debouncedQ, filters]);

  const onFilters = (next) => {
    setQ(next.q);
    const p = new URLSearchParams();
    for (const k of KEYS) if (next[k]) p.set(k, next[k]);
    setParams(p, { replace: true });
  };

  const books = result?.books || [];
  const shelves = chunk(books, PER_SHELF);
  while (shelves.length < MIN_SHELVES) shelves.push([]);
  const filtered = KEYS.some((k) => filters[k]) || q;
  const emptyText =
    result === null
      ? 'Відчиняємо шафу…'
      : filtered
        ? 'За цими фільтрами нічого не знайшлося'
        : 'Шафа поки порожня. Будь першою — додай книги на свою полицю';

  return (
    <section className="home-scene">
      <header className="page-intro">
        <span className="eyebrow">Обмін книгами між студентами УКУ</span>
        <h1>
          Віддай прочитане — <span className="serif-italic">знайди своє</span>
        </h1>
        <p>
          У шафі стоять книги, які інші студенти готові віддати чи обміняти. Натисни на корінець,
          щоб роздивитися книгу. <Link to="/profile">До моєї полиці →</Link>
        </p>
      </header>

      {error && <p className="error">Не вдалося завантажити каталог: {error}</p>}

      <Cabinet
        title="ReadCycle"
        toolbar={
          <CatalogFilters
            value={{ ...filters, q }}
            onChange={onFilters}
            total={result ? result.total : null}
          />
        }
      >
        {shelves.map((row, i) => (
          <Shelf
            key={i}
            books={row}
            empty={i === 0 ? emptyText : ''}
            onBookClick={(book) => setOpen(book)}
          />
        ))}
      </Cabinet>
      {result && result.total > books.length && (
        <p className="catalog-more">
          Показано {books.length} з {result.total}. Уточни пошук, щоб знайти потрібне.
        </p>
      )}

      {open && (
        <Modal onClose={() => setOpen(null)} wide>
          <BookDetails book={open} />
        </Modal>
      )}
    </section>
  );
}

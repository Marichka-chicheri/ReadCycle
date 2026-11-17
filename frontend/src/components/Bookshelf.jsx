// Realistic wooden furniture for books: <Cabinet> (big oak bookcase on the main page),
// <Shelf> (one shelf: inside a cabinet or wall-mounted in a profile) and <BookSpine>.
// Spines are drawn cloth bindings; hovering one shows a card with the real cover and details.

import { useRef, useState } from 'react';
import { genreLabel, offerLabel } from '../genres.js';
import BookCover from './BookCover.jsx';
import { spineStyle } from './spine.js';

export { spineStyle };

export function BookSpine({
  title,
  author,
  offer,
  lean = 0,
  onClick,
  selected = false,
  onPeek,
  onUnpeek,
}) {
  const s = spineStyle(title, author);
  // A plain <div> when the book is decorative; a <button> only when it can be clicked.
  const Tag = onClick ? 'button' : 'div';
  const cls = [
    'spine',
    s.light && 'spine--light',
    selected && 'spine--selected',
    onClick && 'spine--clickable',
  ]
    .filter(Boolean)
    .join(' ');
  return (
    <Tag
      {...(onClick ? { type: 'button', onClick } : {})}
      onMouseEnter={onPeek}
      onMouseLeave={onUnpeek}
      onFocus={onPeek}
      onBlur={onUnpeek}
      className={cls}
      data-bands={s.bands}
      style={{
        '--c': s.color,
        '--h': `${s.height}px`,
        '--w': `${s.width}px`,
        '--lean': `${lean}deg`,
        // a leaning book needs a little room so it rests on its neighbour instead of cutting into it
        marginLeft: lean ? '14px' : undefined,
      }}
      title={onPeek ? undefined : author ? `${title} — ${author}` : title}
      aria-label={author ? `${title} — ${author}` : title}
    >
      {/* a gold silk bookmark marks books that are given away for free */}
      {offer === 'give' && <span className="spine__ribbon" aria-hidden="true" />}
      <span className="spine__title">{title}</span>
      <span className="spine__mark" aria-hidden="true" />
    </Tag>
  );
}

const PEEK_HALF_WIDTH = 150; // half of .peek width, keeps the card inside the shelf

// Card that floats above a spine on hover: the cover (photo or drawn) and the main facts.
function Peek({ book, x, bottom }) {
  return (
    <div className="peek" style={{ left: x, bottom }} role="tooltip">
      <div className="peek__cover">
        <BookCover title={book.title} author={book.author} src={book.cover_src} />
      </div>
      <div className="peek__text">
        <strong>{book.title}</strong>
        <span>{book.author}</span>
        <small>
          {[book.genre && genreLabel(book.genre), book.offer && offerLabel(book.offer)]
            .filter(Boolean)
            .join(' · ')}
        </small>
        {book.owner_name && <small>з полиці: {book.owner_name}</small>}
      </div>
    </div>
  );
}

// One shelf. `variant="wall"` = floating plank with brackets (profile),
// default = shelf inside a <Cabinet>. With `onBookClick`, spines are clickable and show a
// preview card on hover.
export function Shelf({ books = [], variant = 'cabinet', empty, onBookClick, children }) {
  const ref = useRef(null);
  const [peek, setPeek] = useState(null); // { book, x, bottom }

  const showPeek = (book) => (e) => {
    const spine = e.currentTarget;
    const width = ref.current?.clientWidth || 0;
    const center = spine.offsetLeft + spine.offsetWidth / 2;
    const x = Math.min(Math.max(center, PEEK_HALF_WIDTH), width - PEEK_HALF_WIDTH);
    setPeek({ book, x, bottom: spine.offsetHeight + 34 });
  };

  return (
    <div className={`shelf shelf--${variant}`} ref={ref}>
      <div className="shelf__books">
        {books.length === 0 && empty && <p className="shelf__empty">{empty}</p>}
        {books.map((b, i) => (
          <BookSpine
            key={b.book_id || b.id || `${b.title}-${i}`}
            title={b.title}
            author={b.author}
            offer={b.offer}
            // the last book on a shelf that is not full leans on its neighbour
            lean={i === books.length - 1 && books.length > 2 && books.length < 9 ? -6 : 0}
            onClick={onBookClick ? () => onBookClick(b) : undefined}
            onPeek={onBookClick ? showPeek(b) : undefined}
            onUnpeek={onBookClick ? () => setPeek(null) : undefined}
          />
        ))}
        {children}
      </div>
      <div className="shelf__plank" aria-hidden="true" />
      {peek && <Peek {...peek} />}
    </div>
  );
}

// Big oak bookcase: crown on top, optional toolbar (a drawer rail with filters), dark back
// panel with shelves, plinth.
export function Cabinet({ title, toolbar, children }) {
  return (
    <div className="cabinet">
      <div className="cabinet__crown" aria-hidden="true" />
      {title && <div className="cabinet__plaque">{title}</div>}
      {toolbar && <div className="cabinet__toolbar">{toolbar}</div>}
      <div className="cabinet__inner">{children}</div>
      <div className="cabinet__plinth" aria-hidden="true" />
    </div>
  );
}

// Split a flat list of books into shelves of `perShelf`.
export function chunk(list, perShelf) {
  const out = [];
  for (let i = 0; i < list.length; i += perShelf) out.push(list.slice(i, i + perShelf));
  return out;
}

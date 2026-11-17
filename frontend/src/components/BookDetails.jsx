import { genreLabel, languageLabel, offerLabel } from '../genres.js';
import BookCover from './BookCover.jsx';

// Cover + facts about one book. `children` are the action buttons under it.
export default function BookDetails({ book, children }) {
  return (
    <div className="book-view">
      <BookCover title={book.title} author={book.author} src={book.cover_src} />
      <div className="book-view__info">
        <span className={`offer-badge offer-badge--${book.offer}`}>{offerLabel(book.offer)}</span>
        <h2>{book.title}</h2>
        <p className="book-view__author">{book.author}</p>
        <dl className="facts">
          <dt>Жанр</dt>
          <dd>{genreLabel(book.genre)}</dd>
          <dt>Мова</dt>
          <dd>{languageLabel(book.language)}</dd>
          {book.year && (
            <>
              <dt>Рік</dt>
              <dd>{book.year}</dd>
            </>
          )}
          {book.isbn && (
            <>
              <dt>ISBN</dt>
              <dd>{book.isbn}</dd>
            </>
          )}
          {book.owner_name && (
            <>
              <dt>З полиці</dt>
              <dd>{book.owner_name}</dd>
            </>
          )}
        </dl>
        {book.description && <p className="book-view__description">{book.description}</p>}
        {children && <div className="form-actions">{children}</div>}
      </div>
    </div>
  );
}

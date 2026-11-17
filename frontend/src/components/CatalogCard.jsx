import { genreLabel, languageLabel } from '../genres.js';
import BookCover from './BookCover.jsx';

// A wishlist entry drawn as a typed library catalogue card (lined paper, red rule, rod hole).
// Clickable when `onClick` is given (own wishlist), read-only otherwise.
export default function CatalogCard({ wish, number, onClick }) {
  const isBook = wish.kind === 'book';
  // read-only on other people's profiles: a plain <div> instead of a button
  const Tag = onClick ? 'button' : 'div';
  const cls = `catalog-card${onClick ? '' : ' catalog-card--static'}${
    wish.cover_url ? ' catalog-card--with-cover' : ''
  }`;
  const meta = [wish.genre && genreLabel(wish.genre), wish.language && languageLabel(wish.language)]
    .filter(Boolean)
    .join(' · ');

  return (
    <Tag {...(onClick ? { type: 'button', onClick } : {})} className={cls}>
      <span className="catalog-card__head">
        <span>№ {String(number).padStart(2, '0')}</span>
        <span>{isBook ? 'Книга' : 'Жанр'}</span>
      </span>
      {isBook ? (
        <>
          <span className="catalog-card__title">{wish.title}</span>
          {wish.author && <span className="catalog-card__author">{wish.author}</span>}
          {meta && <span className="catalog-card__meta">{meta}</span>}
        </>
      ) : (
        <>
          <span className="catalog-card__author">будь-що з жанру</span>
          <span className="catalog-card__title">{genreLabel(wish.genre)}</span>
          <span className="catalog-card__meta">
            {wish.language
              ? `мова: ${languageLabel(wish.language).toLowerCase()}`
              : 'будь-якою мовою'}
          </span>
        </>
      )}
      {wish.note && <span className="catalog-card__note">{wish.note}</span>}
      {wish.cover_url && (
        // a little cover clipped to the card
        <span className="catalog-card__cover" aria-hidden="true">
          <BookCover title={wish.title} author={wish.author} src={wish.cover_url} size="mini" />
        </span>
      )}
      <span className="catalog-card__hole" aria-hidden="true" />
    </Tag>
  );
}

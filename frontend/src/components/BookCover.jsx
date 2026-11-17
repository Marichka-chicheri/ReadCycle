import { spineStyle } from './Bookshelf.jsx';

// Front cover of a drawn book: the same cloth colour as its spine, a gilt frame, embossed title.
// size="mini" is a small thumbnail (title only), e.g. pasted into a match letter.
export default function BookCover({ title, author, size }) {
  const s = spineStyle(title, author);
  const mini = size === 'mini';
  const cls = ['cover', s.light && 'cover--light', mini && 'cover--mini'].filter(Boolean).join(' ');
  return (
    <div className={cls} style={{ '--c': s.color }}>
      <div className="cover__frame">
        {!mini && <span className="cover__author">{author}</span>}
        <span className="cover__ornament" aria-hidden="true">
          ❦
        </span>
        <span className="cover__title">{title}</span>
      </div>
    </div>
  );
}

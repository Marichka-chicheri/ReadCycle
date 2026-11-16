import { spineStyle } from './Bookshelf.jsx';

// Front cover of a drawn book: the same cloth colour as its spine, a gilt frame, embossed title.
export default function BookCover({ title, author }) {
  const s = spineStyle(title, author);
  return (
    <div className={`cover${s.light ? ' cover--light' : ''}`} style={{ '--c': s.color }}>
      <div className="cover__frame">
        <span className="cover__author">{author}</span>
        <span className="cover__ornament" aria-hidden="true">
          ❦
        </span>
        <span className="cover__title">{title}</span>
      </div>
    </div>
  );
}

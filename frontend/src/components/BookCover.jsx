import { useEffect, useState } from 'react';
import { spineStyle } from './spine.js';

// A book's front cover. With `src` it shows the photo (uploaded or found); without one, or if the
// photo fails to load, it draws a cloth-bound cover in the same colour as the book's spine.
// size="mini" is a small thumbnail (e.g. pasted into a match letter).
export default function BookCover({ title, author, src, size }) {
  const [failed, setFailed] = useState(false);
  useEffect(() => setFailed(false), [src]);
  const mini = size === 'mini';

  if (src && !failed) {
    return (
      <div className={`cover cover--photo${mini ? ' cover--mini' : ''}`}>
        <img src={src} alt={title} loading="lazy" onError={() => setFailed(true)} />
      </div>
    );
  }

  const s = spineStyle(title, author);
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

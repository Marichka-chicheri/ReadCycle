// Realistic wooden furniture for books: <Cabinet> (big oak bookcase on the main page),
// <Shelf> (one shelf: inside a cabinet or wall-mounted in a profile) and <BookSpine>.
// Books are drawn, not photographed: a cloth-bound spine whose colour, height and width
// are derived from the title, so the same book always looks the same.

const CLOTH = [
  '#5c1724', // бордо
  '#7a2a2f', // теракотово-винний
  '#2f4a3a', // пляшкова зелень
  '#1f2f4a', // чорнильно-синій
  '#4a2340', // слива
  '#5a3a22', // тютюн
  '#3d4650', // графіт
  '#8a6a2e', // охра
  '#d9c7a3', // небілений льон
  '#2a2320', // майже чорний
];

function hash(str) {
  let h = 2166136261;
  for (let i = 0; i < str.length; i++) {
    h ^= str.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

export function spineStyle(title = '', author = '') {
  const h = hash(`${title}|${author}`);
  const color = CLOTH[h % CLOTH.length];
  const height = 148 + ((h >> 4) % 50); // 148–197 px
  const width = 36 + ((h >> 10) % 16) + Math.min(title.length, 26) * 0.45; // ~36–64 px
  const light = color === '#d9c7a3';
  const bands = (h >> 16) % 3; // 0: none, 1: top+bottom, 2: double
  return { color, height, width: Math.round(width), light, bands };
}

export function BookSpine({ title, author, lean = 0, onClick, selected = false }) {
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
      title={author ? `${title} — ${author}` : title}
    >
      <span className="spine__title">{title}</span>
      <span className="spine__mark" aria-hidden="true" />
    </Tag>
  );
}

// One shelf. `variant="wall"` = floating plank with brackets (profile),
// default = shelf inside a <Cabinet>.
export function Shelf({ books = [], variant = 'cabinet', empty, onBookClick, children }) {
  return (
    <div className={`shelf shelf--${variant}`}>
      <div className="shelf__books">
        {books.length === 0 && empty && <p className="shelf__empty">{empty}</p>}
        {books.map((b, i) => (
          <BookSpine
            key={b.id || `${b.title}-${i}`}
            title={b.title}
            author={b.author}
            // the last book on a shelf that is not full leans on its neighbour
            lean={i === books.length - 1 && books.length > 2 && books.length < 9 ? -6 : 0}
            onClick={onBookClick ? () => onBookClick(b) : undefined}
          />
        ))}
        {children}
      </div>
      <div className="shelf__plank" aria-hidden="true" />
    </div>
  );
}

// Big oak bookcase: crown on top, dark back panel, shelves, plinth.
export function Cabinet({ title, children }) {
  return (
    <div className="cabinet">
      <div className="cabinet__crown" aria-hidden="true" />
      {title && <div className="cabinet__plaque">{title}</div>}
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

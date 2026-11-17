// Find book covers by title (and author) in two free catalogues, straight from the browser:
//   Open Library — large covers, strong on English books;
//   Google Books — much better for Ukrainian books, smaller pictures.
// Only these hosts are accepted by the backend (backend/src/domain/media.py COVER_HOSTS).

const LIMIT = 12;

async function openLibrary(title, author) {
  const params = new URLSearchParams({
    title,
    limit: String(LIMIT),
    fields: 'title,author_name,first_publish_year,cover_i',
  });
  if (author) params.set('author', author);
  const res = await fetch(`https://openlibrary.org/search.json?${params}`);
  if (!res.ok) return [];
  const { docs = [] } = await res.json();
  return docs
    .filter((d) => d.cover_i)
    .map((d) => ({
      src: `https://covers.openlibrary.org/b/id/${d.cover_i}-L.jpg`,
      title: d.title,
      author: (d.author_name || []).join(', '),
      year: d.first_publish_year || '',
      source: 'Open Library',
    }));
}

async function googleBooks(title, author) {
  const q = `intitle:${title}${author ? ` inauthor:${author}` : ''}`;
  const params = new URLSearchParams({
    q,
    maxResults: String(LIMIT),
    printType: 'books',
    fields: 'items(volumeInfo(title,authors,publishedDate,imageLinks))',
  });
  const res = await fetch(`https://www.googleapis.com/books/v1/volumes?${params}`);
  if (!res.ok) return [];
  const { items = [] } = await res.json();
  return items
    .map(({ volumeInfo: v = {} }) => {
      const link = v.imageLinks?.thumbnail || v.imageLinks?.smallThumbnail;
      if (!link) return null;
      return {
        src: link.replace(/^http:/, 'https:').replace('&edge=curl', ''),
        title: v.title,
        author: (v.authors || []).join(', '),
        year: (v.publishedDate || '').slice(0, 4),
        source: 'Google Books',
      };
    })
    .filter(Boolean);
}

export async function searchCovers(title, author = '') {
  const t = title.trim();
  if (!t) return [];
  const a = author.trim();
  const [google, ol] = await Promise.allSettled([googleBooks(t, a), openLibrary(t, a)]);
  const all = [
    ...(google.status === 'fulfilled' ? google.value : []),
    ...(ol.status === 'fulfilled' ? ol.value : []),
  ];
  const seen = new Set();
  return all.filter((c) => !seen.has(c.src) && seen.add(c.src)).slice(0, 2 * LIMIT);
}

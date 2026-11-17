import { api } from './api.js';

// Cover candidates for a book, found by our backend in Google Books and Open Library
// (backend/src/common/cover_sources.py). Pass { title, author } or { q } for free text.
// Returns { covers: [{ src, title, author, year, source }], google: bool }.
export async function searchCovers({ title = '', author = '', q = '' }) {
  const params = new URLSearchParams();
  if (q.trim()) params.set('q', q.trim());
  else {
    params.set('title', title.trim());
    if (author.trim()) params.set('author', author.trim());
  }
  return api(`/covers/search?${params}`);
}

// Catalogue matches for auto-filling the book form: title/author text or an ISBN.
// Returns { books: [{ title, author, year, isbn, language, genre, cover_url, source }] }.
export async function lookupBooks(q) {
  return api(`/books/lookup?${new URLSearchParams({ q: q.trim() })}`);
}

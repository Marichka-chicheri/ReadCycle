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

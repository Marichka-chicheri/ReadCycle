import { useEffect, useState } from 'react';
import { api } from '../api.js';

// Placeholder protected page: proves the token reaches the API. Book features go in src/pages.
export default function Home() {
  const [me, setMe] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    api('/me').then(setMe).catch((e) => setError(e.message));
  }, []);

  return (
    <section>
      <h1>Вітаємо в ReadCycle</h1>
      <p>Обмін паперовими книгами між студентами УКУ.</p>
      {me && (
        <p>
          API <code>/me</code>: ви увійшли як <b>{me.email}</b>
        </p>
      )}
      {error && <p className="error">{error}</p>}
    </section>
  );
}

import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../api.js';

// "Заблоковані" in the profile: people the user does not want to see, with an unblock button.
// Renders nothing while the list is empty.
export default function BlockedUsers() {
  const [blocks, setBlocks] = useState([]);

  useEffect(() => {
    api('/my/blocks')
      .then((r) => setBlocks(r.blocks))
      .catch(() => {});
  }, []);

  const unblock = async (id) => {
    try {
      await api(`/blocks/${encodeURIComponent(id)}`, { method: 'DELETE' });
      setBlocks((list) => list.filter((b) => b.user_id !== id));
    } catch (e) {
      window.alert(`Не вдалося розблокувати: ${e.message}`);
    }
  };

  if (!blocks.length) return null;
  return (
    <>
      <div className="section-head section-head--spaced">
        <h2>Заблоковані</h2>
        <span className="muted">Не бачать вас, а ви — їх</span>
      </div>
      <ul className="card mod-list">
        {blocks.map((b) => (
          <li key={b.user_id} className="mod-row">
            <span>{b.display_name}</span>
            <button className="btn--ghost btn--small" onClick={() => unblock(b.user_id)}>
              Розблокувати
            </button>
          </li>
        ))}
      </ul>
    </>
  );
}

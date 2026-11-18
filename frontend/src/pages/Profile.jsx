import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../api.js';
import { useAuth } from '../AuthContext.jsx';
import { useDialogs } from '../components/Dialogs.jsx';
import { AboutBlock, IdentityCard } from '../components/Identity.jsx';
import BlockedUsers from '../components/BlockedUsers.jsx';
import MyShelf from '../components/MyShelf.jsx';
import ProfileForm from '../components/ProfileForm.jsx';
import TelegramAlerts from '../components/TelegramAlerts.jsx';
import Wishlist from '../components/Wishlist.jsx';
import { useProfile } from '../ProfileContext.jsx';

// The signed-in user's own profile: identity card, details, bookshelf and wishlist.
export default function Profile() {
  const { profile, save } = useProfile();
  const [editing, setEditing] = useState(false);
  const [saved, setSaved] = useState(false);

  return (
    <section className="profile">
      <div className="profile__top">
        <IdentityCard profile={profile} />

        <div className="card profile__details">
          {editing ? (
            <>
              <span className="eyebrow">Редагування профілю</span>
              <ProfileForm
                initial={profile}
                onSubmit={async (data) => {
                  await save(data);
                  setEditing(false);
                  setSaved(true);
                }}
                secondary={
                  <button type="button" className="btn--ghost" onClick={() => setEditing(false)}>
                    Скасувати
                  </button>
                }
              />
            </>
          ) : (
            <>
              {saved && <p className="ok">Профіль збережено.</p>}
              <AboutBlock
                profile={profile}
                emptyAbout="Тут поки порожньо. Додай кілька слів про себе: що любиш читати, що шукаєш."
                action={
                  <button
                    className="btn--ghost btn--small"
                    onClick={() => {
                      setSaved(false);
                      setEditing(true);
                    }}
                  >
                    Редагувати
                  </button>
                }
              />
            </>
          )}
        </div>
      </div>

      <MyShelf />
      <Wishlist />
      <TelegramAlerts />
      <BlockedUsers />
      <DeleteAccount />
    </section>
  );
}

// Deleting the account: the API removes the data, then the browser removes the sign-in.
function DeleteAccount() {
  const { deleteSignIn } = useAuth();
  const { confirm, notify } = useDialogs();
  const navigate = useNavigate();
  const [busy, setBusy] = useState(false);

  const run = async () => {
    const ok = await confirm({
      title: 'Видалити акаунт назавжди?',
      message:
        'Зникнуть профіль, фото, усі книги з полиці та вішліст. Повернути їх не вийде. Зареєструватися знову з цією поштою можна буде будь-коли.',
      confirmLabel: 'Видалити акаунт',
      danger: true,
    });
    if (!ok) return;
    setBusy(true);
    try {
      await api('/profile', { method: 'DELETE' });
    } catch (e) {
      setBusy(false);
      notify(`Не вдалося видалити акаунт: ${e.message}`);
      return;
    }
    try {
      await deleteSignIn();
    } catch {
      // the data is already gone; the sign-in itself will simply lead to a fresh onboarding
    }
    navigate('/login', { replace: true });
  };

  return (
    <div className="danger-zone">
      <button type="button" className="link-button" onClick={run} disabled={busy}>
        {busy ? 'Видаляємо…' : 'Видалити акаунт'}
      </button>
    </div>
  );
}

import { useState } from 'react';
import { AboutBlock, IdentityCard } from '../components/Identity.jsx';
import MyShelf from '../components/MyShelf.jsx';
import ProfileForm from '../components/ProfileForm.jsx';
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
    </section>
  );
}

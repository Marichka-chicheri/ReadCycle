import { createContext, useCallback, useContext, useEffect, useState } from 'react';
import { api } from './api.js';
import { useAuth } from './AuthContext.jsx';

// Loads the signed-in user's profile once and shares it with every page.
// profile: undefined = loading, null = no profile yet (show onboarding), object = ready.
const ProfileContext = createContext(null);

export function ProfileProvider({ children }) {
  const { user } = useAuth();
  const [profile, setProfile] = useState(undefined);
  const [error, setError] = useState('');

  const reload = useCallback(async () => {
    setError('');
    try {
      const { profile } = await api('/profile');
      setProfile(profile);
    } catch (e) {
      setError(e.message);
    }
  }, []);

  useEffect(() => {
    if (user) reload();
    else setProfile(undefined);
  }, [user, reload]);

  const save = async (data) => {
    const { profile } = await api('/profile', { method: 'PUT', body: JSON.stringify(data) });
    setProfile(profile);
    return profile;
  };

  return (
    <ProfileContext.Provider value={{ profile, error, reload, save }}>
      {children}
    </ProfileContext.Provider>
  );
}

export const useProfile = () => useContext(ProfileContext);

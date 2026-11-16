import { createContext, useContext, useEffect, useState } from 'react';
import * as auth from './auth.js';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  // undefined = still checking the stored session, null = signed out
  const [user, setUser] = useState(undefined);

  const refresh = async () => {
    const session = await auth.getSession();
    setUser(session ? { email: session.getIdToken().payload.email } : null);
  };

  useEffect(() => {
    refresh();
  }, []);

  const value = {
    user,
    signIn: async (email, password) => {
      await auth.signIn(email, password);
      await refresh();
    },
    signOut: () => {
      auth.signOut();
      setUser(null);
    },
  };
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);

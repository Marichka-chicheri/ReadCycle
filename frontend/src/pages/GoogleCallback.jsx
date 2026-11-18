import { useEffect, useRef, useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { friendlyError, startGoogleSignIn } from '../auth.js';
import { useAuth } from '../AuthContext.jsx';
import AuthLayout from '../components/AuthLayout.jsx';

const RETRY_KEY = 'rc_google_retry';

// Where Cognito sends the browser back after Google: /auth/callback?code=...&state=...
export default function GoogleCallback() {
  const { finishGoogleSignIn } = useAuth();
  const navigate = useNavigate();
  const { search } = useLocation();
  const [error, setError] = useState('');
  const started = useRef(false); // an authorization code works once: don't run twice (StrictMode)

  useEffect(() => {
    if (started.current) return;
    started.current = true;
    finishGoogleSignIn(search)
      .then(() => {
        sessionStorage.removeItem(RETRY_KEY);
        navigate('/', { replace: true });
      })
      .catch((err) => {
        // First Google login of a student who already has a password account: the pre sign-up
        // trigger links the two, and Cognito asks to repeat the login once. Do it automatically.
        if (
          String(err.message).includes('Already found an entry for username') &&
          !sessionStorage.getItem(RETRY_KEY)
        ) {
          sessionStorage.setItem(RETRY_KEY, '1');
          startGoogleSignIn().catch((e) => setError(friendlyError(e)));
          return;
        }
        sessionStorage.removeItem(RETRY_KEY);
        setError(friendlyError(err));
      });
  }, []);

  return (
    <AuthLayout>
      <div className="card">
        <h1>Вхід через Google</h1>
        {error ? (
          <>
            <p className="error">{error}</p>
            <Link to="/login">Повернутися до входу</Link>
          </>
        ) : (
          <p>Заходимо…</p>
        )}
      </div>
    </AuthLayout>
  );
}

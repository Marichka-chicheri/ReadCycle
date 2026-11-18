import { useState } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom';
import { friendlyError } from '../auth.js';
import { useAuth } from '../AuthContext.jsx';
import AuthLayout from '../components/AuthLayout.jsx';
import GoogleButton from '../components/GoogleButton.jsx';

export default function Login() {
  const { user, signIn } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState(location.state?.email || '');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  if (user) return <Navigate to="/" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      await signIn(email.trim(), password);
      navigate(location.state?.from?.pathname || '/', { replace: true });
    } catch (err) {
      if (err.code === 'UserNotConfirmedException') {
        navigate('/register', { state: { email: email.trim(), step: 'confirm' } });
        return;
      }
      setError(friendlyError(err));
    } finally {
      setBusy(false);
    }
  };

  return (
    <AuthLayout>
      <form onSubmit={submit} className="card">
        <span className="eyebrow">З поверненням</span>
        <h1>Вхід</h1>
        {location.state?.confirmed && <p className="ok">Пошту підтверджено. Увійдіть.</p>}
        {location.state?.passwordChanged && (
          <p className="ok">Пароль змінено. Увійдіть з новим паролем.</p>
        )}
        <GoogleButton />
        <label>
          Пошта УКУ
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>
          Пароль
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button disabled={busy}>Увійти</button>
        <p>
          <Link to="/forgot" state={{ email }}>
            Забули пароль?
          </Link>
        </p>
        <p>
          Немає акаунта? <Link to="/register">Зареєструватися</Link>
        </p>
      </form>
    </AuthLayout>
  );
}

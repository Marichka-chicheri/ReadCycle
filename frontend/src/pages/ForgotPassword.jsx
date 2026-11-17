import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { forgotPassword, friendlyError, resetPassword } from '../auth.js';
import AuthLayout from '../components/AuthLayout.jsx';

// Two steps: ask for a code by email, then set a new password with that code.
export default function ForgotPassword() {
  const navigate = useNavigate();
  const location = useLocation();
  const [step, setStep] = useState('email');
  const [email, setEmail] = useState(location.state?.email || '');
  const [code, setCode] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);

  const run = async (fn) => {
    setError('');
    setInfo('');
    setBusy(true);
    try {
      await fn();
    } catch (err) {
      setError(friendlyError(err));
    } finally {
      setBusy(false);
    }
  };

  const sendCode = (e) => {
    e?.preventDefault();
    run(async () => {
      await forgotPassword(email.trim());
      setStep('reset');
      setInfo(`Якщо акаунт ${email.trim()} існує, ми надіслали на нього код.`);
    });
  };

  const submitReset = (e) => {
    e.preventDefault();
    run(async () => {
      await resetPassword(email.trim(), code.trim(), password);
      navigate('/login', {
        state: { email: email.trim(), passwordChanged: true },
      });
    });
  };

  if (step === 'reset') {
    return (
      <AuthLayout>
        <form onSubmit={submitReset} className="card">
          <span className="eyebrow">Крок 2 з 2</span>
          <h1>Новий пароль</h1>
          <label>
            Код з листа
            <input value={code} onChange={(e) => setCode(e.target.value)} required />
          </label>
          <label>
            Новий пароль (мін. 8 символів, малі літери та цифри)
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              minLength={8}
              required
            />
          </label>
          {info && <p className="ok">{info}</p>}
          {error && <p className="error">{error}</p>}
          <button disabled={busy}>Змінити пароль</button>
          <button type="button" className="link" disabled={busy} onClick={() => sendCode()}>
            Надіслати код ще раз
          </button>
        </form>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <form onSubmit={sendCode} className="card">
        <span className="eyebrow">Крок 1 з 2</span>
        <h1>Забули пароль?</h1>
        <p>Вкажіть пошту: ми надішлемо код для встановлення нового пароля.</p>
        <label>
          Пошта УКУ
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        {error && <p className="error">{error}</p>}
        <button disabled={busy}>Надіслати код</button>
        <p>
          <Link to="/login">← Повернутися до входу</Link>
        </p>
      </form>
    </AuthLayout>
  );
}

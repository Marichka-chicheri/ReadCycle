import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { confirmSignUp, friendlyError, isAllowedEmail, resendCode, signUp } from '../auth.js';
import { getConfig } from '../config.js';
import AuthLayout from '../components/AuthLayout.jsx';
import GoogleButton from '../components/GoogleButton.jsx';

// Two steps: sign up with email+password, then confirm with the emailed code.
export default function Register() {
  const navigate = useNavigate();
  const location = useLocation();
  const [step, setStep] = useState(location.state?.step || 'signup');
  const [email, setEmail] = useState(location.state?.email || '');
  const [password, setPassword] = useState('');
  const [code, setCode] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [busy, setBusy] = useState(false);
  const domain = getConfig().allowedEmailDomain;

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

  const submitSignUp = (e) => {
    e.preventDefault();
    // Fast client-side check; the Pre Sign-up Lambda enforces it on the server.
    if (!isAllowedEmail(email)) {
      setError(`Реєстрація можлива лише з університетською поштою @${domain}.`);
      return;
    }
    run(async () => {
      await signUp(email.trim(), password);
      setStep('confirm');
      setInfo(`Ми надіслали код на ${email.trim()}.`);
    });
  };

  const submitConfirm = (e) => {
    e.preventDefault();
    run(async () => {
      await confirmSignUp(email.trim(), code.trim());
      navigate('/login', { state: { email: email.trim(), confirmed: true } });
    });
  };

  if (step === 'confirm') {
    return (
      <AuthLayout>
        <form onSubmit={submitConfirm} className="card">
          <span className="eyebrow">Крок 2 з 2</span>
          <h1>Підтвердження пошти</h1>
          <label>
            Пошта
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <label>
            Код з листа
            <input value={code} onChange={(e) => setCode(e.target.value)} required />
          </label>
          {info && <p className="ok">{info}</p>}
          {error && <p className="error">{error}</p>}
          <button disabled={busy}>Підтвердити</button>
          <button
            type="button"
            className="link"
            disabled={busy}
            onClick={() =>
              run(async () => {
                await resendCode(email.trim());
                setInfo('Новий код надіслано.');
              })
            }
          >
            Надіслати код ще раз
          </button>
        </form>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout>
      <form onSubmit={submitSignUp} className="card">
        <span className="eyebrow">Крок 1 з 2</span>
        <h1>Реєстрація</h1>
        <GoogleButton />
        <label>
          Пошта @{domain}
          <input
            type="email"
            placeholder={`name@${domain}`}
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
        </label>
        <label>
          Пароль (мін. 8 символів, малі літери та цифри)
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            minLength={8}
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button disabled={busy}>Зареєструватися</button>
        <p>
          Вже є акаунт? <Link to="/login">Увійти</Link> ·{' '}
          <button type="button" className="link" onClick={() => setStep('confirm')}>
            Маю код
          </button>
        </p>
      </form>
    </AuthLayout>
  );
}

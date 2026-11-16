import { useState } from 'react';
import { Navigate, useNavigate } from 'react-router-dom';
import ProfileForm from '../components/ProfileForm.jsx';
import { useProfile } from '../ProfileContext.jsx';

// First sign-in: step 1 creates the profile (name + contact), step 2 is optional details.
export default function Welcome() {
  const { profile, save } = useProfile();
  const navigate = useNavigate();
  // a user who already has a profile and opens /welcome directly goes straight to it
  const [step, setStep] = useState(profile ? 'done' : 'contacts');

  if (step === 'done') return <Navigate to="/profile" replace />;

  const steps = [
    { key: 'contacts', title: 'Знайомство' },
    { key: 'about', title: 'Про тебе' },
  ];

  return (
    <div className="onboarding">
      <ol className="steps">
        {steps.map((s, i) => (
          <li key={s.key} className={s.key === step ? 'current' : ''}>
            <span>{['I', 'II'][i]}</span> {s.title}
          </li>
        ))}
      </ol>

      <div className="card onboarding__card">
        {step === 'contacts' ? (
          <>
            <span className="eyebrow">Ласкаво просимо до ReadCycle</span>
            <h1>Як тебе звати?</h1>
            <p className="muted">
              Ім'я або нік підпишуть твою полицю, а контакт потрібен, щоб домовитися про обмін.
            </p>
            <ProfileForm
              key="contacts"
              sections={['contacts']}
              submitLabel="Далі"
              onSubmit={async (data) => {
                await save(data);
                setStep('about');
              }}
            />
          </>
        ) : (
          <>
            <span className="eyebrow">Необов'язково</span>
            <h1>Трохи про тебе</h1>
            <p className="muted">Це допоможе іншим зрозуміти, що тобі запропонувати.</p>
            <ProfileForm
              key="about"
              initial={profile}
              sections={['about']}
              submitLabel="Зберегти"
              onSubmit={async (data) => {
                await save(data);
                navigate('/profile', { replace: true });
              }}
              secondary={
                <button
                  type="button"
                  className="btn--ghost"
                  onClick={() => navigate('/profile', { replace: true })}
                >
                  Пропустити
                </button>
              }
            />
          </>
        )}
      </div>
    </div>
  );
}

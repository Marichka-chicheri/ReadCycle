import { useEffect, useRef, useState } from 'react';
import { api } from '../api.js';
import { useDialogs } from './Dialogs.jsx';

const POLL_MS = 3000;
const POLL_TRIES = 60; // ~3 minutes to press Start in Telegram

// "Сповіщення в Telegram" in the profile: connect the bot, see that it works, switch it off.
// Hidden completely while the bot is not configured on the server.
export default function TelegramAlerts() {
  const [state, setState] = useState(null); // { available, linked }
  const [waiting, setWaiting] = useState(false);
  const { notify } = useDialogs();
  const timer = useRef(null);

  const load = () => api('/telegram').then(setState);

  useEffect(() => {
    load().catch(() => setState({ available: false, linked: false }));
    return () => clearInterval(timer.current);
  }, []);

  // after opening the bot: check every few seconds until Start is pressed
  const waitForStart = () => {
    setWaiting(true);
    let tries = 0;
    clearInterval(timer.current);
    timer.current = setInterval(async () => {
      tries += 1;
      const s = await api('/telegram').catch(() => null);
      if (s?.linked || tries >= POLL_TRIES) {
        clearInterval(timer.current);
        setWaiting(false);
        if (s) setState(s);
      }
    }, POLL_MS);
  };

  const connect = async () => {
    // open the tab right away (a tab opened after an await is often blocked as a pop-up)
    const tab = window.open('', '_blank');
    try {
      const { url } = await api('/telegram/link', { method: 'POST' });
      if (tab) tab.location.href = url;
      else window.location.href = url;
      waitForStart();
    } catch (e) {
      tab?.close();
      notify(`Не вдалося підключити Telegram: ${e.message}`);
    }
  };

  const disconnect = async () => {
    try {
      await api('/telegram', { method: 'DELETE' });
      setState((s) => ({ ...s, linked: false }));
    } catch (e) {
      notify(`Не вдалося вимкнути: ${e.message}`);
    }
  };

  if (!state?.available) return null;

  return (
    <div className="card tg-alerts">
      <div className="tg-alerts__text">
        <span className="eyebrow">Сповіщення в Telegram</span>
        {state.linked ? (
          <p>
            <strong>Увімкнено.</strong> Бот напише, щойно хтось поставить на полицю книгу з вашого
            вішліста.
          </p>
        ) : waiting ? (
          <p>
            Натисніть <strong>Start</strong> у Telegram — ця сторінка сама побачить, що бот
            підключено.
          </p>
        ) : (
          <p>
            Дізнавайтеся першими: бот напише, щойно на полиці з’явиться книга з вашого вішліста.
          </p>
        )}
      </div>
      {state.linked ? (
        <button type="button" className="btn--ghost btn--small" onClick={disconnect}>
          Вимкнути
        </button>
      ) : (
        <button type="button" className="btn--small" onClick={connect}>
          {waiting ? 'Відкрити бота ще раз' : 'Підключити Telegram'}
        </button>
      )}
    </div>
  );
}

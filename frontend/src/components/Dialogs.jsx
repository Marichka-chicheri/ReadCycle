import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

// Site-styled replacements for window.confirm / window.alert.
//   const { confirm, notify } = useDialogs();
//   if (!(await confirm({ title: 'Прибрати книгу?', confirmLabel: 'Прибрати', danger: true }))) return;
//   notify(`Не вдалося видалити: ${e.message}`);
// confirm() resolves to true / false; notify() shows a note in the corner that fades by itself.

const DialogsContext = createContext(null);

const NOTE_MS = 6000;

export function DialogsProvider({ children }) {
  const [ask, setAsk] = useState(null); // { title, message, confirmLabel, cancelLabel, danger, resolve }
  const [notes, setNotes] = useState([]); // [{ id, text, tone }]
  const nextId = useRef(1);

  const confirm = useCallback((opts) => new Promise((resolve) => setAsk({ ...opts, resolve })), []);

  const dismiss = useCallback((id) => setNotes((list) => list.filter((n) => n.id !== id)), []);

  const notify = useCallback(
    (text, tone = 'error') => {
      const id = nextId.current++;
      setNotes((list) => [...list.slice(-2), { id, text, tone }]);
      setTimeout(() => dismiss(id), NOTE_MS);
    },
    [dismiss],
  );

  const answer = useCallback(
    (value) => {
      ask?.resolve(value);
      setAsk(null);
    },
    [ask],
  );

  return (
    <DialogsContext.Provider value={{ confirm, notify }}>
      {children}
      {ask && <ConfirmDialog {...ask} onAnswer={answer} />}
      {notes.length > 0 && (
        <div className="notes" role="status" aria-live="polite">
          {notes.map((n) => (
            <div key={n.id} className={`note note--${n.tone}`}>
              <p>{n.text}</p>
              <button
                type="button"
                className="note__close"
                aria-label="Закрити"
                onClick={() => dismiss(n.id)}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </DialogsContext.Provider>
  );
}

function ConfirmDialog({
  title,
  message,
  confirmLabel = 'Так',
  cancelLabel = 'Скасувати',
  danger,
  onAnswer,
}) {
  const okRef = useRef(null);

  useEffect(() => {
    okRef.current?.focus();
    // Capture phase on window: Esc / Enter must not reach a book dialog lying underneath.
    const onKey = (e) => {
      if (e.key === 'Escape') {
        e.stopPropagation();
        onAnswer(false);
      }
    };
    window.addEventListener('keydown', onKey, true);
    return () => window.removeEventListener('keydown', onKey, true);
  }, [onAnswer]);

  return (
    <div className="confirm" onMouseDown={(e) => e.target === e.currentTarget && onAnswer(false)}>
      <div className="confirm__panel" role="alertdialog" aria-modal aria-labelledby="confirm-title">
        <h3 id="confirm-title">{title}</h3>
        {message && <p>{message}</p>}
        <div className="confirm__actions">
          <button type="button" className="btn--ghost" onClick={() => onAnswer(false)}>
            {cancelLabel}
          </button>
          <button
            type="button"
            ref={okRef}
            className={danger ? 'btn--danger' : ''}
            onClick={() => onAnswer(true)}
          >
            {confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}

export function useDialogs() {
  const ctx = useContext(DialogsContext);
  if (!ctx) throw new Error('useDialogs() must be used inside <DialogsProvider>');
  return ctx;
}

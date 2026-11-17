import { useState } from 'react';
import { api } from '../api.js';
import { REPORT_REASONS } from '../genres.js';

// Complaint about a book or a student. `target` = { target_type, target_id, owner_id? }.
export default function ReportForm({ target, subject, onDone }) {
  const [reason, setReason] = useState('');
  const [comment, setComment] = useState('');
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [sent, setSent] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    setErrors({});
    setMessage('');
    setBusy(true);
    try {
      await api('/reports', {
        method: 'POST',
        body: JSON.stringify({ ...target, reason, comment }),
      });
      setSent(true);
    } catch (error) {
      setErrors(error.fields || {});
      setMessage(error.fields && Object.keys(error.fields).length ? '' : error.message);
    } finally {
      setBusy(false);
    }
  };

  if (sent)
    return (
      <div className="profile-form">
        <p className="ok">Дякуємо! Скаргу отримано, ми її розглянемо.</p>
        <div className="form-actions">
          <button onClick={onDone}>Закрити</button>
        </div>
      </div>
    );

  return (
    <form onSubmit={submit} className="profile-form" noValidate>
      {subject && <p className="muted">Скарга на: {subject}</p>}
      <label>
        Причина
        <select value={reason} onChange={(e) => setReason(e.target.value)}>
          <option value="" disabled>
            Оберіть причину
          </option>
          {REPORT_REASONS.map(([code, label]) => (
            <option key={code} value={code}>
              {label}
            </option>
          ))}
        </select>
        {errors.reason && <span className="field-error">{errors.reason}</span>}
      </label>
      <label>
        <span>
          Що сталося {reason !== 'other' && <span className="optional">необов'язково</span>}
        </span>
        <textarea
          rows={3}
          maxLength={500}
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
        {errors.comment && <span className="field-error">{errors.comment}</span>}
      </label>
      {message && <p className="error">{message}</p>}
      <div className="form-actions">
        <button disabled={busy}>{busy ? 'Надсилаємо…' : 'Надіслати скаргу'}</button>
        <button type="button" className="btn--ghost" onClick={onDone}>
          Скасувати
        </button>
      </div>
    </form>
  );
}

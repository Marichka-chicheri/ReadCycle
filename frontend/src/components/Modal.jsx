import { useEffect } from 'react';

// Simple dialog: dark veil + cream panel. Closes on Esc and on a click outside the panel.
export default function Modal({ title, onClose, children, wide = false }) {
  useEffect(() => {
    const onKey = (e) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    document.body.style.overflow = 'hidden';
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = '';
    };
  }, [onClose]);

  return (
    <div className="modal" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div className={`modal__panel${wide ? ' modal__panel--wide' : ''}`} role="dialog" aria-modal>
        <button type="button" className="modal__close" onClick={onClose} aria-label="Закрити">
          ×
        </button>
        {title && <h2>{title}</h2>}
        {children}
      </div>
    </div>
  );
}

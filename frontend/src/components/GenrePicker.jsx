import { GENRES } from '../genres.js';

// Multi-select genre chips. `max` limits how many can be picked.
export default function GenrePicker({ value = [], onChange, max = 10 }) {
  const toggle = (code) => {
    if (value.includes(code)) onChange(value.filter((g) => g !== code));
    else if (value.length < max) onChange([...value, code]);
  };
  return (
    <div className="chips" role="group">
      {GENRES.map(([code, label]) => {
        const on = value.includes(code);
        return (
          <button
            key={code}
            type="button"
            className={`chip${on ? ' chip--on' : ''}`}
            aria-pressed={on}
            disabled={!on && value.length >= max}
            onClick={() => toggle(code)}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}

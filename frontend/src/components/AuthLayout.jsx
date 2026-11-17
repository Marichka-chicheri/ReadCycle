// Login / register: an open antique book over a dimly lit library.
// The left page is the "frontispiece" with a quote and an ex-libris stamp; the form is on the right.
export default function AuthLayout({ children }) {
  return (
    <div className="auth-scene">
      <div className="tome">
        <section className="tome__page tome__page--verso" aria-hidden="true">
          <span className="tome__ornament">❦</span>
          <p className="tome__kicker">Ex libris · УКУ</p>
          <p className="tome__quote">
            <span className="dropcap">П</span>рочитана книга на твоїй полиці — ще не прочитана для
            когось іншого.
          </p>
          <p className="tome__text">
            ReadCycle — спільна бібліотека з полиць студентів. Постав на свою те, що вже прочитала,
            і знайди те, що давно хотіла.
          </p>
          <span className="tome__stamp">
            ReadCycle
            <small>MMXXVI</small>
          </span>
          <span className="tome__folio">i</span>
        </section>
        <section className="tome__page tome__page--recto">
          {children}
          <span className="tome__folio">ii</span>
        </section>
      </div>
    </div>
  );
}

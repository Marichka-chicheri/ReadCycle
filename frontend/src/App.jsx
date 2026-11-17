import { Link, Navigate, NavLink, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext.jsx';
import ForgotPassword from './pages/ForgotPassword.jsx';
import Home from './pages/Home.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Matches from './pages/Matches.jsx';
import Profile from './pages/Profile.jsx';
import UserProfile from './pages/UserProfile.jsx';
import Welcome from './pages/Welcome.jsx';
import { useProfile } from './ProfileContext.jsx';

// Signed-in pages. Until the user has a profile, every page except /welcome redirects to it.
function ProtectedRoute({ children, onboarding = false }) {
  const { user } = useAuth();
  const { profile, error, reload } = useProfile();
  const location = useLocation();
  if (user === undefined) return <p className="loading">Відчиняємо шафу…</p>;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  if (error)
    return (
      <div className="card narrow">
        <p className="error">Не вдалося завантажити профіль: {error}</p>
        <button onClick={reload}>Спробувати ще раз</button>
      </div>
    );
  if (profile === undefined) return <p className="loading">Відчиняємо шафу…</p>;
  if (profile === null && !onboarding) return <Navigate to="/welcome" replace />;
  return children;
}

// Navigation items. New pages (profile, wishlist, matches) are added here as they appear.
const NAV = [
  { to: '/', title: 'Шафа', caption: 'усі книги' },
  { to: '/matches', title: 'Обмін', caption: 'знайти пару' },
  { to: '/profile', title: 'Профіль', caption: 'моя полиця' },
];

function BrandMark() {
  // an open book, drawn with two strokes
  return (
    <svg
      width="22"
      height="22"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.5"
    >
      <path d="M12 6.5C10 5 7 4.5 3.5 5v13c3.5-.5 6.5 0 8.5 1.5 2-1.5 5-2 8.5-1.5V5C17 4.5 14 5 12 6.5Z" />
      <path d="M12 6.5v13" />
    </svg>
  );
}

function TopBar() {
  const { user, signOut } = useAuth();
  const { profile } = useProfile();
  const name = profile?.display_name || user?.email || '';
  return (
    <header className="topbar">
      <div className="topbar__inner">
        <Link to="/" className="brand">
          <span className="brand__mark">
            <BrandMark />
          </span>
          <span className="brand__name">ReadCycle</span>
        </Link>
        {user && (
          <>
            {/* menu appears once the profile exists; sign-out is always available */}
            <nav className="nav">
              {profile &&
                NAV.map((n) => (
                  <NavLink key={n.to} to={n.to} end>
                    <span>{n.title}</span>
                    <small>{n.caption}</small>
                  </NavLink>
                ))}
            </nav>
            <div className="topbar__user">
              <span className="email">{name}</span>
              <span className="avatar" aria-hidden="true">
                {profile?.avatar_src ? (
                  <img src={profile.avatar_src} alt="" />
                ) : (
                  name[0]?.toUpperCase()
                )}
              </span>
              <button className="btn-signout" onClick={signOut}>
                Вийти
              </button>
            </div>
          </>
        )}
      </div>
    </header>
  );
}

export default function App() {
  return (
    <>
      <TopBar />
      <main>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/forgot" element={<ForgotPassword />} />
          {/* Add new protected pages from src/pages here */}
          <Route
            path="/welcome"
            element={
              <ProtectedRoute onboarding>
                <Welcome />
              </ProtectedRoute>
            }
          />
          <Route
            path="/matches"
            element={
              <ProtectedRoute>
                <Matches />
              </ProtectedRoute>
            }
          />
          <Route
            path="/u/:id"
            element={
              <ProtectedRoute>
                <UserProfile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/profile"
            element={
              <ProtectedRoute>
                <Profile />
              </ProtectedRoute>
            }
          />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Home />
              </ProtectedRoute>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </>
  );
}

import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import { useAuth } from './AuthContext.jsx';
import Home from './pages/Home.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';

function ProtectedRoute({ children }) {
  const { user } = useAuth();
  const location = useLocation();
  if (user === undefined) return <p>Завантаження…</p>;
  if (!user) return <Navigate to="/login" replace state={{ from: location }} />;
  return children;
}

export default function App() {
  const { user, signOut } = useAuth();
  return (
    <>
      <header>
        <Link to="/" className="logo">
          ReadCycle
        </Link>
        {user && (
          <span>
            {user.email} <button onClick={signOut}>Вийти</button>
          </span>
        )}
      </header>
      <main>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          {/* Add new protected pages from src/pages here */}
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

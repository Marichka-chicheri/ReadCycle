import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App.jsx';
import { AuthProvider } from './AuthContext.jsx';
import { loadConfig } from './config.js';
import './styles.css';

const root = ReactDOM.createRoot(document.getElementById('root'));

loadConfig()
  .then(() =>
    root.render(
      <React.StrictMode>
        <BrowserRouter>
          <AuthProvider>
            <App />
          </AuthProvider>
        </BrowserRouter>
      </React.StrictMode>,
    ),
  )
  .catch((e) => root.render(<p className="error">Не вдалося завантажити config.json: {e.message}</p>));

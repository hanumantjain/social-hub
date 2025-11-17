import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { BrowserRouter } from 'react-router-dom'
import { GoogleOAuthProvider } from '@react-oauth/google'

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

// Log if Google Client ID is missing (for debugging)
if (!GOOGLE_CLIENT_ID) {
  console.error('VITE_GOOGLE_CLIENT_ID is not set! Google OAuth will not work.');
  console.error('Available env vars:', Object.keys(import.meta.env).filter(k => k.startsWith('VITE_')));
} else {
  console.log('Google OAuth Client ID loaded:', GOOGLE_CLIENT_ID.substring(0, 20) + '...');
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    {GOOGLE_CLIENT_ID ? (
      <GoogleOAuthProvider clientId={GOOGLE_CLIENT_ID}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
      </GoogleOAuthProvider>
    ) : (
      <div style={{ padding: '20px', textAlign: 'center' }}>
        <h1>Configuration Error</h1>
        <p>Google OAuth Client ID is not configured. Please contact support.</p>
      </div>
    )}
  </StrictMode>,
)

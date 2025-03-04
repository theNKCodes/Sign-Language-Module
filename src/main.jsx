import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import SignLanguageApp from './SignLanguageApp.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
    {/* <SignLanguageApp /> */}
  </StrictMode>,
)

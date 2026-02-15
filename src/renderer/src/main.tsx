import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/global.css'
import './styles/components.css'

const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('[main.tsx] Root element #root not found in DOM')
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)

import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

const rootElement = document.getElementById('root');

if (rootElement.hasChildNodes()) {
  // Hydrate pre-rendered content from react-snap
  ReactDOM.hydrateRoot(rootElement, <App />, {
    onRecoverableError: () => {} // Suppress hydration warnings
  });
} else {
  // Normal render for development
  const root = ReactDOM.createRoot(rootElement);
  root.render(<App />);
}
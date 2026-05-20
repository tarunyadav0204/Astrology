import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import App from './App';

function hasAuthToken() {
  try {
    return typeof localStorage !== 'undefined' && !!localStorage.getItem('token');
  } catch {
    return false;
  }
}

const rootElement = document.getElementById('root');
const prerendered = rootElement?.hasChildNodes();
const tokenPresent = hasAuthToken();

if (prerendered && !tokenPresent) {
  // Crawlers / logged-out: static HTML matches first paint when App starts with loading=false (see App.js).
  ReactDOM.hydrateRoot(rootElement, <App />, {
    onRecoverableError: () => {},
  });
} else if (prerendered && tokenPresent) {
  // Logged-in HTML cannot match prerender (always logged-out homepage). Hydrating would mis-bind handlers / user.
  rootElement.textContent = '';
  ReactDOM.createRoot(rootElement).render(<App />);
} else {
  ReactDOM.createRoot(rootElement).render(<App />);
}
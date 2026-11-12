import React from 'react';
import ReactDOM from 'react-dom/client';
import Counter from './Counter';

const container = document.getElementById('react-root');

if (container) {
  ReactDOM.createRoot(container).render(
    <React.StrictMode>
      <Counter />
    </React.StrictMode>
  );
}
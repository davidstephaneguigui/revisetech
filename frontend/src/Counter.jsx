import { useState } from 'react';

export default function Counter() {
  const [count, setCount] = useState(0);

  return (
    <div style={{ border: '2px solid #6a1b9a', padding: '20px', borderRadius: '12px', textAlign: 'center', backgroundColor: '#fdfbfe' }}>
      <h3 style={{ color: '#6a1b9a' }}>Compteur React (Test d'intégration)</h3>
      <p>Vous avez cliqué {count} fois.</p>
      <button
        onClick={() => setCount(count + 1)}
        style={{ padding: '10px 20px', backgroundColor: '#6a1b9a', color: 'white', border: 'none', borderRadius: '8px', cursor: 'pointer' }}
      >
        Cliquez-moi
      </button>
    </div>
  );
}
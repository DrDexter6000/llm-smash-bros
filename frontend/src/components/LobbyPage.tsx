import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './LobbyPage.module.css';

interface Archetype {
  id: string;
  codename: string;
}

export default function LobbyPage() {
  const navigate = useNavigate();
  const [archetypes, setArchetypes] = useState<Archetype[]>([]);
  const [fighter1, setFighter1] = useState('striker');
  const [fighter2, setFighter2] = useState('guardian');
  const [mode, setMode] = useState<'mock' | 'live'>('mock');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/archetypes')
      .then(res => res.json())
      .then(data => setArchetypes(data))
      .catch(err => {
        console.error('Failed to fetch archetypes', err);
        // Fallback for when backend is not running
        setArchetypes([
          { id: 'striker', codename: 'Striker' },
          { id: 'guardian', codename: 'Guardian' },
          { id: 'controller', codename: 'Controller' },
          { id: 'berserker', codename: 'Berserker' }
        ]);
      });
  }, []);

  const handleFight = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch('http://localhost:8000/api/matches', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fighter1_archetype: fighter1, fighter2_archetype: fighter2, mode })
      });
      if (!response.ok) throw new Error('Failed to create match');
      const data = await response.json();
      navigate(`/match/${data.match_id}`);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const replay = JSON.parse(reader.result as string);
        navigate('/replay-local', { state: { replayData: replay } });
      } catch (err) {
        setError('Invalid replay JSON file');
      }
    };
    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
  };

  return (
    <div className={styles.lobbyContainer}>
      <h1 className={styles.title}>LLM SMASH BROS</h1>
      <div className={styles.lobbyCard}>
        <h2 className={styles.subtitle}>Select Your Fighters</h2>
        
        <div className={styles.fighterSelection}>
          <div className={styles.fighterSlot}>
            <label htmlFor="fighter1">Fighter 1</label>
            <select id="fighter1" value={fighter1} onChange={e => setFighter1(e.target.value)}>
              {archetypes.map(a => (
                <option key={a.id} value={a.id}>{a.codename}</option>
              ))}
            </select>
          </div>
          
          <div className={styles.vs}>VS</div>
          
          <div className={styles.fighterSlot}>
            <label htmlFor="fighter2">Fighter 2</label>
            <select id="fighter2" value={fighter2} onChange={e => setFighter2(e.target.value)}>
              {archetypes.map(a => (
                <option key={a.id} value={a.id}>{a.codename}</option>
              ))}
            </select>
          </div>
        </div>

        <div className={styles.options}>
          <label>
            <input 
              type="radio" 
              value="mock" 
              checked={mode === 'mock'} 
              onChange={() => setMode('mock')} 
            />
            Mock Mode
          </label>
          <label>
            <input 
              type="radio" 
              value="live" 
              checked={mode === 'live'} 
              onChange={() => setMode('live')} 
            />
            Live API
          </label>
        </div>

        {error && <div className={styles.error}>{error}</div>}

        <button 
          type="button"
          className={styles.fightButton} 
          onClick={handleFight} 
          disabled={loading}
        >
          {loading ? 'INITIALIZING...' : 'FIGHT!'}
        </button>
      </div>

      <div 
        className={styles.dropZone} 
        onDrop={handleDrop} 
        onDragOver={handleDragOver}
      >
        <p>📥 Drop a CLI replay JSON file here to watch it</p>
      </div>
    </div>
  );
}

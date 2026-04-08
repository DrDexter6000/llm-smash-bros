import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import styles from './MatchHistoryPage.module.css';

interface MatchFighterInfo {
  slot_id: string;
  archetype_id: string;
  codename: string;
  model?: string;
}

interface MatchSummary {
  match_id: string;
  status: string;
  fighters: MatchFighterInfo[];
  winner: string | null;
  turn_count: number;
  created_at: number;
  is_draw: boolean;
  end_reason: string | null;
  total_fumbles: number;
  error: string | null;
}

const ARCHETYPE_ICONS: Record<string, string> = {
  striker: '⚡',
  guardian: '🛡️',
  controller: '🎯',
  berserker: '🔥',
};

function formatRelativeTime(timestamp: number) {
  const diffMs = Date.now() - timestamp * 1000;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'just now';
  if (diffMins < 60) return `${diffMins} min ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours} hours ago`;
  return `${Math.floor(diffHours / 24)} days ago`;
}

export default function MatchHistoryPage() {
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch('http://localhost:8000/api/matches?limit=50')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load history');
        return res.json();
      })
      .then((data) => {
        setMatches(data);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, []);

  if (loading) return <div className={styles.loading}>Loading history...</div>;
  if (error) return <div className={styles.error}>{error}</div>;

  return (
    <div className={styles.container}>
      <h1 className={styles.title}>Match History</h1>
      {matches.length === 0 ? (
        <div className={styles.empty}>No matches played yet.</div>
      ) : (
        <div className={styles.grid}>
          {matches.map((match) => (
            <div key={match.match_id} className={styles.card}>
              <div className={styles.cardHeader}>
                <span className={styles.matchId}>#{match.match_id.substring(0, 8)}</span>
                <span className={styles.time}>{formatRelativeTime(match.created_at)}</span>
              </div>
              
              <div className={styles.fighters}>
                {match.fighters.map((f, i) => (
                  <span key={f.slot_id}>
                    {i > 0 && <span className={styles.vs}> VS </span>}
                    {ARCHETYPE_ICONS[f.archetype_id] || ''} {f.codename} 
                    <span className={styles.modelName}> ({f.model || 'Mock'})</span>
                  </span>
                ))}
              </div>

              <div className={styles.stats}>
                <div>Winner: <strong className={styles.winner}>{match.is_draw ? 'DRAW' : match.winner || 'None'}</strong></div>
                <div>Turns: {match.turn_count}</div>
              </div>

              <div className={styles.actions}>
                <Link to={`/replay/${match.match_id}`} className={styles.replayBtn}>
                  Watch Replay →
                </Link>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

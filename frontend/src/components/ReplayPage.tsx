import { useEffect, useState } from 'react';
import { useParams, useLocation, useNavigate } from 'react-router-dom';
import MatchLayout from './MatchLayout';
import { useReplayPlayback, type ReplayData } from '../hooks/useReplayPlayback';
import styles from './ReplayPage.module.css';

export default function ReplayPage() {
  const { matchId } = useParams<{ matchId: string }>();
  const location = useLocation();
  const navigate = useNavigate();
  const [replayData, setReplayData] = useState<ReplayData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    if (location.state?.replayData) {
      setReplayData(location.state.replayData);
      setLoading(false);
      return;
    }

    if (matchId) {
      fetch(`http://localhost:8000/api/matches/${matchId}/replay`)
        .then((res) => {
          if (res.status === 404) throw new Error('Replay not found');
          if (!res.ok) throw new Error('Failed to load replay');
          return res.json();
        })
        .then((data) => {
          setReplayData(data);
        })
        .catch((err) => {
          setError(err.message);
        })
        .finally(() => {
          setLoading(false);
        });
    } else {
      setError('No match ID or replay data provided');
      setLoading(false);
    }
  }, [matchId, location.state]);

  const {
    currentTurn,
    totalTurns,
    displayState,
    isPlaying,
    speed,
    play,
    pause,
    setSpeed,
    stepForward,
    stepBackward,
    seekTo,
  } = useReplayPlayback(replayData);

  if (loading) return <div className={styles.loading}>Loading Replay...</div>;
  if (error) return (
    <div className={styles.errorScreen}>
      <h2>Error</h2>
      <p>{error}</p>
      <button type="button" onClick={() => navigate('/')}>Back to Lobby</button>
    </div>
  );
  if (!replayData || !displayState) return <div className={styles.loading}>Processing Replay...</div>;

  return (
    <div className={styles.replayPage}>
      <div className={styles.playbackBar}>
        <div className={styles.controlsLeft}>
          <button type="button" onClick={() => seekTo(0)} disabled={currentTurn === 0} title="Jump to Start">⏮</button>
          <button type="button" onClick={stepBackward} disabled={currentTurn === 0} title="Step Backward">◀</button>
          <button type="button" onClick={isPlaying ? pause : play} title="Play/Pause">
            {isPlaying ? '⏸' : '▶'}
          </button>
          <button type="button" onClick={stepForward} disabled={currentTurn === totalTurns - 1} title="Step Forward">▶</button>
          <button type="button" onClick={() => seekTo(totalTurns - 1)} disabled={currentTurn === totalTurns - 1} title="Jump to End">⏭</button>
        </div>

        <div className={styles.scrubberContainer}>
          <input 
            type="range" 
            min={0} 
            max={totalTurns - 1} 
            value={currentTurn}
            onChange={(e) => seekTo(Number(e.target.value))}
            className={styles.scrubber}
          />
          <div className={styles.turnLabel}>
            {currentTurn + 1} / {totalTurns}
          </div>
        </div>

        <div className={styles.speedControls}>
          <span>Speed:</span>
          {[0.5, 1, 2, 4].map(s => (
            <button 
              key={s} 
              type="button"
              className={speed === s ? styles.activeSpeed : ''} 
              onClick={() => setSpeed(s)}
            >
              {s}x
            </button>
          ))}
        </div>
      </div>

      <MatchLayout state={displayState} />
    </div>
  );
}

import 'react';
import { useMatchWebSocket } from '../hooks/useMatchWebSocket';
import { useTurnPacer } from '../hooks/useTurnPacer';
import MatchLayout from './MatchLayout';
import styles from './MatchPage.module.css';

interface MatchPageProps {
  matchId: string;
  onExit: () => void;
}

export default function MatchPage({ matchId, onExit }: MatchPageProps) {
  const wsState = useMatchWebSocket(matchId);
  const pacer = useTurnPacer(wsState.battleState, wsState.turns);
  
  if (wsState.status === 'connecting') {
    return <div className={styles.loading}>Connecting to Arena...</div>;
  }
  
  if (wsState.status === 'error') {
    return (
      <div className={styles.errorScreen}>
        <h2>Connection Error</h2>
        <p>{wsState.error}</p>
        <button onClick={onExit} type="button">Back to Lobby</button>
      </div>
    );
  }

  const stateToRender = pacer.displayState || wsState.battleState;

  if (!stateToRender) {
    return <div className={styles.loading}>Waiting for match data...</div>;
  }

  return (
    <div className={styles.matchPage}>
      <div className={styles.controls}>
        <button onClick={() => pacer.setIsPaused(!pacer.isPaused)} type="button">
          {pacer.isPaused ? '▶ Resume' : '⏸ Pause'}
        </button>
        <select value={pacer.speed} onChange={(e) => pacer.setSpeed(Number(e.target.value))}>
          <option value={1}>1x Speed</option>
          <option value={2}>2x Speed</option>
          <option value={4}>4x Speed</option>
        </select>
        <button onClick={pacer.skipToEnd} type="button">⏭ Skip to End</button>
        <button onClick={onExit} type="button">Exit Match</button>
      </div>

      <MatchLayout state={stateToRender} />

      {/* Intro Overlay */}
      {wsState.battleState && pacer.currentTurnLog === null && (
        <div className={styles.introOverlay}>
          <h1>FIGHT!</h1>
          <p>{stateToRender.fighters[0]?.model_name} VS {stateToRender.fighters[1]?.model_name}</p>
        </div>
      )}

      {/* End Match Overlay */}
      {wsState.matchResult && (
        <div className={styles.endOverlay}>
          <h1>MATCH OVER</h1>
          <h2>{wsState.matchResult.winner ? `${wsState.matchResult.winner} WINS!` : 'DRAW!'}</h2>
          <p>Reason: {wsState.matchResult.reason}</p>
          <button onClick={onExit} type="button">Back to Lobby</button>
        </div>
      )}
    </div>
  );
}

import type { BattleState } from '../types/game';
import ArenaGrid from './ArenaGrid';
import FighterPanel from './FighterPanel';
import styles from './MatchLayout.module.css';

interface MatchLayoutProps {
  state: BattleState;
}

export default function MatchLayout({ state }: MatchLayoutProps) {
  const [fighter1, fighter2] = state.fighters;

  return (
    <div className={styles.layout}>
      <header className={styles.header}>
        <h1 className={styles.title}>LLM SMASH BROS</h1>
        <div className={styles.turnInfo}>Turn {state.turn_number}</div>
      </header>

      <main className={styles.mainContent}>
        {fighter1 && <FighterPanel fighter={fighter1} />}
        
        <div className={styles.centerStage}>
          <ArenaGrid arena={state.arena} fighters={state.fighters} />
        </div>

        {fighter2 && <FighterPanel fighter={fighter2} />}
      </main>

      <footer className={styles.eventLogArea}>
        <div className={styles.eventLogTitle}>Event Log</div>
        <div className={styles.eventLogContent}>
          {/* Placeholder for event log */}
          <div className={styles.logPlaceholder}>
            Waiting for events...
          </div>
        </div>
      </footer>
    </div>
  );
}

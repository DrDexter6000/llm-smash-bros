import { Arena, Fighter, Hazard } from '../types/game';
import FighterToken from './FighterToken';
import styles from './ArenaGrid.module.css';

interface ArenaGridProps {
  arena: Arena;
  fighters: Fighter[];
}

function HazardIndicator({ hazard }: { hazard: Hazard }) {
  return (
    <div className={styles.hazardIndicator}>
      <span className={styles.hazardIcon}>🔥</span>
      <span className={styles.hazardTurns}>{hazard.turns_remaining}</span>
    </div>
  );
}

export default function ArenaGrid({ arena, fighters }: ArenaGridProps) {
  const cells = [];
  for (let y = 0; y < arena.height; y++) {
    for (let x = 0; x < arena.width; x++) {
      const terrain = arena.terrain[`${x},${y}`] || "open";
      const fighter = fighters.find(f => f.position.x === x && f.position.y === y);
      const hazard = arena.hazards.find(h => h.position.x === x && h.position.y === y);
      
      cells.push(
        <div key={`${x},${y}`} className={`${styles.cell} ${styles[`terrain_${terrain}`]}`}>
          {hazard && <HazardIndicator hazard={hazard} />}
          {fighter && <FighterToken fighter={fighter} />}
        </div>
      );
    }
  }

  return (
    <div 
      className={styles.arenaGrid} 
      style={{
        gridTemplateColumns: `repeat(${arena.width}, 1fr)`,
        gridTemplateRows: `repeat(${arena.height}, 1fr)`,
      }}
    >
      {cells}
    </div>
  );
}

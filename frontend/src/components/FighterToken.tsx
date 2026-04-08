import type { Fighter } from '../types/game';
import styles from './FighterToken.module.css';

interface FighterTokenProps {
  fighter: Fighter;
  gridWidth?: number;
  gridHeight?: number;
}

export default function FighterToken({ fighter, gridWidth = 8, gridHeight = 8 }: FighterTokenProps) {
  const archetypeIcons: Record<string, string> = {
    striker: "⚡",
    guardian: "🛡️",
    controller: "🎯",
    berserker: "🔥",
  };

  const hpPercent = Math.max(0, Math.min(100, (fighter.hp / fighter.max_hp) * 100));
  
  let hpColor = "var(--hp-high)";
  if (hpPercent < 25) {
    hpColor = "var(--hp-low)";
  } else if (hpPercent <= 50) {
    hpColor = "var(--hp-mid)";
  }

  // Calculate transform percentage based on grid size
  const xPercent = (fighter.position.x / gridWidth) * 100;
  const yPercent = (fighter.position.y / gridHeight) * 100;

  return (
    <div 
      className={`${styles.fighterToken} ${styles[`token_${fighter.archetype}`]}`}
      style={{
        transform: `translate(${xPercent}%, ${yPercent}%)`,
        width: `${100 / gridWidth}%`,
        height: `${100 / gridHeight}%`,
      }}
    >
      <div className={styles.tokenInner}>
        <span className={styles.fighterIcon}>{archetypeIcons[fighter.archetype] || "❓"}</span>
        <div className={styles.hpBarContainer}>
          <div 
            className={styles.hpBarFill} 
            style={{ 
              width: `${hpPercent}%`,
              backgroundColor: hpColor
            }} 
          />
        </div>
      </div>
    </div>
  );
}

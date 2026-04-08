import { Fighter } from '../types/game';
import styles from './FighterToken.module.css';

interface FighterTokenProps {
  fighter: Fighter;
}

export default function FighterToken({ fighter }: FighterTokenProps) {
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

  return (
    <div className={`${styles.fighterToken} ${styles[`token_${fighter.archetype}`]}`}>
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
  );
}

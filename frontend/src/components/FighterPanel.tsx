import { Fighter } from '../types/game';
import styles from './FighterPanel.module.css';

interface FighterPanelProps {
  fighter: Fighter;
}

export default function FighterPanel({ fighter }: FighterPanelProps) {
  const hpPercent = Math.max(0, Math.min(100, (fighter.hp / fighter.max_hp) * 100));
  const energyPercent = Math.max(0, Math.min(100, (fighter.energy / fighter.max_energy) * 100));
  
  let hpColor = "var(--hp-high)";
  if (hpPercent < 25) {
    hpColor = "var(--hp-low)";
  } else if (hpPercent <= 50) {
    hpColor = "var(--hp-mid)";
  }

  const archetypeIcons: Record<string, string> = {
    striker: "⚡",
    guardian: "🛡️",
    controller: "🎯",
    berserker: "🔥",
  };

  return (
    <div className={styles.fighterPanel}>
      <div className={styles.header}>
        <div className={styles.headerIcon}>{archetypeIcons[fighter.archetype] || "❓"}</div>
        <div className={styles.headerText}>
          <div className={styles.archetype}>{fighter.archetype.toUpperCase()}</div>
          <div className={styles.modelName}>{fighter.model_name}</div>
        </div>
      </div>

      <div className={styles.stats}>
        <div className={styles.statRow}>
          <span className={styles.statLabel}>HP</span>
          <div className={styles.barTrack}>
            <div className={styles.barFill} style={{ width: `${hpPercent}%`, backgroundColor: hpColor }} />
          </div>
          <span className={styles.statValue}>{fighter.hp}/{fighter.max_hp}</span>
        </div>
        
        <div className={styles.statRow}>
          <span className={styles.statLabel}>EN</span>
          <div className={styles.barTrack}>
            <div className={styles.barFill} style={{ width: `${energyPercent}%`, backgroundColor: "var(--energy-bar)" }} />
          </div>
          <span className={styles.statValue}>{fighter.energy}/{fighter.max_energy}</span>
        </div>
      </div>

      {fighter.status_effects.length > 0 && (
        <div className={styles.statusEffects}>
          <div className={styles.sectionTitle}>STATUS</div>
          {fighter.status_effects.map((effect) => (
            <div key={effect.type} className={`${styles.statusBadge} ${styles[`status_${effect.type}`] || styles.status_default}`}>
              {effect.type.replace('_', ' ').toUpperCase()} ({effect.remaining_turns}t)
            </div>
          ))}
        </div>
      )}

      <div className={styles.abilities}>
        <div className={styles.sectionTitle}>ABILITIES</div>
        <div className={styles.abilityList}>
          {fighter.abilities.map((ability) => (
            <div key={ability.name} className={`${styles.abilityItem} ${ability.cooldown_remaining > 0 ? styles.abilityCooldown : ''}`}>
              <div className={styles.abilityHeader}>
                <span className={styles.abilityName}>{ability.name}</span>
                <span className={styles.abilityStatus}>
                  {ability.cooldown_remaining > 0 ? `${ability.cooldown_remaining}cd` : 'rdy'}
                </span>
              </div>
              <div className={styles.abilityDesc}>{ability.description}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
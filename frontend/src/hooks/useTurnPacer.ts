import { useState, useEffect } from 'react';
import type { BattleState, TurnLog, TurnAction } from '../types/game';

interface TurnPacerResult {
  displayState: BattleState | null;
  currentTurnLog: TurnLog | null;
  isPaused: boolean;
  setIsPaused: (val: boolean) => void;
  speed: number;
  setSpeed: (val: number) => void;
  skipToEnd: () => void;
}

export function useTurnPacer(initialState: BattleState | null, incomingTurns: TurnLog[], onSyncRequest?: () => void): TurnPacerResult {
  const [displayState, setDisplayState] = useState<BattleState | null>(null);
  const [currentTurnIndex, setCurrentTurnIndex] = useState(-1);
  const [isPaused, setIsPaused] = useState(false);
  const [speed, setSpeed] = useState(1);

  useEffect(() => {
    if (!displayState && initialState) {
      setDisplayState(initialState);
    }
  }, [initialState, displayState]);

  useEffect(() => {
    if (isPaused || !displayState) return;

    const interval = setInterval(() => {
      if (currentTurnIndex + 1 < incomingTurns.length) {
        const nextIndex = currentTurnIndex + 1;
        const nextTurn = incomingTurns[nextIndex];
        
        setDisplayState(prev => {
          if (!prev) return prev;
          
          const nextState = JSON.parse(JSON.stringify(prev)) as BattleState;
          nextState.turn_number = nextTurn.turn_number;

          nextTurn.actions.forEach((action: TurnAction) => {
            const fighter = nextState.fighters.find(f => f.id === action.fighter_id);
            if (fighter) {
              if (action.move_direction) {
                switch(action.move_direction) {
                  case 'up': fighter.position.y = Math.max(0, fighter.position.y - 1); break;
                  case 'down': fighter.position.y = Math.min(nextState.arena.height - 1, fighter.position.y + 1); break;
                  case 'left': fighter.position.x = Math.max(0, fighter.position.x - 1); break;
                  case 'right': fighter.position.x = Math.min(nextState.arena.width - 1, fighter.position.x + 1); break;
                }
              }
            }
          });

          return nextState;
        });

        setCurrentTurnIndex(nextIndex);
      }
    }, 1500 / speed);

    return () => clearInterval(interval);
  }, [isPaused, currentTurnIndex, incomingTurns, displayState, speed]);

  const skipToEnd = () => {
    if (incomingTurns.length > 0) {
      const lastIndex = incomingTurns.length - 1;
      setCurrentTurnIndex(lastIndex);
      if (onSyncRequest) onSyncRequest();
    }
  };

  return {
    displayState,
    currentTurnLog: currentTurnIndex >= 0 ? incomingTurns[currentTurnIndex] : null,
    isPaused,
    setIsPaused,
    speed,
    setSpeed,
    skipToEnd
  };
}

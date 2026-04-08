import { useState, useEffect } from 'react';
import type { BattleState, TurnLog } from '../types/game';

export interface ReplayData {
  match_id: string;
  winner: string | null;
  is_draw: boolean;
  total_turns: number;
  total_fumbles: number;
  turn_log: TurnLog[];
  end_reason: string;
}

export interface UseReplayPlaybackReturn {
  currentTurn: number;
  totalTurns: number;
  displayState: BattleState | null;
  isPlaying: boolean;
  speed: number;
  play: () => void;
  pause: () => void;
  setSpeed: (speed: number) => void;
  stepForward: () => void;
  stepBackward: () => void;
  seekTo: (turn: number) => void;
}

export function useReplayPlayback(replay: ReplayData | null): UseReplayPlaybackReturn {
  const [currentTurn, setCurrentTurn] = useState<number>(0);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [speed, setSpeed] = useState<number>(1);
  const [displayState, setDisplayState] = useState<BattleState | null>(null);

  const totalTurns = replay ? replay.turn_log.length : 0;

  useEffect(() => {
    if (!replay || replay.turn_log.length === 0) {
      setDisplayState(null);
      return;
    }

    // Since MatchResult doesn't contain an explicit "initial_state", 
    // and turn_log[].state_after is a full snapshot, we just render state_after of the current turn.
    // If currentTurn is 0, we render turn_log[0].state_after.
    const validTurn = Math.max(0, Math.min(currentTurn, totalTurns - 1));
    if (replay.turn_log[validTurn]?.state_after) {
      setDisplayState(replay.turn_log[validTurn].state_after);
    }
  }, [replay, currentTurn, totalTurns]);

  useEffect(() => {
    if (!isPlaying || !replay || currentTurn >= totalTurns - 1) {
      if (currentTurn >= totalTurns - 1 && isPlaying) {
        setIsPlaying(false);
      }
      return;
    }

    const interval = setInterval(() => {
      setCurrentTurn(prev => {
        if (prev + 1 >= totalTurns - 1) {
          setIsPlaying(false);
          return totalTurns - 1;
        }
        return prev + 1;
      });
    }, 1500 / speed);

    return () => clearInterval(interval);
  }, [isPlaying, replay, currentTurn, totalTurns, speed]);

  const play = () => {
    if (currentTurn >= totalTurns - 1) {
      setCurrentTurn(0);
    }
    setIsPlaying(true);
  };
  
  const pause = () => setIsPlaying(false);
  
  const stepForward = () => {
    pause();
    setCurrentTurn(prev => Math.min(prev + 1, totalTurns - 1));
  };
  
  const stepBackward = () => {
    pause();
    setCurrentTurn(prev => Math.max(prev - 1, 0));
  };
  
  const seekTo = (turn: number) => {
    pause();
    setCurrentTurn(Math.max(0, Math.min(turn, totalTurns - 1)));
  };

  return {
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
  };
}

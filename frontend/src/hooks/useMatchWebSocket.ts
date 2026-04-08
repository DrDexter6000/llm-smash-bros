import { useEffect, useReducer, useRef } from 'react';
import type { BattleState, WsMatchStart, WsTurn, WsMatchEnd, TurnLog, MatchResult } from '../types/game';

type ConnectionState = 'connecting' | 'connected' | 'disconnected' | 'error';

interface MatchWebSocketState {
  status: ConnectionState;
  battleState: BattleState | null;
  turns: TurnLog[];
  matchResult: MatchResult | null;
  error: string | null;
}

type Action =
  | { type: 'SET_STATUS'; payload: ConnectionState }
  | { type: 'SET_ERROR'; payload: string }
  | { type: 'MATCH_START'; payload: WsMatchStart }
  | { type: 'TURN'; payload: WsTurn }
  | { type: 'MATCH_END'; payload: WsMatchEnd }
  | { type: 'STATE_SYNC'; payload: { turns_so_far: TurnLog[], current_state: BattleState } };

function reducer(state: MatchWebSocketState, action: Action): MatchWebSocketState {
  switch (action.type) {
    case 'SET_STATUS':
      return { ...state, status: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload, status: 'error' };
    case 'MATCH_START':
      return {
        ...state,
        battleState: {
          fighters: action.payload.fighters,
          arena: action.payload.arena,
          turn_number: 0,
          match_phase: 'running'
        },
      };
    case 'TURN':
      return {
        ...state,
        turns: [...state.turns, action.payload.turn_log]
      };
    case 'MATCH_END':
      return {
        ...state,
        matchResult: action.payload.result
      };
    case 'STATE_SYNC':
      return {
        ...state,
        battleState: action.payload.current_state,
        turns: action.payload.turns_so_far
      };
    default:
      return state;
  }
}

export function useMatchWebSocket(matchId: string) {
  const [state, dispatch] = useReducer(reducer, {
    status: 'connecting',
    battleState: null,
    turns: [],
    matchResult: null,
    error: null,
  });

  const reconnectCount = useRef(0);
  const maxReconnects = 3;

  useEffect(() => {
    if (!matchId) return;

    let ws: WebSocket;
    let reconnectTimer: number;

    const connect = () => {
      dispatch({ type: 'SET_STATUS', payload: 'connecting' });
      ws = new WebSocket(`ws://localhost:8000/api/matches/${matchId}/ws`);

      ws.onopen = () => {
        dispatch({ type: 'SET_STATUS', payload: 'connected' });
        reconnectCount.current = 0;
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'match_start') {
          dispatch({ type: 'MATCH_START', payload: data });
        } else if (data.type === 'turn') {
          dispatch({ type: 'TURN', payload: data });
        } else if (data.type === 'match_end') {
          dispatch({ type: 'MATCH_END', payload: data });
        } else if (data.type === 'state_sync') {
          dispatch({ type: 'STATE_SYNC', payload: data });
        } else if (data.type === 'error') {
          dispatch({ type: 'SET_ERROR', payload: data.message });
        }
      };

      ws.onclose = () => {
        dispatch({ type: 'SET_STATUS', payload: 'disconnected' });
        if (reconnectCount.current < maxReconnects) {
          reconnectCount.current += 1;
          reconnectTimer = window.setTimeout(connect, 2000);
        } else {
          dispatch({ type: 'SET_ERROR', payload: 'Connection lost' });
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      clearTimeout(reconnectTimer);
      if (ws) {
        ws.close();
      }
    };
  }, [matchId]);

  return state;
}

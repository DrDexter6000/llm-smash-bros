export type TerrainType = "open" | "high_ground" | "cover" | "rift";

export interface Position {
  x: number;
  y: number;
}

export interface StatusEffect {
  type: string;
  value: number;
  remaining_turns: number;
}

export interface Ability {
  name: string;
  type: string;
  damage: number;
  energy_cost: number;
  range: number;
  cooldown: number;
  cooldown_remaining: number;
  description: string;
}

export interface Fighter {
  id: string;
  archetype: string;
  model_name: string;
  hp: number;
  max_hp: number;
  energy: number;
  max_energy: number;
  position: Position;
  status_effects: StatusEffect[];
  abilities: Ability[];
}

export interface Hazard {
  type: string;
  position: Position;
  damage: number;
  turns_remaining: number;
}

export interface Arena {
  width: number;
  height: number;
  terrain: Record<string, TerrainType>;  // "x,y" -> terrain type
  hazards: Hazard[];
}

export interface BattleState {
  fighters: Fighter[];
  arena: Arena;
  turn_number: number;
  match_phase: string;
}

// WebSocket message types (for Phase 4, defined now for type safety)
export interface WsMatchStart {
  type: "match_start";
  match_id: string;
  fighters: Fighter[];
  arena: Arena;
}

export interface WsTurn {
  type: "turn";
  turn_number: number;
  turn_log: TurnLog;
}

export interface WsMatchEnd {
  type: "match_end";
  result: MatchResult;
}

export interface TurnLog {
  turn_number: number;
  actions: TurnAction[];
  events: TurnEvent[];
  state_after?: BattleState;
}

export interface TurnAction {
  fighter_id: string;
  action_type: string;
  ability?: string;
  move_direction?: string;
  tactical_summary?: string;
  trash_talk?: string;
}

export interface TurnEvent {
  type: string;
  description: string;
}

export interface MatchResult {
  winner: string | null;
  reason: string;
  total_turns: number;
}

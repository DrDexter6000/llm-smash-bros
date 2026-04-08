import { useState } from 'react';
import LobbyPage from './components/LobbyPage';
import MatchPage from './components/MatchPage';

function App() {
  const [currentMatchId, setCurrentMatchId] = useState<string | null>(null);

  if (currentMatchId) {
    return <MatchPage matchId={currentMatchId} onExit={() => setCurrentMatchId(null)} />;
  }

  return <LobbyPage onFight={(matchId) => setCurrentMatchId(matchId)} />;
}

export default App

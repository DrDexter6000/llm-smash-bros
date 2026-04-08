import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LobbyPage from './components/LobbyPage';
import MatchPage from './components/MatchPage';
import MatchHistoryPage from './components/MatchHistoryPage';
import ReplayPage from './components/ReplayPage';
import NavBar from './components/NavBar';

function App() {
  return (
    <BrowserRouter>
      <NavBar />
      <Routes>
        <Route path="/" element={<LobbyPage />} />
        <Route path="/match/:matchId" element={<MatchPage />} />
        <Route path="/history" element={<MatchHistoryPage />} />
        <Route path="/replay/:matchId" element={<ReplayPage />} />
        <Route path="/replay-local" element={<ReplayPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;

import { Link, useLocation } from 'react-router-dom';
import styles from './NavBar.module.css';

export default function NavBar() {
  const location = useLocation();

  return (
    <nav className={styles.navbar}>
      <div className={styles.brand}>⚔️ LLM Smash Bros</div>
      <div className={styles.links}>
        <Link to="/" className={location.pathname === '/' ? styles.active : ''}>
          [New Match]
        </Link>
        <Link to="/history" className={location.pathname === '/history' ? styles.active : ''}>
          [History]
        </Link>
      </div>
    </nav>
  );
}

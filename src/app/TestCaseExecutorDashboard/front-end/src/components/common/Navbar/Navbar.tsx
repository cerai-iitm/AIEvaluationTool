import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Navbar.module.css';
import logo from '../../../../src/assets/logo/cerai-logo.png';
import iit from '../../../../src/assets/iitm/iit-logo.png';
import wsai from '../../../../src/assets/logo/WSAI_Logo.png';
import { logoutAndRedirect } from '../../../utils/auth';

const Navbar: React.FC = () => {
  return (
    <nav className={styles.navbar}>
      <div className={styles.navContainer}>
        {/* Left Section: Branding/Title */}
        <div className={styles.brandSection}>
          <h1 className={styles.navTitle}>AI Evaluation Tool</h1>
        </div>

        {/* Right Section: User info and Logout */}
        <div className={styles.userSection}>
          <span className={styles.userName}>
            {localStorage.getItem('user_name') || 'User'}
          </span>
          <button onClick={logoutAndRedirect} className={styles.logoutButton}>
            Logout
          </button>

          <div className={styles.divider}></div>

          <Link to="/" className={styles.logoWrapper}>
            <img src={logo} alt="Partner Logo 1" className={styles.logoImage} />
          </Link>

          <div className={styles.divider}></div>

          <Link to="/" className={styles.logoWrapper}>
            <img src={wsai} alt="Partner Logo 2" className={styles.logoImage} />
          </Link>

          <div className={styles.divider}></div>

          <Link to="/" className={styles.logoWrapper}>
            <img src={iit} alt="Partner Logo 3" className={styles.logoImage} />
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;

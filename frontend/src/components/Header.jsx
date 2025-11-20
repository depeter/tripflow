import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useAuth } from '../context/AuthContext';
import './Header.css';

const Header = () => {
  const { t, i18n } = useTranslation(['common']);
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showLanguageMenu, setShowLanguageMenu] = useState(false);
  const menuRef = useRef(null);
  const languageMenuRef = useRef(null);

  // Close menus when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
      if (languageMenuRef.current && !languageMenuRef.current.contains(event.target)) {
        setShowLanguageMenu(false);
      }
    };

    if (showUserMenu || showLanguageMenu) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showUserMenu, showLanguageMenu]);

  const handleLogout = () => {
    logout();
    setShowUserMenu(false);
    navigate('/login');
  };

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng);
    setShowLanguageMenu(false);
  };

  const languages = [
    { code: 'en', name: t('language.en'), flag: '🇬🇧' },
    { code: 'nl', name: t('language.nl'), flag: '🇳🇱' },
  ];

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  const getInitials = (name) => {
    if (!name) return user?.email?.charAt(0).toUpperCase() || 'U';
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2);
  };

  return (
    <header className="header">
      <div className="header-container">
        <Link to="/" className="header-logo">
          <svg width="32" height="32" viewBox="0 0 32 32" fill="none">
            <path
              d="M16 2L3 9V23L16 30L29 23V9L16 2Z"
              fill="var(--primary-green)"
            />
            <path
              d="M16 10L10 13V19L16 22L22 19V13L16 10Z"
              fill="white"
            />
          </svg>
          <span className="header-title">TripFlow</span>
        </Link>

        <nav className="header-nav">
          {isAuthenticated ? (
            <>
              <Link to="/" className="nav-link">
                {t('header.discovery')}
              </Link>
              <Link to="/plan-trip" className="nav-link">
                {t('header.planTrip')}
              </Link>
              <Link to="/my-trips" className="nav-link">
                {t('header.myTrips')}
              </Link>

              <div className="user-menu-wrapper" ref={menuRef}>
                <button
                  className="user-menu-button"
                  onClick={() => setShowUserMenu(!showUserMenu)}
                  aria-label="User menu"
                >
                  <div className="user-avatar">
                    {user?.avatar_url ? (
                      <img src={user.avatar_url} alt={user.full_name || user.email} />
                    ) : (
                      <span>{getInitials(user?.full_name)}</span>
                    )}
                  </div>
                  <svg
                    width="16"
                    height="16"
                    viewBox="0 0 16 16"
                    fill="currentColor"
                    className={`chevron ${showUserMenu ? 'open' : ''}`}
                  >
                    <path
                      fillRule="evenodd"
                      d="M4.293 5.293a1 1 0 011.414 0L8 7.586l2.293-2.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                      clipRule="evenodd"
                    />
                  </svg>
                </button>

                {showUserMenu && (
                  <div className="user-menu-dropdown">
                    <div className="user-menu-header">
                      <div className="user-info">
                        <p className="user-name">{user?.full_name || 'User'}</p>
                        <p className="user-email">{user?.email}</p>
                      </div>
                      {user?.subscription_tier && (
                        <span className="subscription-badge">
                          {user.subscription_tier}
                        </span>
                      )}
                    </div>

                    <div className="user-menu-divider"></div>

                    <Link
                      to="/profile"
                      className="user-menu-item"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path
                          fillRule="evenodd"
                          d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {t('header.profile')}
                    </Link>

                    <Link
                      to="/settings"
                      className="user-menu-item"
                      onClick={() => setShowUserMenu(false)}
                    >
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path
                          fillRule="evenodd"
                          d="M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {t('header.settings')}
                    </Link>

                    <div className="user-menu-divider"></div>

                    <button className="user-menu-item logout" onClick={handleLogout}>
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor">
                        <path
                          fillRule="evenodd"
                          d="M3 3a1 1 0 00-1 1v12a1 1 0 001 1h12a1 1 0 001-1V4a1 1 0 00-1-1H3zm11 4.414l-4.293 4.293a1 1 0 01-1.414 0L5 8.414 6.414 7l3.293 3.293L13.586 6 15 7.414z"
                          clipRule="evenodd"
                        />
                      </svg>
                      {t('header.signOut')}
                    </button>
                  </div>
                )}
              </div>
            </>
          ) : (
            <div className="auth-buttons">
              <Link to="/login" className="btn btn-outline">
                {t('header.signIn')}
              </Link>
              <Link to="/register" className="btn btn-primary">
                {t('header.getStarted')}
              </Link>
            </div>
          )}

          {/* Language Switcher */}
          <div className="language-menu-wrapper" ref={languageMenuRef}>
            <button
              className="language-button"
              onClick={() => setShowLanguageMenu(!showLanguageMenu)}
              aria-label="Change language"
            >
              <span className="language-flag">{currentLanguage.flag}</span>
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="currentColor"
                className={`chevron ${showLanguageMenu ? 'open' : ''}`}
              >
                <path
                  fillRule="evenodd"
                  d="M4.293 5.293a1 1 0 011.414 0L8 7.586l2.293-2.293a1 1 0 111.414 1.414l-3 3a1 1 0 01-1.414 0l-3-3a1 1 0 010-1.414z"
                  clipRule="evenodd"
                />
              </svg>
            </button>

            {showLanguageMenu && (
              <div className="language-menu-dropdown">
                {languages.map((lang) => (
                  <button
                    key={lang.code}
                    className={`language-menu-item ${i18n.language === lang.code ? 'active' : ''}`}
                    onClick={() => changeLanguage(lang.code)}
                  >
                    <span className="language-flag">{lang.flag}</span>
                    <span>{lang.name}</span>
                    {i18n.language === lang.code && (
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" className="check-icon">
                        <path
                          fillRule="evenodd"
                          d="M13.854 3.646a.5.5 0 010 .708l-7 7a.5.5 0 01-.708 0l-3.5-3.5a.5.5 0 11.708-.708L6.5 10.293l6.646-6.647a.5.5 0 01.708 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </button>
                ))}
              </div>
            )}
          </div>
        </nav>
      </div>
    </header>
  );
};

export default Header;

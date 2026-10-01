import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Menu,
  ChevronDown,
  Globe,
  Check,
  LogOut,
  Settings,
  Sparkles,
  User as UserIcon,
} from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { useUiStore } from '../../stores/uiStore';
import { Badge } from '../ui/Badge';
import './Navbar.css';

export function Navbar() {
  const navigate = useNavigate();
  const { user, activeLanguage, switchPrimaryLanguage, logout } = useAuthStore();
  const { toggleSidebar, addToast } = useUiStore();

  const [langMenuOpen, setLangMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const langRef = useRef(null);
  const userRef = useRef(null);

  // Close dropdowns on outside click
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (langRef.current && !langRef.current.contains(e.target)) {
        setLangMenuOpen(false);
      }
      if (userRef.current && !userRef.current.contains(e.target)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleLanguageSwitch = async (langId) => {
    try {
      await switchPrimaryLanguage(langId);
      setLangMenuOpen(false);
      addToast({
        title: 'Primary Language Updated',
        message: 'Your active learning context has been updated.',
        type: 'success',
      });
    } catch (err) {
      addToast({
        title: 'Switch Failed',
        message: err.response?.data?.detail || 'Could not update primary language.',
        type: 'error',
      });
    }
  };

  const handleLogout = async () => {
    try {
      await logout();
      addToast({
        title: 'Signed out',
        message: 'You have been safely signed out.',
        type: 'info',
      });
      navigate('/login');
    } catch {
      navigate('/login');
    }
  };

  const enrolledLanguages = user?.user_languages || [];
  const initial = user?.username ? user.username[0].toUpperCase() : 'U';

  return (
    <header className="navbar">
      <div className="navbar-left">
        <button
          type="button"
          className="navbar-sidebar-toggle"
          onClick={toggleSidebar}
          aria-label="Toggle sidebar"
        >
          <Menu size={20} />
        </button>

        <div className="navbar-brand-mobile">
          <div
            style={{
              width: '28px',
              height: '28px',
              backgroundColor: 'var(--color-primary)',
              borderRadius: 'var(--radius-xs)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 'bold',
              fontSize: '14px',
            }}
          >
            F
          </div>
          <span style={{ fontWeight: 'bold', fontSize: '16px' }}>FluentFlow</span>
        </div>
      </div>

      <div className="navbar-right">
        {/* Language Selector */}
        <div className="lang-selector-container" ref={langRef}>
          <button
            type="button"
            className="lang-selector-btn"
            onClick={() => setLangMenuOpen((prev) => !prev)}
            aria-haspopup="true"
            aria-expanded={langMenuOpen}
          >
            <Globe size={16} color="var(--color-olive)" />
            <span>
              {activeLanguage?.language_name || 'English (US)'}
            </span>
            <Badge variant="lemon" style={{ padding: '1px 6px', fontSize: '10px' }}>
              {activeLanguage?.current_cefr_level || user?.cefr_level || 'B1'}
            </Badge>
            <ChevronDown size={14} />
          </button>

          {langMenuOpen && (
            <div className="lang-menu-dropdown" role="menu">
              <div className="lang-menu-header">Enrolled Languages</div>
              {enrolledLanguages.length === 0 ? (
                <div style={{ padding: 'var(--space-2) var(--space-3)', fontSize: 'var(--font-size-xs)', color: 'var(--color-text-muted)' }}>
                  No extra languages enrolled.
                </div>
              ) : (
                enrolledLanguages.map((ul) => {
                  const isCurrent = ul.id === activeLanguage?.id || ul.is_primary;
                  return (
                    <button
                      key={ul.id}
                      type="button"
                      className={`lang-menu-item ${isCurrent ? 'active' : ''}`}
                      onClick={() => handleLanguageSwitch(ul.id)}
                    >
                      <div style={{ display: 'flex', flexDirection: 'column' }}>
                        <span style={{ fontWeight: isCurrent ? 600 : 400 }}>
                          {ul.language_name || ul.language_code || 'English'}
                        </span>
                        <span style={{ fontSize: '10px', color: 'var(--color-text-muted)' }}>
                          Goal: {ul.target_goal || 'General Fluency'}
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                        <Badge variant={isCurrent ? 'olive' : 'muted'} style={{ fontSize: '10px' }}>
                          {ul.current_cefr_level}
                        </Badge>
                        {isCurrent && <Check size={14} color="var(--color-olive)" />}
                      </div>
                    </button>
                  );
                })
              )}
            </div>
          )}
        </div>

        {/* User Avatar Menu */}
        <div className="user-menu-container" ref={userRef}>
          <button
            type="button"
            className="user-avatar-btn"
            onClick={() => setUserMenuOpen((prev) => !prev)}
            aria-haspopup="true"
            aria-expanded={userMenuOpen}
          >
            <div className="user-avatar">{initial}</div>
            <ChevronDown size={14} color="var(--color-text-secondary)" />
          </button>

          {userMenuOpen && (
            <div className="user-dropdown" role="menu">
              <div className="user-dropdown-info">
                <p className="user-dropdown-name">{user?.username}</p>
                <p className="user-dropdown-email">{user?.email}</p>
                <div style={{ marginTop: 'var(--space-2)', display: 'flex', gap: '4px' }}>
                  <Badge variant="lemon">{user?.cefr_level || 'B1'}</Badge>
                  {user?.native_language && (
                    <Badge variant="muted">Native: {user.native_language}</Badge>
                  )}
                </div>
              </div>

              <button
                type="button"
                className="user-dropdown-btn"
                onClick={() => {
                  setUserMenuOpen(false);
                  navigate('/settings');
                }}
              >
                <Settings size={16} />
                <span>Settings & Profile</span>
              </button>

              <button
                type="button"
                className="user-dropdown-btn logout"
                onClick={handleLogout}
              >
                <LogOut size={16} />
                <span>Sign Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}

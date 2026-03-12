'use client';

import { useState, useEffect, useCallback } from 'react';

/**
 * ThemeToggle — Light/Dark mode toggle button.
 *
 * Toggles data-theme="light" / data-theme="dark" on the <html> element.
 * Persists user preference to localStorage. Defaults to dark (runbook style).
 *
 * Accessibility:
 * - Keyboard-navigable button element
 * - aria-label announces current action ("Switch to light mode" / "Switch to dark mode")
 * - Focus-visible ring for keyboard users
 * - No color-only information — icon changes shape (sun ↔ moon)
 */
export default function ThemeToggle() {
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [mounted, setMounted] = useState(false);

  // Read persisted preference on mount
  useEffect(() => {
    setMounted(true);
    const stored = localStorage.getItem('ncdit-theme');
    if (stored === 'light' || stored === 'dark') {
      setTheme(stored);
      document.documentElement.setAttribute('data-theme', stored);
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('ncdit-theme', next);
      return next;
    });
  }, []);

  // Prevent hydration mismatch — render placeholder until mounted
  if (!mounted) {
    return (
      <button
        type="button"
        className="theme-toggle"
        aria-label="Toggle theme"
        style={{ visibility: 'hidden' }}
      >
        <span aria-hidden="true">🌙</span>
      </button>
    );
  }

  const isDark = theme === 'dark';

  return (
    <>
      <button
        type="button"
        className="theme-toggle"
        onClick={toggleTheme}
        aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
        title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      >
        <span className="theme-toggle__icon" aria-hidden="true">
          {isDark ? (
            /* Sun icon for "switch to light" */
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="5" />
              <line x1="12" y1="1" x2="12" y2="3" />
              <line x1="12" y1="21" x2="12" y2="23" />
              <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
              <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
              <line x1="1" y1="12" x2="3" y2="12" />
              <line x1="21" y1="12" x2="23" y2="12" />
              <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
              <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
            </svg>
          ) : (
            /* Moon icon for "switch to dark" */
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
            </svg>
          )}
        </span>
      </button>

      <style jsx>{`
        .theme-toggle {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 2.25rem;
          height: 2.25rem;
          padding: 0;
          border: 1px solid var(--border);
          border-radius: var(--radius-md);
          background: var(--surface);
          color: var(--text-secondary);
          cursor: pointer;
          transition: all var(--transition-fast);
        }

        .theme-toggle:hover {
          background: var(--surface-hover);
          color: var(--accent-amber);
          border-color: var(--border-hover);
        }

        .theme-toggle:focus-visible {
          outline: 3px solid var(--accent-sky);
          outline-offset: 2px;
        }

        .theme-toggle__icon {
          display: flex;
          align-items: center;
          justify-content: center;
          transition: transform var(--transition-normal);
        }

        .theme-toggle:hover .theme-toggle__icon {
          transform: rotate(15deg);
        }
      `}</style>
    </>
  );
}

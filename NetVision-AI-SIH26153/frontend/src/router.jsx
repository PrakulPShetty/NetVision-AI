/**
 * NetVision AI — minimal hash router
 *
 * The application is a Vite SPA served as static files, so routing is kept
 * dependency-free and hash based. That guarantees deep links work on any
 * static host without server rewrites.
 *
 * Routes
 *   /          Home (landing page, includes the #about section)
 *   /analyze   Traffic profile input + analysis
 *   /forecast  Future-state forecast
 *   /explain   Explainability (SHAP)
 *   /attack    MITRE ATT&CK correlation
 *
 * Swapping this for react-router later only requires replacing useRoute()
 * and navigate() — pages receive plain data and callbacks, never router
 * internals.
 */

import { useEffect, useState } from 'react';

export const ROUTES = {
  home: '/',
  analyze: '/analyze',
  forecast: '/forecast',
  explain: '/explain',
  attack: '/attack',
};

/** Navigation model shared by the navbar, footer and in-page calls to action. */
export const NAV_ITEMS = [
  { id: 'home', label: 'HOME', to: ROUTES.home },
  { id: 'about', label: 'ABOUT', to: ROUTES.home, scrollTo: 'about' },
  { id: 'analyze', label: 'ANALYZE', to: ROUTES.analyze },
  { id: 'forecast', label: 'FORECAST', to: ROUTES.forecast },
  { id: 'explain', label: 'EXPLAIN', to: ROUTES.explain },
  { id: 'attack', label: 'ATT&CK', to: ROUTES.attack },
];

const listeners = new Set();
let pendingScrollTarget = null;

function readPath() {
  if (typeof window === 'undefined') return ROUTES.home;
  const raw = window.location.hash.replace(/^#/, '');
  if (!raw || raw === '/') return ROUTES.home;
  const path = raw.startsWith('/') ? raw : `/${raw}`;
  return path.length > 1 ? path.replace(/\/+$/, '') : '/';
}

function flush() {
  listeners.forEach((listener) => listener());
}

/**
 * Navigate to a route.
 * @param {string} path   target route, e.g. '/forecast'
 * @param {object} [opts]
 * @param {string} [opts.scrollTo] element id to scroll to after the route renders
 */
export function navigate(path, { scrollTo = null } = {}) {
  pendingScrollTarget = scrollTo;
  if (readPath() === path) {
    flush();
    return;
  }
  window.location.hash = path;
}

/** Current route path, kept in sync with the URL hash. */
export function useRoute() {
  const [path, setPath] = useState(readPath);

  useEffect(() => {
    const handle = () => {
      setPath(readPath());
      const target = pendingScrollTarget;
      pendingScrollTarget = null;
      window.requestAnimationFrame(() => {
        if (target) {
          document.getElementById(target)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } else {
          window.scrollTo({ top: 0, left: 0, behavior: 'auto' });
        }
      });
    };

    listeners.add(handle);
    window.addEventListener('hashchange', handle);
    return () => {
      listeners.delete(handle);
      window.removeEventListener('hashchange', handle);
    };
  }, []);

  return path;
}

/** Anchor that behaves like a router link (middle-click / open-in-new-tab safe). */
export function RouteLink({ to, scrollTo, className, children, onBeforeNavigate, ...rest }) {
  return (
    <a
      href={`#${to}`}
      className={className}
      onClick={(event) => {
        event.preventDefault();
        onBeforeNavigate?.();
        navigate(to, { scrollTo });
      }}
      {...rest}
    >
      {children}
    </a>
  );
}

import { useEffect, useRef, useState } from 'react';
import { Menu, X } from 'lucide-react';
import Brand from '../common/Brand';
import { NAV_ITEMS } from '../../router';

/**
 * Application navbar.
 *
 * Layout contract: the brand lockup is anchored to the LEFT edge of the page
 * container and every navigation item plus the engine status are pushed to the
 * RIGHT edge — done structurally with flexbox `margin-left: auto` on the nav
 * group, not with arbitrary margins. The logo renders at 34px (up from 26px)
 * on its light plate so the wordmark stays sharp and clearly readable.
 *
 * Below 1000px the link row collapses into a disclosure menu; the brand and
 * the status pill remain in the bar.
 */

const HEALTH_LABELS = {
  checking: 'Checking engine',
  online: 'Forecast engine online',
  offline: 'Forecast engine unreachable',
};

export default function SiteNav({ activeId, onSelect, health = 'checking' }) {
  const [open, setOpen] = useState(false);
  const [elevated, setElevated] = useState(false);
  const menuButton = useRef(null);

  useEffect(() => {
    let frame = 0;
    const onScroll = () => {
      if (frame) return;
      frame = window.requestAnimationFrame(() => {
        setElevated(window.scrollY > 8);
        frame = 0;
      });
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      if (frame) window.cancelAnimationFrame(frame);
    };
  }, []);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  const select = (item) => {
    setOpen(false);
    onSelect(item);
  };

  return (
    <header className={`site-header${elevated ? ' elevated' : ''}`}>
      <div className="nav-inner">
        <Brand height={34} framed onClick={() => select(NAV_ITEMS[0])} />

        <nav className="desktop-nav" aria-label="Primary navigation">
          {NAV_ITEMS.map((item) => {
            const active = activeId === item.id;
            return (
              <button
                key={item.id}
                type="button"
                className={`nav-link${active ? ' active' : ''}`}
                aria-current={active ? 'page' : undefined}
                onClick={() => select(item)}
              >
                {item.label}
              </button>
            );
          })}
        </nav>

        <div className="nav-tail">
          <span
            className={`nav-status ${health}`}
            title={
              health === 'online'
                ? 'FastAPI backend responded to the health check.'
                : health === 'offline'
                ? 'No response from the FastAPI backend — start it to run analyses.'
                : 'Contacting the forecast service…'
            }
          >
            <span className="nav-status-dot" aria-hidden="true" />
            <span className="nav-status-text">{HEALTH_LABELS[health]}</span>
          </span>

          <button
            type="button"
            className="menu-button"
            ref={menuButton}
            aria-expanded={open}
            aria-label={open ? 'Close navigation' : 'Open navigation'}
            onClick={() => setOpen((value) => !value)}
          >
            {open ? <X size={20} /> : <Menu size={20} />}
          </button>
        </div>
      </div>

      <nav className={`mobile-nav${open ? ' open' : ''}`} aria-label="Primary navigation" aria-hidden={!open}>
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            type="button"
            className={`nav-link${activeId === item.id ? ' active' : ''}`}
            tabIndex={open ? 0 : -1}
            onClick={() => select(item)}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </header>
  );
}

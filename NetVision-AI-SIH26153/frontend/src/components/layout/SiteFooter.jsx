import Brand from '../common/Brand';
import { NAV_ITEMS } from '../../router';

/**
 * Product footer.
 *
 * Kept intentionally short: a visible light-treatment logo (previously an
 * unreadable dark mark on a dark surface), one line of product description,
 * the page navigation, and the project reference.
 */
export default function SiteFooter({ onSelect, engineState = 'checking' }) {
  return (
    <footer className="site-footer">
      <div className="footer-grid">
        <div className="footer-brand">
          <Brand height={34} variant="lockup" onClick={() => onSelect(NAV_ITEMS[0])} />
          <p className="footer-desc">
            Forecasts how a network&apos;s security state is likely to evolve from observed traffic behaviour —
            combining an XGBoost + Random Forest ensemble, a Markov world model, SHAP explainability and
            MITRE ATT&amp;CK correlation.
          </p>
        </div>

        <nav className="footer-col" aria-label="Footer navigation">
          <p className="footer-heading">Navigation</p>
          {NAV_ITEMS.map((item) => (
            <button key={item.id} type="button" className="footer-link" onClick={() => onSelect(item)}>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="footer-col">
          <p className="footer-heading">Project</p>
          <p className="footer-meta">Smart India Hackathon 2026 · Problem statement SIH26153</p>
          <p className="footer-meta">AI-based network attack forecasting from network traffic data</p>
          <p className="footer-meta">
            Dataset: CIC-IDS2018 · Engine:{' '}
            <span className={`footer-engine ${engineState}`}>
              {engineState === 'online' ? 'online' : engineState === 'offline' ? 'unreachable' : 'checking'}
            </span>
          </p>
        </div>
      </div>

      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} NetVision AI — predictive network security intelligence.</span>
        <span>Detections and forecasts are model estimates, not proof of malicious intent.</span>
      </div>
    </footer>
  );
}

import { useEffect, useRef } from 'react';
import { ArrowDownRight, ArrowRight } from 'lucide-react';
import Panel from '../components/common/Panel';
import Chip from '../components/common/Chip';
import HeroDiagram from '../components/home/HeroDiagram';
import ForecastWorkflow from '../components/home/ForecastWorkflow';
import PipelineTrack from '../components/home/PipelineTrack';

/**
 * Landing page.
 *
 * Keeps the existing narrative and dark identity, but every section now states
 * something functional: what the platform answers, how the pipeline works, what
 * each page delivers, and what the system is built on. No statistics are shown
 * here — the landing page contains no model output at all.
 */

const ANSWERS = [
  {
    question: 'What is happening in the network?',
    answer: 'A 5-minute observation window describes flows, packet and byte volumes, rates, timings and TCP flag activity.',
    stage: 'Observe',
    route: '/analyze',
    routeLabel: 'Analyze traffic',
  },
  {
    question: 'What is the current network state?',
    answer: 'The trained ensemble scores that window and the probability is compared with the calibrated decision threshold.',
    stage: 'Assess',
    route: '/analyze',
    routeLabel: 'See the assessment',
  },
  {
    question: 'What is likely to happen next?',
    answer: 'A Markov world model propagates the current state across future horizons instead of returning a present-tense verdict.',
    stage: 'Forecast',
    route: '/forecast',
    routeLabel: 'Open forecast',
  },
  {
    question: 'Why does the model believe that?',
    answer: 'SHAP attribution ranks the traffic signals that raised or lowered the probability, with magnitude and direction.',
    stage: 'Explain',
    route: '/explain',
    routeLabel: 'Review the explanation',
  },
  {
    question: 'Which ATT&CK behaviour may be relevant?',
    answer: 'Behavioural signal groups are matched against MITRE ATT&CK rules, and a technique is reported only with its evidence.',
    stage: 'Correlate',
    route: '/attack',
    routeLabel: 'View correlation',
  },
];

const CAPABILITIES = [
  {
    tone: 'default',
    eyebrow: 'Analyze',
    title: 'Traffic profile in, assessment out',
    text: 'Enter the observation window manually or load a representative scenario. The backend expands fifteen practical inputs into the frozen 138-feature representation and scores them.',
    route: '/analyze',
    routeLabel: 'Open Analyze',
  },
  {
    tone: 'accent',
    eyebrow: 'Forecast',
    title: 'Multi-horizon state projection',
    text: 'See where the state is expected to go, not just where it is: attack probability per horizon, the Markov steps behind each one, and where the projected state changes.',
    route: '/forecast',
    routeLabel: 'Open Forecast',
  },
  {
    tone: 'normal',
    eyebrow: 'Explain',
    title: 'Attribution you can audit',
    text: 'Ranked SHAP contributions with direction and importance, each resolved to the traffic behaviour behind it, plus a base-and-reconstruction check of the explanation itself.',
    route: '/explain',
    routeLabel: 'Open Explain',
  },
  {
    tone: 'elevated',
    eyebrow: 'ATT&CK',
    title: 'Evidence-based correlation',
    text: 'Techniques appear only when the configured behavioural rules are satisfied, always accompanied by the supporting signal groups and an explicit limitation statement.',
    route: '/attack',
    routeLabel: 'Open ATT&CK',
  },
];

export default function HomePage({ onGo, onSectionChange, workflowIndex, onWorkflowIndexChange }) {
  const aboutRef = useRef(null);

  // Report which landing section is on screen so the navbar can highlight ABOUT.
  useEffect(() => {
    if (!onSectionChange) return undefined;
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((entry) => entry.isIntersecting)
          .sort((a, b) => b.intersectionRatio - a.intersectionRatio)[0];
        if (visible) onSectionChange(visible.target.id);
      },
      { rootMargin: '-45% 0px -45% 0px', threshold: [0.05, 0.3] }
    );
    if (aboutRef.current) observer.observe(aboutRef.current);
    return () => observer.disconnect();
  }, [onSectionChange]);

  return (
    <div className="page home">
      <section id="home" className="hero">
        <div className="hero-copy">
          <p className="eyebrow">Predictive network security intelligence</p>
          <h1 className="hero-title">NETVISION AI</h1>
          <p className="hero-subtitle">AI-based network attack forecasting</p>
          <p className="hero-description">
            Forecast future network security states from traffic behaviour. NetVision AI observes a traffic window, assesses the
            current state, projects how that state may evolve, explains why, and correlates the evidence with MITRE ATT&amp;CK.
          </p>
          <div className="hero-actions">
            <button type="button" className="button primary" onClick={() => onGo('/analyze')}>
              Analyze network <ArrowDownRight size={17} />
            </button>
            <button type="button" className="text-button" onClick={() => onGo('/', { scrollTo: 'about' })}>
              How it works <ArrowDownRight size={16} />
            </button>
          </div>
          <ul className="hero-signals">
            <li>Traffic observation</li>
            <li>Current state</li>
            <li>Future-state forecast</li>
            <li>Explainability</li>
            <li>ATT&amp;CK correlation</li>
          </ul>
        </div>
        <HeroDiagram />
      </section>

      <section className="home-section" id="answers">
        <header className="section-intro">
          <p className="eyebrow">Why forecasting</p>
          <h2>Detection answers the present. Forecasting answers what comes next.</h2>
          <p>
            Conventional intrusion detection decides whether an attack is happening right now. NetVision AI keeps that present-tense
            assessment, then extends it forward in time — and shows the evidence for both.
          </p>
        </header>
        <ol className="answer-grid">
          {ANSWERS.map((item, index) => (
            <li key={item.question}>
              <button type="button" className="answer-card" onClick={() => onGo(item.route)}>
                <span className="answer-head">
                  <span className="answer-index">{String(index + 1).padStart(2, '0')}</span>
                  <Chip tone="muted">{item.stage}</Chip>
                </span>
                <span className="answer-question">{item.question}</span>
                <span className="answer-text">{item.answer}</span>
                <span className="answer-link">
                  {item.routeLabel} <ArrowRight size={13} />
                </span>
              </button>
            </li>
          ))}
        </ol>
      </section>

      <section className="home-section" id="workflow">
        <header className="section-intro split-intro">
          <div>
            <p className="eyebrow">Forecasting workflow</p>
            <h2>Five stages, one continuous pipeline</h2>
          </div>
          <p>
            Hover or select a stage to see what the system does at that point and which page exposes the result. Every stage maps to a
            real component of the backend pipeline.
          </p>
        </header>
        <ForecastWorkflow
          onGo={onGo}
          activeIndex={workflowIndex}
          onActiveIndexChange={onWorkflowIndexChange}
        />
      </section>

      <section className="home-section" id="capabilities">
        <header className="section-intro">
          <p className="eyebrow">Product surface</p>
          <h2>Four working surfaces, one model pipeline</h2>
          <p>Each page has a single responsibility, so nothing important is buried inside a single dashboard.</p>
        </header>
        <div className="capability-grid">
          {CAPABILITIES.map((item) => (
            <Panel
              key={item.eyebrow}
              eyebrow={item.eyebrow}
              title={item.title}
              tone={item.tone}
              interactive
              footer={
                <button type="button" className="text-button" onClick={() => onGo(item.route)}>
                  {item.routeLabel} <ArrowRight size={13} />
                </button>
              }
            >
              <p className="capability-text">{item.text}</p>
            </Panel>
          ))}
        </div>
      </section>

      <section className="home-section about-section" id="about" ref={aboutRef}>
        <div className="about-lead">
          <p className="eyebrow">About NetVision AI</p>
          <h2>
            Security should not
            <br />
            stop at detection.
          </h2>
          <p className="about-intro-p">Network security is often focused on understanding what is happening in the traffic being observed.</p>
          <p className="about-question">NetVision AI explores a different question:</p>
          <p className="about-question-lead">How might the network security state evolve from here?</p>
          <p className="about-body">
            The platform is built for that question specifically. It keeps the present-tense assessment a defender needs, and adds the
            temporal projection, the attribution and the behavioural context that make a forecast usable rather than merely
            interesting.
          </p>
        </div>
        <div className="about-pipeline">
          <p className="eyebrow">What the frontend is built on</p>
          <h3 className="about-pipeline-title">A research pipeline, surfaced end to end</h3>
          <p className="about-body">
            This interface is the last mile of a real machine-learning system. Every visualisation is fed by the same backend that
            performs feature expansion, ensemble inference, Markov state projection, SHAP attribution and ATT&amp;CK correlation.
          </p>
          <PipelineTrack />
        </div>
      </section>

      <section className="home-cta">
        <div>
          <p className="eyebrow">Get started</p>
          <h2>Run a forecast on a traffic profile</h2>
          <p>
            Start from a representative scenario or enter your own 5-minute observation window. Results are produced by the backend
            pipeline — the interface never invents them.
          </p>
        </div>
        <button type="button" className="button primary" onClick={() => onGo('/analyze')}>
          Analyze network <ArrowDownRight size={17} />
        </button>
      </section>
    </div>
  );
}

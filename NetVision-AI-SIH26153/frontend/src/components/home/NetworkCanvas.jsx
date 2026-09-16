import { useEffect, useRef, useState } from 'react';

/**
 * Hero visual: an interactive network-forecast field.
 *
 * A canvas renders the project's core idea — traffic moving across a node
 * graph, the assessed current state and the projected future state. It is a
 * structural illustration, not data: no probabilities, counts or model output
 * appear anywhere in it.
 *
 * Behaviour:
 *  - requestAnimationFrame loop; pauses when scrolled off-screen or tab hidden
 *  - nodes drift slowly; links and nodes respond to the pointer (parallax +
 *    highlight), so the field feels three-dimensional without WebGL
 *  - a copper pulse travels the "current state -> forecast horizon" bridge
 *  - reduced motion: the same scene renders once, frozen, with no listeners
 *  - plain 2D canvas, so it degrades gracefully where WebGL is unavailable
 */

const NODE_COUNT = 26;
const LINK_DIST = 132;
const PACKET_COUNT = 7;
const PULSE_PERIOD = 3400; // ms between forecast pulses
const PULSE_TRAVEL = 1150; // ms for one pulse to cross the bridge

const COLORS = {
  node: 'rgba(154, 170, 190, 0.5)',
  nodeHot: 'rgba(222, 228, 234, 0.9)',
  link: 'rgba(122, 144, 176, 0.15)',
  linkHot: 'rgba(206, 216, 227, 0.4)',
  packet: 'rgba(221, 142, 104, 0.85)',
  bridge: 'rgba(187, 118, 88, 0.55)',
  now: 'rgba(141, 171, 148, 0.95)',
  next: 'rgba(214, 137, 99, 0.95)',
};

export default function NetworkCanvas() {
  const wrapRef = useRef(null);
  const canvasRef = useRef(null);
  const [supported, setSupported] = useState(true);

  useEffect(() => {
    const wrap = wrapRef.current;
    const canvas = canvasRef.current;
    if (!wrap || !canvas) return undefined;

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      setSupported(false);
      return undefined;
    }

    const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false;

    let width = 1;
    let height = 1;
    let raf = 0;
    let last = performance.now();
    let pulseClock = 0;
    let pulseT = 1; // inactive until the first period elapses
    let inView = true;
    let disposed = false;

    const pointer = { x: -9999, y: -9999, inside: false };

    const nodes = Array.from({ length: NODE_COUNT }, () => ({
      x: Math.random(),
      y: Math.random(),
      vx: (Math.random() - 0.5) * 0.00002, // fraction of the field per ms
      vy: (Math.random() - 0.5) * 0.000016,
      r: 1.3 + Math.random() * 1.7,
    }));

    const randomLink = () => {
      let a = (Math.random() * nodes.length) | 0;
      let b = (Math.random() * nodes.length) | 0;
      if (a === b) b = (b + 1) % nodes.length;
      return [a, b];
    };

    const packets = Array.from({ length: PACKET_COUNT }, () => {
      const [a, b] = randomLink();
      return { a, b, t: Math.random(), speed: 0.00014 + Math.random() * 0.00014 };
    });

    // Anchors of the state bridge, as fractions of the field.
    const beacons = { now: { x: 0.17, y: 0.66 }, next: { x: 0.83, y: 0.32 } };

    const resize = () => {
      const rect = wrap.getBoundingClientRect();
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      width = Math.max(1, rect.width);
      height = Math.max(1, rect.height);
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    const drawFrame = (dt) => {
      for (const node of nodes) {
        node.x += node.vx * dt;
        node.y += node.vy * dt;
        if (node.x < -0.02) node.x = 1.02;
        else if (node.x > 1.02) node.x = -0.02;
        if (node.y < -0.02) node.y = 1.02;
        else if (node.y > 1.02) node.y = -0.02;
      }

      // Pointer parallax: deeper layers shift less than near ones.
      const px = pointer.inside ? pointer.x / width - 0.5 : 0;
      const py = pointer.inside ? pointer.y / height - 0.5 : 0;
      const shiftX = px * 14;
      const shiftY = py * 10;
      const X = (f) => f * width + shiftX * (0.4 + f * 0.6);
      const Y = (f) => f * height + shiftY * (0.4 + f * 0.6);

      ctx.clearRect(0, 0, width, height);

      // proximity links
      for (let i = 0; i < nodes.length; i += 1) {
        for (let j = i + 1; j < nodes.length; j += 1) {
          const ax = X(nodes[i].x);
          const ay = Y(nodes[i].y);
          const bx = X(nodes[j].x);
          const by = Y(nodes[j].y);
          const d = Math.hypot(ax - bx, ay - by);
          if (d > LINK_DIST) continue;
          const near = 1 - d / LINK_DIST;
          const mx = (ax + bx) / 2;
          const my = (ay + by) / 2;
          const boost = pointer.inside ? Math.max(0, 1 - Math.hypot(mx - pointer.x, my - pointer.y) / 130) : 0;
          ctx.strokeStyle = boost > 0.25 ? COLORS.linkHot : COLORS.link;
          ctx.globalAlpha = 0.35 + near * 0.65;
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.moveTo(ax, ay);
          ctx.lineTo(bx, by);
          ctx.stroke();
        }
      }
      ctx.globalAlpha = 1;

      // packets — traffic moving node to node
      for (const packet of packets) {
        packet.t += packet.speed * dt;
        if (packet.t > 1) {
          packet.t = 0;
          [packet.a, packet.b] = randomLink();
        }
        for (let k = 0; k < 4; k += 1) {
          const tt = packet.t - k * 0.035;
          if (tt < 0 || tt > 1) continue;
          const x = X(nodes[packet.a].x + (nodes[packet.b].x - nodes[packet.a].x) * tt);
          const y = Y(nodes[packet.a].y + (nodes[packet.b].y - nodes[packet.a].y) * tt);
          ctx.fillStyle = COLORS.packet;
          ctx.globalAlpha = (1 - k / 4) * 0.8;
          ctx.beginPath();
          ctx.arc(x, y, k === 0 ? 1.8 : 1.2, 0, Math.PI * 2);
          ctx.fill();
        }
      }
      ctx.globalAlpha = 1;

      // nodes — swell slightly near the pointer
      for (const node of nodes) {
        const x = X(node.x);
        const y = Y(node.y);
        const hot = pointer.inside ? Math.max(0, 1 - Math.hypot(x - pointer.x, y - pointer.y) / 90) : 0;
        ctx.fillStyle = hot > 0.3 ? COLORS.nodeHot : COLORS.node;
        ctx.beginPath();
        ctx.arc(x, y, node.r + hot * 1.6, 0, Math.PI * 2);
        ctx.fill();
      }

      // state beacons and the forecast bridge between them
      const nowX = X(beacons.now.x);
      const nowY = Y(beacons.now.y);
      const nextX = X(beacons.next.x);
      const nextY = Y(beacons.next.y);
      const ctrlY = Math.min(nowY, nextY) - 46;

      ctx.strokeStyle = COLORS.bridge;
      ctx.setLineDash([3, 6]);
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(nowX, nowY);
      ctx.quadraticCurveTo((nowX + nextX) / 2, ctrlY, nextX, nextY);
      ctx.stroke();
      ctx.setLineDash([]);

      const ring = (x, y, color) => {
        ctx.strokeStyle = color;
        ctx.lineWidth = 1.4;
        ctx.beginPath();
        ctx.arc(x, y, 6.5, 0, Math.PI * 2);
        ctx.stroke();
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(x, y, 2.4, 0, Math.PI * 2);
        ctx.fill();
      };
      ring(nowX, nowY, COLORS.now);
      ring(nextX, nextY, COLORS.next);

      // travelling pulse — current state to future state
      pulseClock += dt;
      if (pulseClock >= PULSE_PERIOD && pulseT >= 1) {
        pulseClock = 0;
        pulseT = 0;
      }
      if (pulseT < 1) {
        pulseT = Math.min(1, pulseT + dt / PULSE_TRAVEL);
        const t = pulseT;
        const qx = (1 - t) * (1 - t) * nowX + 2 * (1 - t) * t * ((nowX + nextX) / 2) + t * t * nextX;
        const qy = (1 - t) * (1 - t) * nowY + 2 * (1 - t) * t * ctrlY + t * t * nextY;
        const glow = ctx.createRadialGradient(qx, qy, 0, qx, qy, 12);
        glow.addColorStop(0, 'rgba(224, 148, 108, 0.85)');
        glow.addColorStop(1, 'rgba(224, 148, 108, 0)');
        ctx.fillStyle = glow;
        ctx.beginPath();
        ctx.arc(qx, qy, 12, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = 'rgba(240, 205, 185, 0.95)';
        ctx.beginPath();
        ctx.arc(qx, qy, 2, 0, Math.PI * 2);
        ctx.fill();
      }
    };

    const loop = (now) => {
      if (disposed) return;
      const dt = Math.min(48, now - last);
      last = now;
      if (inView && !document.hidden) drawFrame(dt);
      raf = window.requestAnimationFrame(loop);
    };

    resize();

    if (reduceMotion) {
      // Same scene, frozen: the field still reads, nothing animates.
      pulseT = 0.5;
      drawFrame(0);
      const staticObserver = new ResizeObserver(() => {
        resize();
        drawFrame(0);
      });
      staticObserver.observe(wrap);
      return () => staticObserver.disconnect();
    }

    const onPointerMove = (event) => {
      const rect = wrap.getBoundingClientRect();
      pointer.x = event.clientX - rect.left;
      pointer.y = event.clientY - rect.top;
      pointer.inside = true;
    };
    const onPointerLeave = () => {
      pointer.inside = false;
    };
    const onVisibility = () => {
      last = performance.now();
    };

    const resizeObserver = new ResizeObserver(resize);
    const viewObserver = new IntersectionObserver(
      (entries) => {
        inView = entries.some((entry) => entry.isIntersecting);
      },
      { threshold: 0.02 }
    );

    resizeObserver.observe(wrap);
    viewObserver.observe(wrap);
    wrap.addEventListener('pointermove', onPointerMove);
    wrap.addEventListener('pointerleave', onPointerLeave);
    document.addEventListener('visibilitychange', onVisibility);
    raf = window.requestAnimationFrame(loop);

    return () => {
      disposed = true;
      window.cancelAnimationFrame(raf);
      resizeObserver.disconnect();
      viewObserver.disconnect();
      wrap.removeEventListener('pointermove', onPointerMove);
      wrap.removeEventListener('pointerleave', onPointerLeave);
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);

  const note = (
    <p className="hero-visual-note">
      Structural illustration — traffic across the network, the assessed state and the projected future state. No model output is
      shown on this page.
    </p>
  );

  if (!supported) {
    return (
      <div className="hero-visual">
        <div className="hero-visual-fallback">
          Traffic observation → current state → future-state forecast → explanation → ATT&amp;CK context
        </div>
        {note}
      </div>
    );
  }

  return (
    <div className="hero-visual">
      <div className="hero-canvas-wrap" ref={wrapRef}>
        <canvas ref={canvasRef} className="hero-canvas" aria-hidden="true" />
        <span className="hero-beacon-label now">Current state</span>
        <span className="hero-beacon-label next">Forecast horizon</span>
      </div>
      {note}
    </div>
  );
}

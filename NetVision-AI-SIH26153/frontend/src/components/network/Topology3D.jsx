import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { MOCK_TOPOLOGY_NODES, MOCK_TOPOLOGY_EDGES } from '../../mocks/phase1/mockData';
import { Server, Database, Globe, Shield, Monitor, Activity, Radio, Info } from 'lucide-react';

export default function Topology3D() {
  const mountRef = useRef(null);
  const [selectedNode, setSelectedNode] = useState(MOCK_TOPOLOGY_NODES[1]); // Default Gateway
  const [hoveredNode, setHoveredNode] = useState(null);

  useEffect(() => {
    const container = mountRef.current;
    if (!container) return;

    // Scene, Camera, Renderer setup
    const scene = new THREE.Scene();
    scene.background = new THREE.Color('#0b0d10');

    const width = container.clientWidth;
    const height = container.clientHeight || 450;
    const camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000);
    camera.position.set(0, 4, 12);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    container.appendChild(renderer.domElement);

    // Lights
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
    scene.add(ambientLight);

    const pointLight = new THREE.PointLight(0x14b8a6, 2, 50);
    pointLight.position.set(0, 10, 10);
    scene.add(pointLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(-5, 10, 5);
    scene.add(directionalLight);

    // Node Meshes Mapping
    const nodeMeshes = [];
    const nodeMap = {};

    MOCK_TOPOLOGY_NODES.forEach((node) => {
      let color = 0x0d9488; // Default Teal
      if (node.status === 'elevated') color = 0xf59e0b; // Amber
      if (node.status === 'critical') color = 0xe11d48; // Crimson
      if (node.status === 'external') color = 0x06b6d4; // Cyan

      let geometry;
      if (node.type === 'cloud') {
        geometry = new THREE.IcosahedronGeometry(0.7, 1);
      } else if (node.type === 'firewall') {
        geometry = new THREE.OctahedronGeometry(0.75, 0);
      } else if (node.type === 'database') {
        geometry = new THREE.CylinderGeometry(0.5, 0.5, 0.9, 16);
      } else {
        geometry = new THREE.SphereGeometry(0.6, 24, 24);
      }

      const material = new THREE.MeshStandardMaterial({
        color: color,
        metalness: 0.3,
        roughness: 0.2,
        emissive: color,
        emissiveIntensity: 0.2,
        wireframe: node.type === 'cloud'
      });

      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.set(...node.pos);
      mesh.userData = node;

      // Glow halo ring
      const ringGeo = new THREE.RingGeometry(0.75, 0.85, 32);
      const ringMat = new THREE.MeshBasicMaterial({
        color: color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.4
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.rotation.x = Math.PI / 2;
      mesh.add(ring);

      scene.add(mesh);
      nodeMeshes.push(mesh);
      nodeMap[node.id] = mesh;
    });

    // Edges (Connection Lines)
    const edgeLines = [];
    MOCK_TOPOLOGY_EDGES.forEach((edge) => {
      const fromMesh = nodeMap[edge.from];
      const toMesh = nodeMap[edge.to];
      if (fromMesh && toMesh) {
        const points = [fromMesh.position, toMesh.position];
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);

        const isElevated = fromMesh.userData.status === 'elevated' || toMesh.userData.status === 'elevated';
        const lineMat = new THREE.LineBasicMaterial({
          color: isElevated ? 0xf59e0b : 0x334155,
          linewidth: 2,
          transparent: true,
          opacity: isElevated ? 0.8 : 0.4
        });

        const line = new THREE.Line(lineGeo, lineMat);
        scene.add(line);
        edgeLines.push(line);
      }
    });

    // Raycasting & Interaction
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();

    let isMouseDown = false;
    let previousMousePosition = { x: 0, y: 0 };

    const handleMouseDown = (e) => {
      isMouseDown = true;
      previousMousePosition = { x: e.clientX, y: e.clientY };
    };

    const handleMouseMove = (e) => {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;

      // Camera Orbit Controls
      if (isMouseDown) {
        const deltaX = e.clientX - previousMousePosition.x;
        const deltaY = e.clientY - previousMousePosition.y;

        scene.rotation.y += deltaX * 0.005;
        scene.rotation.x += deltaY * 0.005;

        previousMousePosition = { x: e.clientX, y: e.clientY };
      }

      // Raycast Hover Check
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodeMeshes);
      if (intersects.length > 0) {
        container.style.cursor = 'pointer';
        setHoveredNode(intersects[0].object.userData);
      } else {
        container.style.cursor = 'grab';
        setHoveredNode(null);
      }
    };

    const handleMouseUp = () => {
      isMouseDown = false;
    };

    const handleClick = () => {
      raycaster.setFromCamera(mouse, camera);
      const intersects = raycaster.intersectObjects(nodeMeshes);
      if (intersects.length > 0) {
        setSelectedNode(intersects[0].object.userData);
      }
    };

    const domElement = renderer.domElement;
    domElement.addEventListener('mousedown', handleMouseDown);
    domElement.addEventListener('mousemove', handleMouseMove);
    domElement.addEventListener('mouseup', handleMouseUp);
    domElement.addEventListener('click', handleClick);

    // Resize Handler
    const handleResize = () => {
      if (!container) return;
      const w = container.clientWidth;
      const h = container.clientHeight || 450;
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
      renderer.setSize(w, h);
    };
    window.addEventListener('resize', handleResize);

    // Animation Loop
    let animationFrameId;
    const animate = () => {
      animationFrameId = requestAnimationFrame(animate);

      // Rotate nodes subtly
      nodeMeshes.forEach((mesh) => {
        mesh.rotation.y += 0.008;
      });

      renderer.render(scene, camera);
    };
    animate();

    // Cleanup
    return () => {
      window.removeEventListener('resize', handleResize);
      domElement.removeEventListener('mousedown', handleMouseDown);
      domElement.removeEventListener('mousemove', handleMouseMove);
      domElement.removeEventListener('mouseup', handleMouseUp);
      domElement.removeEventListener('click', handleClick);
      cancelAnimationFrame(animationFrameId);

      if (container.contains(renderer.domElement)) {
        container.removeChild(renderer.domElement);
      }
      renderer.dispose();
    };
  }, []);

  const getNodeIcon = (type) => {
    switch (type) {
      case 'cloud': return Globe;
      case 'firewall': return Shield;
      case 'server': return Server;
      case 'database': return Database;
      case 'endpoint': return Monitor;
      default: return Activity;
    }
  };

  return (
    <div className="bg-surface-low border border-surface-border rounded-lg p-5">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-surface-border">
        <div>
          <div className="flex items-center gap-2">
            <Radio className="w-5 h-5 text-primary animate-pulse" />
            <h2 className="text-base font-semibold text-content-primary">Spatial Network Topology</h2>
          </div>
          <p className="text-xs text-content-muted mt-0.5">
            Interactive 3D visualization of infrastructure node relationships and connectivity state.
          </p>
        </div>

        <div className="flex items-center gap-3 font-mono text-xs">
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-surface-container border border-surface-border">
            <span className="w-2 h-2 rounded-full bg-primary"></span>
            <span className="text-content-secondary">Normal State</span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 py-1 rounded bg-elevated-container border border-elevated/40">
            <span className="w-2 h-2 rounded-full bg-elevated"></span>
            <span className="text-elevated font-medium">Elevated Traffic</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mt-5">
        {/* 3D Canvas Canvas Container */}
        <div className="lg:col-span-3 bg-background border border-surface-border rounded-lg relative h-[420px] overflow-hidden subtle-grid">
          <div ref={mountRef} className="w-full h-full cursor-grab active:cursor-grabbing" />
          
          {/* Controls Instruction Overlay */}
          <div className="absolute bottom-3 left-3 bg-surface-dim/90 backdrop-blur border border-surface-border px-3 py-1.5 rounded text-[11px] text-content-muted flex items-center gap-2 select-none">
            <Info className="w-3.5 h-3.5 text-primary" />
            <span>Click & Drag to Orbit • Click Node to Inspect</span>
          </div>

          {/* Hover Tooltip */}
          {hoveredNode && (
            <div className="absolute top-3 left-3 bg-surface-high border border-primary/40 px-3 py-1.5 rounded shadow-lg text-xs font-mono text-primary pointer-events-none">
              Hovering: {hoveredNode.label} ({hoveredNode.ip})
            </div>
          )}
        </div>

        {/* Selected Node Details Panel */}
        <div className="bg-surface-container border border-surface-border rounded-lg p-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <span className="text-xs font-mono text-content-muted uppercase tracking-wider">SELECTED NODE</span>
              <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded uppercase ${
                selectedNode.status === 'elevated' 
                  ? 'bg-elevated-container text-elevated border border-elevated/40' 
                  : 'bg-primary-container text-primary-light border border-primary/30'
              }`}>
                {selectedNode.status}
              </span>
            </div>

            <div className="mt-4 flex items-center gap-3">
              {React.createElement(getNodeIcon(selectedNode.type), { className: "w-8 h-8 text-primary" })}
              <div>
                <h3 className="text-sm font-semibold text-content-primary">{selectedNode.label}</h3>
                <span className="text-xs font-mono text-content-secondary">{selectedNode.ip}</span>
              </div>
            </div>

            <div className="mt-5 space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-surface-border/60">
                <span className="text-content-muted">Node Category:</span>
                <span className="font-mono text-content-primary capitalize">{selectedNode.type}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-surface-border/60">
                <span className="text-content-muted">Primary Role:</span>
                <span className="font-mono text-content-primary">
                  {selectedNode.type === 'firewall' ? 'Perimeter Inspection' : 
                   selectedNode.type === 'database' ? 'Relational Data Store' : 
                   selectedNode.type === 'server' ? 'Application Service' : 'End Host'}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-surface-border/60">
                <span className="text-content-muted">Monitored Telemetry:</span>
                <span className="font-mono text-primary">Active Flow Vector</span>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-3 border-t border-surface-border text-[11px] text-content-muted leading-relaxed">
            <span className="font-semibold text-content-secondary block mb-1">Architecture Context:</span>
            Phase 1 provides spatial topology visualization. Phase 2 will link live telemetry state directly to individual node color highlights.
          </div>
        </div>
      </div>
    </div>
  );
}

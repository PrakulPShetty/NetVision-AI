import React, { useState } from 'react';
import { 
  ShieldAlert, 
  Server, 
  Database, 
  Globe, 
  ShieldCheck, 
  Lock, 
  Laptop, 
  Activity,
  Terminal,
  FileSpreadsheet
} from 'lucide-react';

export default function TopologyGraph({ forecastData }) {
  const [selectedNode, setSelectedNode] = useState('APP-01');

  // Derive risk state from backend response
  const isAttack = forecastData?.ml?.predicted_current_state === 'ATTACK';
  const attackProb = forecastData?.ml?.ensemble_attack_probability ?? 0.0;
  const mitreTechs = forecastData?.mitre_attack?.techniques || [];

  const NODE_DETAILS = {
    'APP-01': {
      id: 'APP-01',
      name: 'APP-01-CLUSTER',
      ip: '10.140.2.14 // ZONE-PROD-APP',
      role: 'Production Application Gateway',
      status: isAttack ? 'HIGH RISK / ANOMALOUS' : 'NOMINAL STATE',
      statusColor: isAttack ? 'text-error bg-error-container/20 border-error/40' : 'text-primary bg-primary/10 border-primary/30',
      icon: Server,
      socketSat: isAttack ? `${(85 + attackProb * 14).toFixed(1)}%` : '12.4%',
      halfOpen: isAttack ? Math.floor(12000 + attackProb * 20000).toLocaleString() : '42',
      targetedPorts: [
        { port: 'PORT 443 (HTTPS/TLS)', rate: isAttack ? `${Math.floor(8000 + attackProb * 6000)} pps [ANOMALY]` : '420 pps [NOMINAL]', flag: isAttack ? 'text-error font-bold' : 'text-on-surface' },
        { port: 'PORT 8443 (Internal API)', rate: isAttack ? `${Math.floor(1200 + attackProb * 1500)} pps [ELEVATED]` : '85 pps [NOMINAL]', flag: isAttack ? 'text-amber-400 font-semibold' : 'text-on-surface' },
        { port: 'PORT 22 (SSH Admin)', rate: '4 pps [NOMINAL]', flag: 'text-on-surface-variant' },
      ],
      description: isAttack
        ? `Backend model detected attack probability of ${(attackProb * 100).toFixed(1)}%. Incoming connection rate exceeds TCP window threshold with asymmetric ACK flags.`
        : 'Application cluster functioning normally with zero socket buffer saturation.',
      recommendation: isAttack
        ? 'Activate SYN Cookie enforcement on Edge Gateway and restrict source CIDR ingress rate.'
        : 'Routine perimeter inspection active.'
    },
    'EXT-WAN': {
      id: 'EXT-WAN',
      name: 'EXTERNAL-WAN-INGRESS',
      ip: 'ASN 4134 // BGP-TRANSIT-01',
      role: 'External Transit Provider',
      status: isAttack ? 'ATTACK TRAFFIC ORIGIN' : 'EXTERNAL TRAFFIC',
      statusColor: isAttack ? 'text-error bg-error-container/20 border-error/40' : 'text-secondary bg-secondary/10 border-secondary/30',
      icon: Globe,
      socketSat: '100%',
      halfOpen: isAttack ? '142,890' : '1,200',
      targetedPorts: [
        { port: 'BGP INGRESS FLOWS', rate: isAttack ? '14,280 flows/s' : '450 flows/s', flag: isAttack ? 'text-error font-bold' : 'text-on-surface' }
      ],
      description: 'Public BGP ingress router interfaces receiving external traffic streams.',
      recommendation: isAttack ? 'Evaluate BGP Flowspec rate-limiting filters at upstream peer.' : 'No action required.'
    },
    'GW-01': {
      id: 'GW-01',
      name: 'EDGE-GW-01 (FIREWALL)',
      ip: '10.140.0.1 // BORDER-FW',
      role: 'Edge Statefull Firewall',
      status: isAttack ? 'TRAFFIC SURGE ELEVATED' : 'NOMINAL TRANSIT',
      statusColor: isAttack ? 'text-amber-400 bg-amber-500/20 border-amber-500/30' : 'text-primary bg-primary/10 border-primary/30',
      icon: ShieldCheck,
      socketSat: isAttack ? '68.1%' : '14.2%',
      halfOpen: isAttack ? '12,900' : '85',
      targetedPorts: [
        { port: 'INGRESS THROUGHPUT', rate: isAttack ? '4.24 Gbps' : '0.45 Gbps', flag: isAttack ? 'text-amber-400 font-bold' : 'text-on-surface' }
      ],
      description: 'Hardware stateful edge packet inspector processing multi-layer flow rules.',
      recommendation: 'Monitor memory buffer pool and CPU core allocation.'
    },
    'AUTH-01': {
      id: 'AUTH-01',
      name: 'AUTH-SSO-01 (KERBEROS)',
      ip: '10.140.1.20 // ID-ENCLAVE',
      role: 'Authentication & SSO Server',
      status: isAttack ? 'POTENTIAL LATERAL TARGET' : 'NOMINAL STATE',
      statusColor: isAttack ? 'text-amber-400 bg-amber-500/20 border-amber-500/30' : 'text-primary bg-primary/10 border-primary/30',
      icon: Lock,
      socketSat: '28.4%',
      halfOpen: '142',
      targetedPorts: [
        { port: 'PORT 88 (Kerberos TGT)', rate: '120 req/s [NOMINAL]', flag: 'text-on-surface' }
      ],
      description: 'Identity enclave server handling Kerberos ticket issuing and SSO auth.',
      recommendation: 'Enforce microsegmentation boundary rules from app cluster.'
    },
    'ENDPOINTS': {
      id: 'ENDPOINTS',
      name: 'WORKSTATIONS-CLUSTER',
      ip: '10.140.4.0/24 // CORP-LAN',
      role: 'Enterprise LAN Workstations',
      status: 'NOMINAL STATE',
      statusColor: 'text-primary bg-primary/10 border-primary/30',
      icon: Laptop,
      socketSat: '8.2%',
      halfOpen: '12',
      targetedPorts: [
        { port: 'CORP WORKSTATIONS', rate: '42 ACTIVE CLIENTS', flag: 'text-on-surface-variant' }
      ],
      description: 'Employee endpoints operating within isolated user VLAN segment.',
      recommendation: 'Endpoint agent EDR active and compliant.'
    },
    'DB-01': {
      id: 'DB-01',
      name: 'DB-TRANSACT-01',
      ip: '10.140.3.50 // DATA-LAKE',
      role: 'Primary PostgreSQL Cluster',
      status: 'ISOLATED & SECURE',
      statusColor: 'text-primary bg-primary/10 border-primary/30',
      icon: Database,
      socketSat: '32.1%',
      socketColor: 'text-primary',
      halfOpen: '6',
      targetedPorts: [
        { port: 'PORT 5432 (TLS Pool)', rate: '45 queries/s [NOMINAL]', flag: 'text-on-surface' }
      ],
      description: 'High-availability transaction database storing encrypted system state.',
      recommendation: 'Database access restricted exclusively to app cluster pool.'
    }
  };

  const currentDetail = NODE_DETAILS[selectedNode] || NODE_DETAILS['APP-01'];
  const NodeIcon = currentDetail.icon;

  return (
    <div className="w-full flex flex-col gap-5">
      {/* Top Banner */}
      <div className="bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold uppercase tracking-wider text-on-surface flex items-center gap-2">
            <Globe className="w-5 h-5 text-primary" />
            Spatial Topology Vector Graph
          </h2>
          <p className="text-xs font-mono text-outline mt-0.5">
            Real-Time Network Entity Communication & Threat Propagation Map
          </p>
        </div>

        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-error" />
            <span className="text-on-surface-variant">Anomalous Target</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-400" />
            <span className="text-on-surface-variant">Gateway / Transit</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-primary" />
            <span className="text-on-surface-variant">Nominal Core</span>
          </div>
        </div>
      </div>

      {/* Main Grid: SVG Canvas + Node Inspector Workbench */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">
        {/* SVG Spatial Topology Graph Canvas (8 cols) */}
        <div className="lg:col-span-8 bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col relative min-h-[460px] select-none">
          <div className="flex items-center justify-between text-xs font-mono text-outline mb-2">
            <span>MODEL: SPATIAL-GRAPH-CONV-V4</span>
            <span className="text-primary">SELECT NODE TO INSPECT TELEMETRY</span>
          </div>

          <div className="relative w-full flex-1 bg-surface-low rounded border border-outline-variant/30 overflow-hidden flex items-center justify-center">
            <svg viewBox="0 0 880 440" className="w-full h-full text-outline-variant">
              <defs>
                <pattern id="gridPattern" width="20" height="20" patternUnits="userSpaceOnUse">
                  <path d="M 20 0 L 0 0 0 20" fill="none" stroke="currentColor" strokeOpacity="0.1" strokeWidth="0.5" />
                </pattern>
              </defs>

              {/* Metric Background Grid */}
              <rect width="880" height="440" fill="url(#gridPattern)" />

              {/* Dynamic Connection Lines & Animated Flow Particles */}
              {/* WAN -> Gateway */}
              <line x1="120" y1="220" x2="270" y2="220" stroke={isAttack ? "#ffb4ab" : "#0ea5e9"} strokeWidth={isAttack ? "2.5" : "1.5"} strokeDasharray={isAttack ? "6,4" : "none"} />
              <circle cx="195" cy="220" r={isAttack ? "4" : "2.5"} fill={isAttack ? "#ffb4ab" : "#89ceff"}>
                <animate attributeName="cx" from="120" to="270" dur={isAttack ? "0.8s" : "2s"} repeatCount="indefinite" />
              </circle>

              {/* Gateway -> APP-01 */}
              <path d="M 270 220 C 340 220, 360 110, 440 110" fill="none" stroke={isAttack ? "#ffb4ab" : "#3e4850"} strokeWidth={isAttack ? "2.5" : "1.5"} strokeDasharray={isAttack ? "5,3" : "none"} />
              <circle cx="355" cy="165" r={isAttack ? "4" : "2"} fill={isAttack ? "#ffb4ab" : "#89ceff"}>
                <animate attributeName="cx" values="270;440" dur={isAttack ? "0.7s" : "3s"} repeatCount="indefinite" />
                <animate attributeName="cy" values="220;110" dur={isAttack ? "0.7s" : "3s"} repeatCount="indefinite" />
              </circle>

              {/* Gateway -> AUTH-01 */}
              <line x1="270" y1="220" x2="440" y2="220" stroke="#88929b" strokeWidth="1.5" strokeDasharray="3,3" />
              <circle cx="355" cy="220" r="2.5" fill="#7bd0ff">
                <animate attributeName="cx" from="270" to="440" dur="2.5s" repeatCount="indefinite" />
              </circle>

              {/* Gateway -> WORKSTATIONS */}
              <path d="M 270 220 C 340 220, 360 330, 440 330" fill="none" stroke="#3e4850" strokeWidth="1.5" />

              {/* APP-01 -> DB-01 */}
              <path d="M 580 110 C 650 110, 670 220, 730 220" fill="none" stroke={isAttack ? "#ffb4ab" : "#3e4850"} strokeWidth="1.5" />

              {/* AUTH-01 -> DB-01 */}
              <line x1="580" y1="220" x2="730" y2="220" stroke="#88929b" strokeWidth="1.5" />

              {/* INTERACTIVE NODES */}
              {/* NODE 1: EXTERNAL WAN */}
              <g className="cursor-pointer group" onClick={() => setSelectedNode('EXT-WAN')}>
                <rect x="25" y="185" width="105" height="70" rx="3" fill="#171f33" stroke={selectedNode === 'EXT-WAN' ? "#0ea5e9" : "#2d3449"} strokeWidth="2" />
                <rect x="25" y="185" width="4" height="70" fill={isAttack ? "#ffb4ab" : "#7bd0ff"} />
                <text x="38" y="205" className="font-mono text-[9px]" fill="#88929b">EXT INGRESS</text>
                <text x="38" y="223" className="font-sans text-xs font-bold" fill="#dae2fd">WAN-IN</text>
                <text x="38" y="242" className="font-mono text-[9px]" fill={isAttack ? "#ffb4ab" : "#bec8d2"}>
                  {isAttack ? 'HIGH INGRESS' : '450 flows/s'}
                </text>
              </g>

              {/* NODE 2: EDGE GATEWAY */}
              <g className="cursor-pointer group" onClick={() => setSelectedNode('GW-01')}>
                <rect x="215" y="180" width="115" height="80" rx="3" fill="#171f33" stroke={selectedNode === 'GW-01' ? "#0ea5e9" : "#2d3449"} strokeWidth="2" />
                <rect x="215" y="180" width="4" height="80" fill={isAttack ? "#fbbf24" : "#0ea5e9"} />
                <text x="228" y="202" className="font-mono text-[9px]" fill="#7bd0ff">FIREWALL</text>
                <text x="228" y="220" className="font-sans text-xs font-bold" fill="#dae2fd">EDGE-GW-01</text>
                <text x="228" y="238" className="font-mono text-[9px]" fill="#bec8d2">BW: {isAttack ? '4.24 Gbps' : '0.45 Gbps'}</text>
              </g>

              {/* NODE 3: APP-01 (TARGET NODE) */}
              <g className="cursor-pointer group" onClick={() => setSelectedNode('APP-01')}>
                {isAttack && (
                  <rect x="420" y="70" width="160" height="80" rx="4" fill="#93000a" opacity="0.3" className="animate-pulse" />
                )}
                <rect x="425" y="75" width="150" height="70" rx="3" fill="#171f33" stroke={selectedNode === 'APP-01' ? (isAttack ? "#ffb4ab" : "#0ea5e9") : (isAttack ? "#ef4444" : "#2d3449")} strokeWidth="2" />
                <rect x="425" y="75" width="4" height="70" fill={isAttack ? "#ffb4ab" : "#0ea5e9"} />
                <text x="438" y="95" className="font-mono text-[9px] font-bold" fill={isAttack ? "#ffb4ab" : "#89ceff"}>
                  {isAttack ? 'CRITICAL TARGET' : 'APP CLUSTER'}
                </text>
                <text x="438" y="113" className="font-sans text-xs font-bold" fill="#dae2fd">APP-01-CLUSTER</text>
                <text x="438" y="132" className="font-mono text-[9px] font-bold" fill={isAttack ? "#ffb4ab" : "#bec8d2"}>
                  {isAttack ? `SOCK-SAT ${(attackProb * 100).toFixed(0)}%` : 'STATUS NOMINAL'}
                </text>
              </g>

              {/* NODE 4: AUTH-01 */}
              <g className="cursor-pointer group" onClick={() => setSelectedNode('AUTH-01')}>
                <rect x="425" y="185" width="150" height="70" rx="3" fill="#171f33" stroke={selectedNode === 'AUTH-01' ? "#0ea5e9" : "#2d3449"} strokeWidth="2" />
                <rect x="425" y="185" width="4" height="70" fill="#89ceff" />
                <text x="438" y="205" className="font-mono text-[9px]" fill="#89ceff">ID ENCLAVE</text>
                <text x="438" y="223" className="font-sans text-xs font-bold" fill="#dae2fd">AUTH-SSO-01</text>
                <text x="438" y="242" className="font-mono text-[9px]" fill="#bec8d2">KERBEROS / PORT 88</text>
              </g>

              {/* NODE 5: WORKSTATIONS */}
              <g className="cursor-pointer group" onClick={() => setSelectedNode('ENDPOINTS')}>
                <rect x="425" y="295" width="150" height="70" rx="3" fill="#171f33" stroke={selectedNode === 'ENDPOINTS' ? "#0ea5e9" : "#2d3449"} strokeWidth="2" />
                <rect x="425" y="295" width="4" height="70" fill="#88929b" />
                <text x="438" y="315" className="font-mono text-[9px]" fill="#bec8d2">CORP LAN</text>
                <text x="438" y="333" className="font-sans text-xs font-bold" fill="#dae2fd">WORKSTATIONS</text>
                <text x="438" y="352" className="font-mono text-[9px]" fill="#bec8d2">42 CLIENTS NOMINAL</text>
              </g>

              {/* NODE 6: DB-01 */}
              <g className="cursor-pointer group" onClick={() => setSelectedNode('DB-01')}>
                <rect x="710" y="180" width="145" height="80" rx="3" fill="#171f33" stroke={selectedNode === 'DB-01' ? "#0ea5e9" : "#2d3449"} strokeWidth="2" />
                <rect x="710" y="180" width="4" height="80" fill="#0ea5e9" />
                <text x="723" y="202" className="font-mono text-[9px]" fill="#7bd0ff">DATA LAKE</text>
                <text x="723" y="220" className="font-sans text-xs font-bold" fill="#dae2fd">DB-TRANSACT-01</text>
                <text x="723" y="238" className="font-mono text-[9px]" fill="#89ceff">POSTGRES / PORT 5432</text>
              </g>
            </svg>
          </div>
        </div>

        {/* Node Inspection Workbench (4 cols) */}
        <div className="lg:col-span-4 bg-surface-lowest p-4 border border-outline-variant/40 rounded flex flex-col justify-between">
          <div>
            {/* Header */}
            <div className="flex items-center justify-between pb-3 mb-3 border-b border-outline-variant/30">
              <div className="flex items-center gap-2.5">
                <NodeIcon className={`w-5 h-5 ${isAttack && currentDetail.id === 'APP-01' ? 'text-error' : 'text-primary'}`} />
                <div>
                  <h3 className="text-sm font-bold text-on-surface">{currentDetail.name}</h3>
                  <span className="text-[10px] font-mono text-outline">{currentDetail.ip}</span>
                </div>
              </div>
              <span className={`text-[10px] font-mono px-2 py-0.5 rounded border font-bold uppercase ${currentDetail.statusColor}`}>
                {currentDetail.status}
              </span>
            </div>

            {/* Metrics */}
            <div className="flex flex-col gap-3">
              <div className="bg-surface-low p-3 rounded border border-outline-variant/30">
                <span className="text-[10px] font-mono text-outline uppercase">Node Description</span>
                <p className="text-xs text-on-surface-variant mt-1 leading-relaxed">
                  {currentDetail.description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div className="bg-surface-low p-2.5 rounded border border-outline-variant/30">
                  <span className="text-[10px] font-mono text-outline uppercase">Socket Saturation</span>
                  <div className="text-sm font-mono font-bold text-on-surface mt-1">{currentDetail.socketSat}</div>
                </div>
                <div className="bg-surface-low p-2.5 rounded border border-outline-variant/30">
                  <span className="text-[10px] font-mono text-outline uppercase">Half-Open Conns</span>
                  <div className="text-sm font-mono font-bold text-on-surface mt-1">{currentDetail.halfOpen}</div>
                </div>
              </div>

              {/* Port Vectors */}
              <div className="bg-surface-low p-3 rounded border border-outline-variant/30">
                <span className="text-[10px] font-mono text-outline uppercase mb-1.5 block">Targeted Port Vectors</span>
                <div className="flex flex-col gap-1 text-xs font-mono">
                  {currentDetail.targetedPorts.map((pv, idx) => (
                    <div key={idx} className="flex items-center justify-between">
                      <span className="text-on-surface">{pv.port}</span>
                      <span className={pv.flag}>{pv.rate}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Prescriptive Recommendation */}
              <div className="bg-surface-low p-3 rounded border border-outline-variant/30">
                <span className="text-[10px] font-mono text-primary uppercase font-semibold block mb-1">
                  PRESCRIPTIVE ACTION
                </span>
                <p className="text-xs text-on-surface leading-normal">
                  {currentDetail.recommendation}
                </p>
              </div>
            </div>
          </div>

          <div className="pt-4 flex flex-col gap-2">
            <button className={`w-full py-2 px-3 text-xs font-mono font-bold rounded flex items-center justify-center gap-2 transition-colors ${
              isAttack && currentDetail.id === 'APP-01'
                ? 'bg-error text-on-error hover:bg-error-container'
                : 'bg-surface-high text-on-surface hover:bg-surface-variant'
            }`}>
              <ShieldAlert className="w-4 h-4" />
              <span>ISOLATE & ENFORCE CONFINEMENT</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

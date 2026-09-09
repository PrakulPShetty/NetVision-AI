import React from 'react';
import MitreIntelView from '../components/mitre/MitreIntelView';

export default function AttackIntelPage({ mitreData }) {
  return (
    <div>
      <MitreIntelView mitreData={mitreData} />
    </div>
  );
}

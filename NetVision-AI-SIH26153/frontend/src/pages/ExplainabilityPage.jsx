import React from 'react';
import ExplainabilityView from '../components/xai/ExplainabilityView';

export default function ExplainabilityPage({ xaiData }) {
  return (
    <div>
      <ExplainabilityView xaiData={xaiData} />
    </div>
  );
}

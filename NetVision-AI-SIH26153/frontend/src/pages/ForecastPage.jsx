import React from 'react';
import ForecastChart from '../components/forecast/ForecastChart';

export default function ForecastPage({ forecastData }) {
  return (
    <div>
      <ForecastChart forecastData={forecastData} />
    </div>
  );
}

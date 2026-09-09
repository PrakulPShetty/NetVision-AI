import React, { useState } from 'react';

export default function NetVisionLogo({ className = "h-9", showText = true }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div className="flex items-center gap-3 select-none">
      {!imgError ? (
        <img
          src="/logo.png"
          alt="NetVision AI Official Logo"
          className={`${className} object-contain`}
          onError={() => setImgError(true)}
        />
      ) : (
        <div className="flex items-center gap-2 font-mono text-primary font-bold text-base">
          <span>NETVISION</span>
          <span className="text-content-primary">AI</span>
        </div>
      )}
      {showText && (
        <div className="flex flex-col leading-tight">
          <span className="text-base font-bold tracking-tight text-content-primary">
            NETVISION<span className="text-primary ml-1">AI</span>
          </span>
          <span className="text-[10px] font-medium text-content-muted tracking-wider uppercase">
            Predictive Network Security Intelligence
          </span>
        </div>
      )}
    </div>
  );
}

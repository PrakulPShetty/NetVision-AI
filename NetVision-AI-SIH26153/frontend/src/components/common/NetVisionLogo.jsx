import React, { useState } from 'react';
import { ShieldAlert } from 'lucide-react';

export default function NetVisionLogo({ className = "h-8", showText = true }) {
  const [imgError, setImgError] = useState(false);

  return (
    <div className="flex items-center gap-3 select-none">
      {!imgError ? (
        <img
          src="/logo.png"
          alt="NetVision AI"
          className={`${className} object-contain`}
          onError={() => setImgError(true)}
        />
      ) : (
        <div className="w-8 h-8 rounded bg-primary-dark/20 border border-primary/40 flex items-center justify-center text-primary">
          <ShieldAlert className="w-5 h-5" />
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

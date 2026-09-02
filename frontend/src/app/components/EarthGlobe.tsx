'use client';

import { useEffect, useRef, useState } from 'react';
import Globe from 'react-globe.gl';

export default function EarthGlobe() {
  const globeEl = useRef<any>();
  const [dimensions, setDimensions] = useState({ width: 1000, height: 1000 });

  useEffect(() => {
    setDimensions({ width: window.innerWidth, height: window.innerHeight });

    const handleResize = () => setDimensions({ width: window.innerWidth, height: window.innerHeight });
    window.addEventListener('resize', handleResize);

    if (globeEl.current) {
      globeEl.current.controls().autoRotate = true;
      globeEl.current.controls().autoRotateSpeed = 0.4;
      globeEl.current.controls().enableZoom = true;
      
      // Point camera to show earth nicely framed
      globeEl.current.pointOfView({ altitude: 1.1 });
    }

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  return (
    <div className="absolute inset-0 flex items-center justify-center pointer-events-auto" style={{ zIndex: 0 }}>
      {typeof window !== 'undefined' && (
        <Globe
          ref={globeEl}
          width={dimensions.width}
          height={dimensions.height}
          
          // Realistic Earth Textures
          globeImageUrl="/earth_day.jpg"
          bumpImageUrl="/earth_topo.png"
          
          // HD 3D Space Background (Stars, distant planets/nebula look)
          backgroundImageUrl="//unpkg.com/three-globe/example/img/night-sky.png"
          
          // Remove atmosphere red glow for realistic space look
          showAtmosphere={false}
          
          // (White scatter dots removed as requested)
        />
      )}
    </div>
  );
}

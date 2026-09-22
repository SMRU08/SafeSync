import React, { useRef, useEffect } from 'react';
import { ActiveTab } from './Sidebar';

interface CustomDesignFrameProps {
  src: string;
  onNavigate?: (tab: ActiveTab) => void;
  title: string;
}

export const CustomDesignFrame: React.FC<CustomDesignFrameProps> = ({
  src,
  onNavigate,
  title,
}) => {
  const iframeRef = useRef<HTMLIFrameElement>(null);

  useEffect(() => {
    const handleMessage = (event: MessageEvent) => {
      if (event.data && event.data.type === 'NAVIGATE' && onNavigate) {
        onNavigate(event.data.tab as ActiveTab);
      }
    };
    window.addEventListener('message', handleMessage);
    return () => window.removeEventListener('message', handleMessage);
  }, [onNavigate]);

  const handleLoad = () => {
    try {
      const iframe = iframeRef.current;
      if (!iframe || !iframe.contentDocument) return;
      const doc = iframe.contentDocument;

      // Intercept sidebar / nav links inside the loaded custom HTML
      const links = doc.querySelectorAll('nav a, aside a, header a');
      links.forEach((link) => {
        link.addEventListener('click', (e) => {
          const text = (link.textContent || '').toLowerCase().trim();
          if (
            text.includes('overview') ||
            text.includes('camera') ||
            text.includes('monitoring') ||
            text.includes('worker') ||
            text.includes('ppe') ||
            text.includes('fire') ||
            text.includes('smoke') ||
            text.includes('alert') ||
            text.includes('incident') ||
            text.includes('analytic') ||
            text.includes('health') ||
            text.includes('system') ||
            text.includes('config') ||
            text.includes('setting') ||
            text.includes('escalat') ||
            text.includes('simulat')
          ) {
            e.preventDefault();
            if (text.includes('overview')) onNavigate?.('overview');
            else if (text.includes('camera') || text.includes('monitoring')) onNavigate?.('cameras');
            else if (text.includes('worker') || text.includes('ppe')) onNavigate?.('workers');
            else if (text.includes('fire') || text.includes('smoke')) onNavigate?.('hazards');
            else if (text.includes('alert') || text.includes('incident')) onNavigate?.('alerts');
            else if (text.includes('analytic')) onNavigate?.('analytics');
            else if (text.includes('health') || text.includes('system')) onNavigate?.('health');
            else if (text.includes('config') || text.includes('setting')) onNavigate?.('settings');
            else if (text.includes('escalat') || text.includes('simulat')) onNavigate?.('simulation');
          }
        });
      });
    } catch {
      // Ignore cross-origin constraints if any
    }
  };

  return (
    <div className="w-full h-full flex-1 overflow-hidden bg-[#eef3f9]">
      <iframe
        ref={iframeRef}
        src={src}
        title={title}
        onLoad={handleLoad}
        className="w-full h-full border-0 block"
        style={{ width: '100%', height: '100%', minHeight: '100vh', border: 'none' }}
      />
    </div>
  );
};

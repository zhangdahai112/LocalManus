'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { Monitor, X, ChevronLeft, ChevronRight, Maximize2, Minimize2, PanelRightOpen, PanelRightClose } from 'lucide-react';
import { getApiBaseUrl } from '../utils/api';
import styles from './vncPreview.module.css';

interface VNCPreviewProps {
  isChatMode: boolean;
}

// Panel width states
const PANEL_WIDTHS = {
  collapsed: 48,      // Just the toggle button
  compact: 400,       // Smaller view
  expanded: 600,      // Default larger view
  full: 900,          // Maximum width
};

export default function VNCPreview({ isChatMode }: VNCPreviewProps) {
  const [panelWidth, setPanelWidth] = useState<number>(PANEL_WIDTHS.expanded);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isResizing, setIsResizing] = useState(false);
  const [vncUrl, setVncUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    const fetchVNCUrl = async () => {
      try {
        setIsLoading(true);
        const token = localStorage.getItem('access_token');
        const baseUrl = getApiBaseUrl();
        
        const response = await fetch(`${baseUrl}/api/sandbox/info`, {
          headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
          const result = await response.json();
          const vncUrlFromApi = result.data?.vnc_url || result.vnc_url;
          
          if (vncUrlFromApi) {
            const isProduction = process.env.NODE_ENV === 'production';
            if (isProduction || window.location.port === '1243') {
              setVncUrl('/vnc/index.html?autoconnect=true');
            } else {
              setVncUrl(vncUrlFromApi);
            }
          } else {
            setVncUrl('/vnc/index.html?autoconnect=true');
          }
        } else {
          setVncUrl('/vnc/index.html?autoconnect=true');
        }
      } catch (err) {
        console.error('Failed to fetch VNC URL:', err);
        setVncUrl('/vnc/index.html?autoconnect=true');
        setError('Using default VNC URL');
      } finally {
        setIsLoading(false);
      }
    };

    if (isChatMode) {
      fetchVNCUrl();
    }
  }, [isChatMode]);

  // Handle resize
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizing(true);
  }, []);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isResizing) return;
      const newWidth = window.innerWidth - e.clientX;
      const clampedWidth = Math.max(PANEL_WIDTHS.compact, Math.min(PANEL_WIDTHS.full, newWidth));
      setPanelWidth(clampedWidth);
    };

    const handleMouseUp = () => {
      setIsResizing(false);
    };

    if (isResizing) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
    };
  }, [isResizing]);

  // Toggle functions
  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed);
  };

  const cycleWidth = () => {
    if (panelWidth >= PANEL_WIDTHS.full * 0.9) {
      setPanelWidth(PANEL_WIDTHS.compact);
    } else if (panelWidth >= PANEL_WIDTHS.expanded * 0.9) {
      setPanelWidth(PANEL_WIDTHS.full);
    } else {
      setPanelWidth(PANEL_WIDTHS.expanded);
    }
  };

  if (!isChatMode) return null;

  // Collapsed state
  if (isCollapsed) {
    return (
      <div className={styles.collapsedContainer}>
        <button 
          className={styles.toggleButton}
          onClick={toggleCollapse}
          title="展开 VNC 预览"
        >
          <PanelRightOpen size={20} />
          <Monitor size={16} />
        </button>
      </div>
    );
  }

  // Calculate responsive height based on aspect ratio
  const aspectRatio = 16 / 10;

  return (
    <div 
      className={styles.container}
      style={{ width: panelWidth }}
    >
      {/* Resize handle */}
      <div 
        className={`${styles.resizeHandle} ${isResizing ? styles.resizing : ''}`}
        onMouseDown={handleMouseDown}
        title="拖动调整宽度"
      >
        <div className={styles.resizeIndicator} />
      </div>

      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <Monitor size={18} className={styles.headerIcon} />
          <span className={styles.headerTitle}>沙盒预览</span>
          {isLoading && <span className={styles.loadingText}>连接中...</span>}
        </div>
        <div className={styles.headerActions}>
          <button 
            className={styles.iconButton}
            onClick={cycleWidth}
            title={panelWidth >= PANEL_WIDTHS.expanded ? "缩小" : "放大"}
          >
            {panelWidth >= PANEL_WIDTHS.expanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
          <button 
            className={styles.iconButton}
            onClick={toggleCollapse}
            title="收起"
          >
            <PanelRightClose size={16} />
          </button>
        </div>
      </div>

      {/* VNC Iframe - Responsive container */}
      <div className={styles.iframeContainer}>
        {vncUrl ? (
          <iframe
            src={vncUrl}
            className={styles.vncIframe}
            title="VNC Preview"
            allow="fullscreen"
            style={{ aspectRatio: `${aspectRatio}` }}
          />
        ) : (
          <div className={styles.placeholder}>
            <Monitor size={56} className={styles.placeholderIcon} />
            <p className={styles.placeholderText}>VNC 预览加载中...</p>
            {error && <p className={styles.errorText}>{error}</p>}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className={styles.footer}>
        <span className={styles.footerText}>沙盒浏览器实时预览</span>
        <a 
          href={vncUrl} 
          target="_blank" 
          rel="noopener noreferrer"
          className={styles.openLink}
        >
          全屏打开
        </a>
      </div>
    </div>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import { Monitor, X, ChevronLeft, ChevronRight, Maximize2, Minimize2 } from 'lucide-react';
import { getApiBaseUrl } from '../utils/api';
import styles from './vncPreview.module.css';

interface VNCPreviewProps {
  isChatMode: boolean;
}

export default function VNCPreview({ isChatMode }: VNCPreviewProps) {
  const [isExpanded, setIsExpanded] = useState(true);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [vncUrl, setVncUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string>('');

  useEffect(() => {
    // Get VNC URL from sandbox info
    const fetchVNCUrl = async () => {
      try {
        setIsLoading(true);
        const token = localStorage.getItem('access_token');
        const baseUrl = getApiBaseUrl();
        
        // Try to get sandbox info from backend
        const response = await fetch(`${baseUrl}/api/sandbox/info`, {
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
        
        if (response.ok) {
          const result = await response.json();
          // Handle both formats: { data: { vnc_url } } or { vnc_url }
          const vncUrlFromApi = result.data?.vnc_url || result.vnc_url;
          
          if (vncUrlFromApi) {
            // In production, VNC is proxied through nginx at /vnc/
            // Replace the direct sandbox URL with the proxied path
            const isProduction = process.env.NODE_ENV === 'production';
            if (isProduction || window.location.port === '1243') {
              // Use relative path for VNC (proxied through nginx)
              setVncUrl('/vnc/index.html?autoconnect=true');
            } else {
              setVncUrl(vncUrlFromApi);
            }
          } else {
            setVncUrl('/vnc/index.html?autoconnect=true');
          }
        } else {
          // Fallback to proxied VNC URL
          setVncUrl('/vnc/index.html?autoconnect=true');
        }
      } catch (err) {
        console.error('Failed to fetch VNC URL:', err);
        // Fallback to proxied VNC URL
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

  // Don't render in home mode
  if (!isChatMode) {
    return null;
  }

  // Collapsed state - show toggle button only
  if (isCollapsed) {
    return (
      <div className={styles.collapsedContainer}>
        <button 
          className={styles.expandButton}
          onClick={() => setIsCollapsed(false)}
          title="展开 VNC 预览"
        >
          <ChevronLeft size={20} />
          <Monitor size={18} />
        </button>
      </div>
    );
  }

  return (
    <div className={`${styles.container} ${isExpanded ? styles.expanded : styles.compact}`}>
      {/* Header */}
      <div className={styles.header}>
        <div className={styles.headerLeft}>
          <Monitor size={16} className={styles.headerIcon} />
          <span className={styles.headerTitle}>沙盒预览</span>
          {isLoading && <span className={styles.loadingText}>连接中...</span>}
        </div>
        <div className={styles.headerActions}>
          <button 
            className={styles.headerButton}
            onClick={() => setIsExpanded(!isExpanded)}
            title={isExpanded ? "缩小" : "放大"}
          >
            {isExpanded ? <Minimize2 size={16} /> : <Maximize2 size={16} />}
          </button>
          <button 
            className={styles.headerButton}
            onClick={() => setIsCollapsed(true)}
            title="收起"
          >
            <ChevronRight size={16} />
          </button>
        </div>
      </div>

      {/* VNC Iframe */}
      <div className={styles.iframeContainer}>
        {vncUrl ? (
          <iframe
            src={vncUrl}
            className={styles.vncIframe}
            title="VNC Preview"
            allow="fullscreen"
          />
        ) : (
          <div className={styles.placeholder}>
            <Monitor size={48} className={styles.placeholderIcon} />
            <p className={styles.placeholderText}>VNC 预览加载中...</p>
            {error && <p className={styles.errorText}>{error}</p>}
          </div>
        )}
      </div>

      {/* Footer info */}
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

'use client';

import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Omnibox from './components/Omnibox';
import Toolbox from './components/Toolbox';
import UserStatus from './components/UserStatus';
import MarkdownRenderer from './components/MarkdownRenderer';
import { getApiBaseUrl } from './utils/api';
import { Plus, User, Bot, Wrench, Search, Eye, Zap, FileText, Palette, BookOpen, BarChart3, Globe, Languages, PlayCircle, Mic } from 'lucide-react';
import styles from './page.module.css';

export default function Home() {
  const [isChatMode, setIsChatMode] = useState(false);
  const [messages, setMessages] = useState<{ 
    role: 'user' | 'bot', 
    content: string, 
    type?: string,
    thought?: string,
    observation?: string,
    call?: { skill: string, tool: string, params: string }
  }[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState(() => Math.random().toString(36).substring(7));
  const [uploadedFiles, setUploadedFiles] = useState<Array<{id: number, filename: string, file_path: string, original_filename: string}>>([]);
  const contentRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Only auto-scroll in chat mode and when there are messages
    if (isChatMode && messages.length > 0 && contentRef.current) {
      // Use requestAnimationFrame to ensure the DOM has updated before scrolling
      requestAnimationFrame(() => {
        if (contentRef.current) {
          contentRef.current.scrollTo({
            top: contentRef.current.scrollHeight,
            behavior: 'smooth'
          });
        }
      });
    }
  }, [messages, isChatMode]);

  const handleSendMessage = async (text: string, filePaths?: string[]) => {
    if ((!text.trim() && !filePaths?.length) || isLoading) return;

    if (!isChatMode) {
      setIsChatMode(true);
    }

    // Build user message content
    let userContent = text;
    if (filePaths && filePaths.length > 0) {
      const filePathsText = filePaths.map(p => `[文件: ${p}]`).join('\n');
      userContent = filePathsText + (text ? '\n\n' + text : '');
    }

    const newUserMessage = { role: 'user' as const, content: userContent };
    setMessages(prev => [...prev, newUserMessage]);
    setIsLoading(true);

    // Log for debugging
    console.log('handleSendMessage called with filePaths:', filePaths);

    try {
      // Add initial bot message for streaming
      setMessages(prev => [...prev, { role: 'bot', content: '', thought: '', observation: '' }]);

      const token = localStorage.getItem('access_token');
      
      const baseUrl = getApiBaseUrl();
      // Build URL with file paths if provided
      let url = `${baseUrl}/api/chat?input=${encodeURIComponent(text)}&session_id=${sessionId}`;
      if (filePaths && filePaths.length > 0) {
        const filePathsParam = filePaths.join(',');
        console.log('File paths parameter:', filePathsParam);
        url += `&file_paths=${encodeURIComponent(filePathsParam)}`;
      }
      if (token) {
        url += `&access_token=${token}`;
      }
      
      console.log('Request URL:', url);
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const reader = response.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      
      if (reader) {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          
          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split('\n');
          // Keep the last partial line in the buffer
          buffer = lines.pop() || '';
          
          for (const line of lines) {
            const trimmedLine = line.trim();
            if (!trimmedLine || !trimmedLine.startsWith('data: ')) continue;
            
            const dataStr = trimmedLine.replace('data: ', '').trim();
            if (dataStr === '[DONE]') continue;
            
            try {
              const data = JSON.parse(dataStr);
              
              if (data.content) {
                setMessages(prev => {
                  const newMessages = [...prev];
                  const lastIndex = newMessages.length - 1;
                  if (lastIndex >= 0 && newMessages[lastIndex].role === 'bot') {
                    newMessages[lastIndex] = {
                      ...newMessages[lastIndex],
                      content: newMessages[lastIndex].content + data.content
                    };
                  }
                  return newMessages;
                });
              }
            } catch (e) {
              console.error('Error parsing SSE data:', e);
            }
          }
        }
      }
      
      // Clear uploaded files after successful send
      setUploadedFiles([]);
    } catch (error) {
      console.error('Error fetching chat:', error);
      setMessages(prev => [...prev, { role: 'bot', content: '抱歉，发生了错误。请稍后再试。' }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setIsChatMode(false);
    setSessionId(Math.random().toString(36).substring(7));
    setUploadedFiles([]); // Clear uploaded files when starting new chat
    
    // Scroll to top when returning to home page
    if (contentRef.current) {
      contentRef.current.scrollTo({
        top: 0,
        behavior: 'smooth'
      });
    }
  };

  const tabs = ['全部模板', '创意与设计', '通用', '营销增长', '产品调研', '市场推广', '学习与成长', '求职发展', '我的模板'];

  const templates = [
    { type: 'upload', name: '上传 PPTX 文件作为模板', icon: 'PPT' },
    { type: 'create', name: '创建空白文档', icon: '+' },
    { type: 'template', name: 'Video to Webpage', tag: 'Web page', color: '#e6f4ea', textColor: '#1e8e3e', usage: '2,359' },
    { type: 'template', name: 'Team OKR Retrospective', tag: 'Slides', color: '#fef1e8', textColor: '#e67c39', usage: '12,940' },
    { type: 'template', name: 'Packaging Design', tag: 'Design', color: '#f3e8ff', textColor: '#9333ea', usage: '170' },
    { type: 'template', name: 'YouTube Thumbnail', tag: 'Design', color: '#f3e8ff', textColor: '#9333ea', usage: '148' },
    { type: 'template', name: 'AI Daily Digest', tag: 'Doc', color: '#e8f0fe', textColor: '#1a73e8', usage: '15,837' },
    { type: 'template', name: 'Horizontal Product Poster', tag: 'Design', color: '#f3e8ff', textColor: '#9333ea', usage: '187' },
    { type: 'template', name: 'Strategic Management Basics', tag: 'Slides', color: '#fef1e8', textColor: '#e67c39', usage: '8,241' },
    { type: 'template', name: 'Product Launch Deck', tag: 'Slides', color: '#fef1e8', textColor: '#e67c39', usage: '5,402' },
  ];

  return (
    <main className={`${styles.main} ${isChatMode ? styles.chatMode : ''}`}>
      <Sidebar onNewChat={handleNewChat} />

      <div className={styles.topRightActions}>
        <UserStatus />
      </div>

      <div className={styles.content} ref={contentRef}>
        <div className={styles.container}>
          <header className={styles.header}>
            <h1 className={styles.title}>今天可以帮你做什么？</h1>
          </header>

          {!isChatMode && (
            <div className={styles.homeContent}>
              <nav className={styles.homeTabs}>
                <div className={styles.homeTab}><Zap size={16} color="#eab308" /> 生成幻灯片</div>
                <div className={styles.homeTab}><FileText size={16} color="#3b82f6" /> 撰写文档</div>
                <div className={styles.homeTab}><Palette size={16} color="#ec4899" /> 生成设计</div>
                <div className={styles.homeTab}><BookOpen size={16} color="#8b5cf6" /> 创建故事绘本</div>
                <div className={styles.homeTab}><Search size={16} color="#10b981" /> 批量调研</div>
                <div className={styles.homeTab}><BarChart3 size={16} color="#f97316" /> 分析数据</div>
                <div className={styles.homeTab}><Globe size={16} color="#06b6d4" /> 创建网页</div>
                <div className={styles.homeTab}><Languages size={16} color="#6366f1" /> 翻译 PDF</div>
                <div className={styles.homeTab}><PlayCircle size={16} color="#ef4444" /> 总结视频</div>
                <div className={styles.homeTab}><Mic size={16} color="#14b8a6" /> 撰写音频</div>
              </nav>
              <div className={styles.homeOmnibox}>
                <Omnibox 
                  onOpenChat={handleSendMessage} 
                  disabled={isLoading}
                  uploadedFiles={uploadedFiles}
                  onUploadedFilesChange={setUploadedFiles}
                />
              </div>
            </div>
          )}

          {isChatMode && (
            <div className={styles.chatInterface}>
              <div className={styles.messageList}>
                {messages.map((msg, i) => (
                  <div key={i} className={`${styles.message} ${msg.role === 'user' ? styles.userMessage : styles.botMessage}`}>
                    <div className={styles.avatar}>
                      {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                    </div>
                    <div className={styles.messageContent}>
                      {msg.role === 'bot' ? (
                        <MarkdownRenderer content={msg.content || ''} />
                      ) : (
                        msg.content && msg.content.split('\n').map((line, j) => (
                          <div key={j} className={line.startsWith('[Tool Use]') || line.startsWith('[Observation]') || line.startsWith('[Error]') ? styles.systemLog : ''}>
                            {line}
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {isChatMode && (
            <div className={styles.fixedOmnibox}>
              <div className={styles.fixedOmniboxInner}>
                <Omnibox 
                  onOpenChat={handleSendMessage} 
                  disabled={isLoading}
                  uploadedFiles={uploadedFiles}
                  onUploadedFilesChange={setUploadedFiles}
                />
              </div>
            </div>
          )}
          
          <Toolbox isHidden={isChatMode} />

          <section className={styles.templates}>
            <nav className={styles.tabNav}>
              {tabs.map((tab, i) => (
                <div key={i} className={`${styles.tab} ${i === 0 ? styles.activeTab : ''}`}>
                  {tab === '我的模板' && <span className={styles.sparkle}>✨</span>}
                  {tab}
                </div>
              ))}
            </nav>

            <div className={styles.templateGrid}>
              {templates.map((tpl, i) => (
                <div key={i} className={styles.templateCard}>
                  <div className={`${styles.templateThumb} ${tpl.type !== 'template' ? styles.specialThumb : ''}`}>
                    {tpl.type === 'upload' && <div className={styles.pptIcon}>P</div>}
                    {tpl.type === 'create' && <div className={styles.plusIcon}><Plus size={32} color="#3b82f6" /></div>}
                    {tpl.type === 'template' && <div className={styles.placeholderImg}></div>}
                  </div>
                  <div className={styles.templateInfo}>
                    <div className={styles.templateName}>{tpl.name}</div>
                    {tpl.type === 'template' && (
                      <div className={styles.templateMeta}>
                        <span
                          className={styles.tag}
                          style={{ backgroundColor: tpl.color, color: tpl.textColor }}
                        >
                          {tpl.tag}
                        </span>
                        <span className={styles.usage}>{tpl.usage} 次使用</span>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </main>
  );
}

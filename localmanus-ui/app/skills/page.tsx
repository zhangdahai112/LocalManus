'use client';

import React, { useState, useEffect } from 'react';
import { Search, Settings, CheckCircle, Circle, Info, ChevronRight } from 'lucide-react';
import * as Icons from 'lucide-react';
import styles from './skills.module.css';

interface Tool {
  name: string;
  description: string;
  parameters: any;
  required: string[];
}

interface Skill {
  id: string;
  name: string;
  category: string;
  description: string;
  icon: string;
  enabled: boolean;
  tools: Tool[];
  config: Record<string, any>;
}

import Sidebar from '../components/Sidebar';
import UserStatus from '../components/UserStatus';
import { getApiBaseUrl } from '../utils/api';
import styles from './skills.module.css';

export default function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedSkill, setSelectedSkill] = useState<Skill | null>(null);
  const [showConfig, setShowConfig] = useState(false);

  const handleNewChat = () => {
    window.location.href = '/';
  };

  useEffect(() => {
    fetchSkills();
  }, []);

    const fetchSkills = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const baseUrl = getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/skills`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                setSkills(data);
            }
        } catch (error) {
            console.error('Failed to fetch skills:', error);
        }
    };

    const toggleSkillStatus = async (skillId: string) => {
        const token = localStorage.getItem('access_token');
        const skill = skills.find(s => s.id === skillId);
        if (!skill) return;

        const baseUrl = getApiBaseUrl();
        const response = await fetch(`${baseUrl}/api/skills/${skillId}/status`, {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ enabled: !skill.enabled })
        });

        if (response.ok) {
            fetchSkills();
        }
    };

  const filteredSkills = skills.filter(skill =>
    skill.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    skill.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getIconComponent = (iconName: string) => {
    const IconComponent = (Icons as any)[iconName];
    return IconComponent ? <IconComponent size={24} /> : <Icons.Wrench size={24} />;
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      search: '#3b82f6',
      file: '#10b981',
      creative: '#ec4899',
      system: '#f59e0b',
      general: '#6b7280'
    };
    return colors[category] || colors.general;
  };

  return (
    <main style={{ display: 'flex', backgroundColor: '#fcfcfc', minHeight: '100vh' }}>
      <Sidebar onNewChat={handleNewChat} />
      
      <div style={{ position: 'fixed', top: '12px', right: '12px', zIndex: 1000 }}>
        <UserStatus />
      </div>

      <div className={styles.container}>
        <header className={styles.header}>
          <div>
            <h1 className={styles.title}>技能库</h1>
            <p className={styles.subtitle}>管理和配置 AI Agent 的核心能力</p>
          </div>
          <div className={styles.searchBox}>
            <Search size={20} className={styles.searchIcon} />
            <input
              type="text"
              placeholder="搜索技能名称或描述..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className={styles.searchInput}
            />
          </div>
        </header>

        {loading ? (
          <div className={styles.loading}>正在加载技能库...</div>
        ) : (
          <>
            {filteredSkills.length === 0 ? (
              <div className={styles.loading}>没有找到相关的技能</div>
            ) : (
              <div className={styles.skillsGrid}>
                {filteredSkills.map((skill) => (
                  <div key={skill.id} className={styles.skillCard}>
                    <div className={styles.skillHeader}>
                      <div 
                        className={styles.skillIcon}
                        style={{ backgroundColor: `${getCategoryColor(skill.category)}15`, color: getCategoryColor(skill.category) }}
                      >
                        {getIconComponent(skill.icon)}
                      </div>
                      <div className={styles.skillInfo}>
                        <h3 className={styles.skillName}>{skill.name}</h3>
                        <p className={styles.skillDescription}>{skill.description}</p>
                      </div>
                      <button
                        className={`${styles.statusToggle} ${skill.enabled ? styles.enabled : ''}`}
                        onClick={() => toggleSkillStatus(skill.id, !skill.enabled)}
                        title={skill.enabled ? '禁用技能' : '启用技能'}
                      >
                        {skill.enabled ? <CheckCircle size={22} fill="currentColor" color="white" /> : <Circle size={22} />}
                      </button>
                    </div>

                    <div className={styles.skillBody}>
                      <div className={styles.toolsCount}>
                        包含 {skill.tools.length} 个工具
                      </div>
                      
                      <div className={styles.toolsList}>
                        {skill.tools.slice(0, 3).map((tool, index) => (
                          <div key={index} className={styles.toolItem}>
                            <ChevronRight size={14} />
                            <span>{tool.name}</span>
                          </div>
                        ))}
                        {skill.tools.length > 3 && (
                          <div className={styles.moreTools}>
                            还有 {skill.tools.length - 3} 个更多工具...
                          </div>
                        )}
                      </div>
                    </div>

                    <div className={styles.skillFooter}>
                      <button
                        className={styles.detailsButton}
                        onClick={() => {
                          setSelectedSkill(skill);
                          setShowConfig(false);
                        }}
                      >
                        <Info size={16} />
                        详情
                      </button>
                      <button
                        className={styles.configButton}
                        onClick={() => {
                          setSelectedSkill(skill);
                          setShowConfig(true);
                        }}
                      >
                        <Settings size={16} />
                        配置
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {selectedSkill && (
          <div className={styles.modal} onClick={() => setSelectedSkill(null)}>
            <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
              <div className={styles.modalHeader}>
                <div>
                  <h2>{selectedSkill.name}</h2>
                  <p className={styles.modalSubtitle}>{selectedSkill.description}</p>
                </div>
                <button className={styles.closeButton} onClick={() => setSelectedSkill(null)}>
                  ×
                </button>
              </div>

              <div className={styles.modalBody}>
                {showConfig ? (
                  <div className={styles.configSection}>
                    <h3>技能配置</h3>
                    <p className={styles.configNote}>
                      您可以自定义技能的运行参数。目前显示为默认设置。
                    </p>
                    <pre className={styles.configJson}>
                      {JSON.stringify(selectedSkill.config, null, 2) || '{}'}
                    </pre>
                  </div>
                ) : (
                  <div className={styles.detailsSection}>
                    <h3>可用工具</h3>
                    {selectedSkill.tools.map((tool, index) => (
                      <div key={index} className={styles.toolDetail}>
                        <div className={styles.toolDetailHeader}>
                          <h4>{tool.name}</h4>
                        </div>
                        <p className={styles.toolDetailDescription}>{tool.description}</p>
                        {tool.parameters && tool.parameters.properties && (
                          <div className={styles.parameters}>
                            <strong>调用参数:</strong>
                            <ul>
                              {Object.entries(tool.parameters.properties).map(([key, value]: [string, any]) => (
                                <li key={key}>
                                  <code>{key}</code>
                                  {tool.required?.includes(key) && <span className={styles.required}>*</span>}
                                  : {value.description || value.type}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className={styles.modalFooter}>
                <button className={styles.switchButton} onClick={() => setShowConfig(!showConfig)}>
                  {showConfig ? '查看工具详情' : '进入配置模式'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

'use client';

import React, { useState, useEffect } from 'react';
import Sidebar from '../components/Sidebar';
import UserStatus from '../components/UserStatus';
import { getApiBaseUrl } from '../utils/api';
import styles from './settings.module.css';

export default function SettingsPage() {
    const [config, setConfig] = useState({
        MODEL_NAME: '',
        OPENAI_API_KEY: '',
        OPENAI_API_BASE: '',
        AGENT_MEMORY_LIMIT: '',
        UPLOAD_SIZE_LIMIT: ''
    });
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);
    const [message, setMessage] = useState('');

    useEffect(() => {
        loadSettings();
    }, []);

    const loadSettings = async () => {
        try {
            const token = localStorage.getItem('access_token');
            const baseUrl = getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/settings`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (response.ok) {
                const data = await response.json();
                setConfig(data);
            }
        } catch (error) {
            console.error('Failed to load settings:', error);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        setMessage('');
        
        try {
            const token = localStorage.getItem('access_token');
            const baseUrl = getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/settings`, {
                method: 'PUT',
                headers: {
                    'Authorization': `Bearer ${token}`,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(config)
            });
            
            if (response.ok) {
                setMessage('设置已保存');
                setTimeout(() => setMessage(''), 3000);
            } else {
                setMessage('保存失败');
            }
        } catch (error) {
            console.error('Failed to save settings:', error);
            setMessage('保存失败');
        } finally {
            setSaving(false);
        }
    };

    const handleNewChat = () => {
        window.location.href = '/';
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
                        <h1 className={styles.title}>系统设置</h1>
                        <p className={styles.subtitle}>管理大模型、API 和系统运行参数</p>
                    </div>
                </header>

                {loading ? (
                    <div className={styles.loading}>正在加载系统配置...</div>
                ) : (
                    <div className={styles.settingsGrid}>
                        {message && (
                            <div className={`${styles.message} ${styles[message.type]}`}>
                                {message.text}
                            </div>
                        )}

                        <section className={styles.section}>
                            <h2 className={styles.sectionTitle}>
                                <Cpu size={22} color="var(--accent)" />
                                模型配置
                            </h2>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>模型名称 (MODEL_NAME)</label>
                                <input
                                    className={styles.input}
                                    value={config.MODEL_NAME}
                                    onChange={e => setConfig({ ...config, MODEL_NAME: e.target.value })}
                                    placeholder="例如: gpt-4o, claude-3-5-sonnet"
                                />
                                <span className={styles.hint}>AI Agent 使用的主模型标识符</span>
                            </div>
                        </section>

                        <section className={styles.section}>
                            <h2 className={styles.sectionTitle}>
                                <Globe size={22} color="#10b981" />
                                API 连接
                            </h2>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>API 基础地址 (OPENAI_API_BASE)</label>
                                <input
                                    className={styles.input}
                                    value={config.OPENAI_API_BASE}
                                    onChange={e => setConfig({ ...config, OPENAI_API_BASE: e.target.value })}
                                    placeholder="https://api.openai.com/v1"
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>API 密钥 (OPENAI_API_KEY)</label>
                                <input
                                    className={styles.input}
                                    type="password"
                                    value={config.OPENAI_API_KEY}
                                    onChange={e => setConfig({ ...config, OPENAI_API_KEY: e.target.value })}
                                    placeholder="sk-..."
                                />
                                <span className={styles.hint}>密钥将被加密存储在本地 .env 文件中</span>
                            </div>
                        </section>

                        <section className={styles.section}>
                            <h2 className={styles.sectionTitle}>
                                <ShieldCheck size={22} color="#f59e0b" />
                                系统限制
                            </h2>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>Agent 记忆轮数 (AGENT_MEMORY_LIMIT)</label>
                                <input
                                    className={styles.input}
                                    type="number"
                                    value={config.AGENT_MEMORY_LIMIT}
                                    onChange={e => setConfig({ ...config, AGENT_MEMORY_LIMIT: e.target.value })}
                                />
                            </div>
                            <div className={styles.formGroup}>
                                <label className={styles.label}>文件上传限制 (字节)</label>
                                <input
                                    className={styles.input}
                                    type="number"
                                    value={config.UPLOAD_SIZE_LIMIT}
                                    onChange={e => setConfig({ ...config, UPLOAD_SIZE_LIMIT: e.target.value })}
                                />
                            </div>
                        </section>

                        <div className={styles.footer}>
                            <button 
                                className={styles.saveButton} 
                                onClick={handleSave}
                                disabled={saving}
                            >
                                <Save size={18} />
                                {saving ? '正在保存...' : '保存更改'}
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </main>
    );
}

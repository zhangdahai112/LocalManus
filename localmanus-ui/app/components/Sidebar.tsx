'use client';
import {
    Folder,
    Clock,
    Library,
    Home,
    Settings,
    LayoutGrid,
    ChevronRight,
    Circle,
    Plus
} from 'lucide-react';
import styles from './sidebar.module.css';
import { useRouter, usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { getApiBaseUrl } from '../utils/api';

interface SidebarProps {
    onNewChat?: () => void;
}

interface Project {
    id: number;
    name: string;
    color: string;
}

export default function Sidebar({ onNewChat }: SidebarProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [projects, setProjects] = useState<Project[]>([]);
    
    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const token = localStorage.getItem('access_token');
            if (!token) return;
            
            const baseUrl = getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/projects`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const data = await response.json();
                setProjects(data.slice(0, 5)); // Show only first 5
            }
        } catch (error) {
            console.error('Error fetching projects:', error);
        }
    };
    
    const recentActivities = [
        { name: '商业计划书.docx', status: 'completed' },
        { name: '分析报告.pdf', status: 'processing' },
        { name: '咖啡店设计.pptx', status: 'completed' },
    ];

    return (
        <aside className={styles.sidebar}>
            <div className={styles.top}>
                <div className={styles.logo}>
                    <div className={styles.logoIcon}>LM</div>
                    <span className={styles.logoText}>LocalManus</span>
                </div>

                <nav className={styles.nav}>
                    <div 
                        className={`${styles.navItem} ${pathname === '/' ? styles.active : ''}`}
                        onClick={() => router.push('/')}
                    >
                        <Home size={18} />
                        <span>主页</span>
                    </div>
                    <div 
                        className={`${styles.navItem} ${pathname === '/skills' ? styles.active : ''}`}
                        onClick={() => router.push('/skills')}
                    >
                        <LayoutGrid size={18} />
                        <span>技能库</span>
                    </div>
                    <div 
                        className={`${styles.navItem} ${pathname === '/settings' ? styles.active : ''}`}
                        onClick={() => router.push('/settings')}
                    >
                        <Settings size={18} />
                        <span>设置</span>
                    </div>
                </nav>

                <button className={styles.newChatBtn} onClick={onNewChat}>
                    <Plus size={18} />
                    <span>新会话</span>
                </button>
            </div>

            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <Folder size={14} />
                    <span>我的项目</span>
                </div>
                {projects.length === 0 ? (
                    <div className={styles.projectItem} onClick={() => router.push('/projects')}>
                        <ChevronRight size={14} />
                        <span>查看全部项目</span>
                    </div>
                ) : (
                    <>
                        {projects.map((project) => (
                            <div key={project.id} className={styles.projectItem}>
                                <Circle size={8} fill={project.color} color="transparent" />
                                <span>{project.name}</span>
                            </div>
                        ))}
                        <div className={styles.projectItem} onClick={() => router.push('/projects')} style={{ marginTop: '8px', color: 'var(--accent)' }}>
                            <ChevronRight size={14} />
                            <span>查看全部</span>
                        </div>
                    </>
                )}
            </div>

            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <Clock size={14} />
                    <span>最近活动</span>
                </div>
                <div className={styles.activityList}>
                    {recentActivities.map((activity, i) => (
                        <div key={i} className={styles.activityItem}>
                            <Circle
                                size={8}
                                fill={activity.status === 'completed' ? '#10b981' : '#3b82f6'}
                                color="transparent"
                            />
                            <span className={styles.activityName}>{activity.name}</span>
                        </div>
                    ))}
                </div>
            </div>

            <div className={styles.section}>
                <div className={styles.sectionHeader}>
                    <Library size={14} />
                    <span>资源库</span>
                </div>
            </div>

            <div className={styles.footer}>
                <div className={styles.userProfile}>
                    <div className={styles.avatar}>U</div>
                    <div className={styles.userInfo}>
                        <div className={styles.userName}>User Name</div>
                        <div className={styles.userRole}>Pro Plan</div>
                    </div>
                </div>
            </div>
        </aside>
    );
}

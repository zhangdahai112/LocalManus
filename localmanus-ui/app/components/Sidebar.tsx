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
    Plus,
    ChevronLeft,
    ChevronRight as ChevronRightIcon,
    LogIn,
    LogOut
} from 'lucide-react';
import styles from './sidebar.module.css';
import { useRouter, usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { getApiBaseUrl } from '../utils/api';

interface SidebarProps {
    onNewChat?: () => void;
    isChatMode?: boolean;
}

interface Project {
    id: number;
    name: string;
    color: string;
}

interface User {
    id: number;
    username: string;
    email: string;
    full_name: string;
}

export default function Sidebar({ onNewChat, isChatMode = false }: SidebarProps) {
    const router = useRouter();
    const pathname = usePathname();
    const [projects, setProjects] = useState<Project[]>([]);
    const [isCollapsed, setIsCollapsed] = useState(false);
    
    // User auth state
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [currentUser, setCurrentUser] = useState<User | null>(null);
    const [showLoginModal, setShowLoginModal] = useState(false);
    const [loginForm, setLoginForm] = useState({ username: '', password: '' });
    const [isRegisterMode, setIsRegisterMode] = useState(false);
    const [registerForm, setRegisterForm] = useState({ 
        username: '', 
        email: '', 
        full_name: '', 
        password: '', 
        confirm_password: '' 
    });
    const [error, setError] = useState('');
    
    // Auto-collapse when entering chat mode
    useEffect(() => {
        if (isChatMode) {
            setIsCollapsed(true);
        }
    }, [isChatMode]);
    
    // Check login status on mount
    useEffect(() => {
        const token = localStorage.getItem('access_token');
        if (token) {
            fetchCurrentUser(token);
        }
    }, []);
    
    useEffect(() => {
        if (isLoggedIn) {
            fetchProjects();
        }
    }, [isLoggedIn]);

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

    const fetchCurrentUser = async (token: string) => {
        try {
            const baseUrl = getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/me`, {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            if (response.ok) {
                const user = await response.json();
                setCurrentUser(user);
                setIsLoggedIn(true);
            } else {
                localStorage.removeItem('access_token');
            }
        } catch (err) {
            console.error('Failed to fetch user:', err);
            localStorage.removeItem('access_token');
        }
    };

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        
        try {
            const formData = new FormData();
            formData.append('username', loginForm.username);
            formData.append('password', loginForm.password);
            
            const baseUrl = getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/login`, {
                method: 'POST',
                body: formData
            });
            
            if (response.ok) {
                const data = await response.json();
                localStorage.setItem('access_token', data.access_token);
                await fetchCurrentUser(data.access_token);
                setShowLoginModal(false);
                setLoginForm({ username: '', password: '' });
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Login failed');
            }
        } catch (err) {
            setError('Network error');
        }
    };

    const handleRegister = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        
        if (registerForm.password !== registerForm.confirm_password) {
            setError('Passwords do not match');
            return;
        }
        
        try {
            const baseUrl = getApiBaseUrl();
            const response = await fetch(`${baseUrl}/api/register`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: registerForm.username,
                    email: registerForm.email,
                    full_name: registerForm.full_name,
                    password: registerForm.password
                })
            });
            
            if (response.ok) {
                // Auto-login after registration
                setLoginForm({ 
                    username: registerForm.username, 
                    password: registerForm.password 
                });
                setIsRegisterMode(false);
                // Trigger login
                const loginEvent = new Event('submit') as unknown as React.FormEvent;
                Object.defineProperty(loginEvent, 'preventDefault', { value: () => {} });
                await handleLogin(loginEvent);
            } else {
                const errorData = await response.json();
                setError(errorData.detail || 'Registration failed');
            }
        } catch (err) {
            setError('Network error');
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('access_token');
        setIsLoggedIn(false);
        setCurrentUser(null);
        setProjects([]);
    };
    
    const recentActivities = [
        { name: '商业计划书.docx', status: 'completed' },
        { name: '分析报告.pdf', status: 'processing' },
        { name: '咖啡店设计.pptx', status: 'completed' },
    ];

    return (
        <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ''}`}>
            <button 
                className={styles.collapseBtn}
                onClick={() => setIsCollapsed(!isCollapsed)}
                title={isCollapsed ? "展开侧边栏" : "收起侧边栏"}
            >
                {isCollapsed ? <ChevronRightIcon size={16} /> : <ChevronLeft size={16} />}
            </button>
            <div className={styles.top}>
                <div className={styles.logo}>
                    <div className={styles.logoIcon}>LM</div>
                    <span className={styles.logoText}>LocalManus</span>
                </div>

                <nav className={styles.nav}>
                    <div 
                        className={`${styles.navItem} ${pathname === '/' ? styles.active : ''}`}
                        onClick={() => router.push('/')}
                        title="主页"
                    >
                        <Home size={18} />
                        <span className={styles.navText}>主页</span>
                    </div>
                    <div 
                        className={`${styles.navItem} ${pathname === '/skills' ? styles.active : ''}`}
                        onClick={() => router.push('/skills')}
                        title="技能库"
                    >
                        <LayoutGrid size={18} />
                        <span className={styles.navText}>技能库</span>
                    </div>
                    <div 
                        className={`${styles.navItem} ${pathname === '/settings' ? styles.active : ''}`}
                        onClick={() => router.push('/settings')}
                        title="设置"
                    >
                        <Settings size={18} />
                        <span className={styles.navText}>设置</span>
                    </div>
                </nav>

                <button className={styles.newChatBtn} onClick={onNewChat} title="新会话">
                    <Plus size={18} />
                    <span className={styles.navText}>新会话</span>
                </button>
            </div>

            {!isCollapsed && (
                <>
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
                </>
            )}

            <div className={styles.footer}>
                {isLoggedIn && currentUser ? (
                    <div className={styles.userProfile} title={currentUser.full_name || currentUser.username}>
                        <div className={styles.avatar}>
                            {(currentUser.full_name?.charAt(0) || currentUser.username.charAt(0)).toUpperCase()}
                        </div>
                        {!isCollapsed && (
                            <div className={styles.userInfo}>
                                <div className={styles.userName}>{currentUser.full_name || currentUser.username}</div>
                                <div className={styles.userRoleRow}>
                                    <span className={styles.userRole}>Pro Plan</span>
                                    <button className={styles.logoutBtn} onClick={handleLogout} title="退出登录">
                                        <LogOut size={12} />
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                ) : (
                    <div 
                        className={styles.userProfile} 
                        onClick={() => setShowLoginModal(true)}
                        title="点击登录"
                    >
                        <div className={styles.avatar}>
                            <LogIn size={16} />
                        </div>
                        {!isCollapsed && (
                            <div className={styles.userInfo}>
                                <div className={styles.userName}>未登录</div>
                                <div className={styles.userRole}>点击登录</div>
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Login/Register Modal */}
            {showLoginModal && (
                <div className={styles.modalOverlay} onClick={() => setShowLoginModal(false)}>
                    <div className={styles.modal} onClick={e => e.stopPropagation()}>
                        <div className={styles.modalHeader}>
                            <h2>{isRegisterMode ? '注册账户' : '登录账户'}</h2>
                            <button 
                                className={styles.closeButton} 
                                onClick={() => setShowLoginModal(false)}
                            >
                                ×
                            </button>
                        </div>
                        
                        {error && <div className={styles.errorMessage}>{error}</div>}
                        
                        <form onSubmit={isRegisterMode ? handleRegister : handleLogin}>
                            {isRegisterMode ? (
                                <>
                                    <div className={styles.formGroup}>
                                        <label>用户名</label>
                                        <input
                                            type="text"
                                            value={registerForm.username}
                                            onChange={(e) => setRegisterForm({...registerForm, username: e.target.value})}
                                            required
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>邮箱</label>
                                        <input
                                            type="email"
                                            value={registerForm.email}
                                            onChange={(e) => setRegisterForm({...registerForm, email: e.target.value})}
                                            required
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>姓名</label>
                                        <input
                                            type="text"
                                            value={registerForm.full_name}
                                            onChange={(e) => setRegisterForm({...registerForm, full_name: e.target.value})}
                                            required
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>密码</label>
                                        <input
                                            type="password"
                                            value={registerForm.password}
                                            onChange={(e) => setRegisterForm({...registerForm, password: e.target.value})}
                                            required
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>确认密码</label>
                                        <input
                                            type="password"
                                            value={registerForm.confirm_password}
                                            onChange={(e) => setRegisterForm({...registerForm, confirm_password: e.target.value})}
                                            required
                                        />
                                    </div>
                                </>
                            ) : (
                                <>
                                    <div className={styles.formGroup}>
                                        <label>用户名</label>
                                        <input
                                            type="text"
                                            value={loginForm.username}
                                            onChange={(e) => setLoginForm({...loginForm, username: e.target.value})}
                                            required
                                        />
                                    </div>
                                    <div className={styles.formGroup}>
                                        <label>密码</label>
                                        <input
                                            type="password"
                                            value={loginForm.password}
                                            onChange={(e) => setLoginForm({...loginForm, password: e.target.value})}
                                            required
                                        />
                                    </div>
                                </>
                            )}
                            
                            <button type="submit" className={styles.submitButton}>
                                {isRegisterMode ? '注册' : '登录'}
                            </button>
                        </form>
                        
                        <div className={styles.switchMode}>
                            {isRegisterMode 
                                ? '已有账户？' 
                                : '没有账户？'}
                            <button 
                                className={styles.switchButton}
                                onClick={() => {
                                    setIsRegisterMode(!isRegisterMode);
                                    setError('');
                                }}
                            >
                                {isRegisterMode ? '立即登录' : '立即注册'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </aside>
    );
}

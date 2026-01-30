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

interface SidebarProps {
    onNewChat?: () => void;
}

export default function Sidebar({ onNewChat }: SidebarProps) {
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
                    <div className={`${styles.navItem} ${styles.active}`}>
                        <Home size={18} />
                        <span>主页</span>
                    </div>
                    <div className={styles.navItem}>
                        <LayoutGrid size={18} />
                        <span>技能库</span>
                    </div>
                    <div className={styles.navItem}>
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
                <div className={styles.projectItem}>
                    <ChevronRight size={14} />
                    <span>默认项目</span>
                </div>
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

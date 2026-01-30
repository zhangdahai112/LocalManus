import Sidebar from './components/Sidebar';
import Omnibox from './components/Omnibox';
import Toolbox from './components/Toolbox';
import { Plus, Download } from 'lucide-react';
import styles from './page.module.css';

export default function Home() {
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
    <main className={styles.main}>
      <Sidebar />

      <div className={styles.content}>
        <div className={styles.container}>
          <header className={styles.header}>
            <h1 className={styles.title}>今天可以帮你做什么？</h1>
          </header>

          <Omnibox />
          <Toolbox />

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

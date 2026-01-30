import {
    Presentation,
    PenTool,
    Palette,
    FileText,
    Layout,
    Languages,
    PlayCircle,
    Mic,
    Search,
    Code
} from 'lucide-react';
import styles from './toolbox.module.css';

export default function Toolbox({ isHidden }: { isHidden?: boolean }) {
    const tools = [
        { icon: <Presentation size={16} />, name: '生成幻灯片' },
        { icon: <PenTool size={16} />, name: '撰写文档' },
        { icon: <Palette size={16} />, name: '生成设计' },
        { icon: <Layout size={16} />, name: '创建故事绘本' },
        { icon: <Search size={16} />, name: '批量调研' },
        { icon: <FileText size={16} />, name: '分析数据' },
        { icon: <Layout size={16} />, name: '创建网页' },
        { icon: <Languages size={16} />, name: '翻译 PDF' },
        { icon: <PlayCircle size={16} />, name: '总结视频' },
        { icon: <Languages size={16} />, name: '转写音频' },
    ];

    return (
        <div className={`${styles.container} ${isHidden ? styles.hidden : ''}`}>
            <div className={styles.tagWrapper}>
                {tools.map((tool, i) => (
                    <button key={i} className={styles.tag}>
                        {tool.icon}
                        <span>{tool.name}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}

import { Plus, Mic, Share2, ArrowUp, Zap } from 'lucide-react';
import styles from './omnibox.module.css';

export default function Omnibox() {
    return (
        <div className={styles.container}>
            <div className={styles.box}>
                <div className={styles.topRow}>
                    <input
                        type="text"
                        placeholder="用 LocalManus 创造无限可能"
                        className={styles.input}
                    />
                    <div className={styles.tabTag}>tab</div>
                </div>

                <div className={styles.bottomRow}>
                    <div className={styles.leftActions}>
                        <button className={styles.iconButton} title="上传">
                            <Plus size={20} />
                        </button>
                        <button className={styles.iconButton} title="分享">
                            <Share2 size={18} />
                        </button>
                    </div>

                    <div className={styles.rightActions}>
                        <button className={styles.iconButton} title="语音输入">
                            <Mic size={20} />
                        </button>
                        <button className={styles.submitButton}>
                            <ArrowUp size={20} color="white" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

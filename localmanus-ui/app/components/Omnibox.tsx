import React from 'react';
import { Plus, Mic, Share2, ArrowUp, Zap } from 'lucide-react';
import styles from './omnibox.module.css';

interface OmniboxProps {
    onOpenChat?: (text: string) => void;
    disabled?: boolean;
}

export default function Omnibox({ onOpenChat, disabled }: OmniboxProps) {
    const [inputValue, setInputValue] = React.useState('');

    const handleSubmit = () => {
        if (inputValue.trim() && onOpenChat && !disabled) {
            onOpenChat(inputValue);
            setInputValue('');
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    };

    return (
        <div className={styles.container}>
            <div className={styles.box}>
                <div className={styles.topRow}>
                    <input
                        type="text"
                        placeholder="用 LocalManus 创造无限可能"
                        className={styles.input}
                        value={inputValue}
                        onChange={(e) => setInputValue(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={disabled}
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
                        <button 
                            className={`${styles.submitButton} ${disabled ? styles.disabled : ''}`} 
                            onClick={handleSubmit}
                            disabled={disabled}
                        >
                            <ArrowUp size={20} color="white" />
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

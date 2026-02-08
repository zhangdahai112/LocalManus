import React from 'react';
import { Plus, Mic, Share2, ArrowUp, Zap, Paperclip, X } from 'lucide-react';
import styles from './omnibox.module.css';

interface OmniboxProps {
    onOpenChat?: (text: string, filePaths?: string[]) => void;
    disabled?: boolean;
    uploadedFiles?: UploadedFileInfo[];
    onUploadedFilesChange?: (files: UploadedFileInfo[]) => void;
}

interface UploadedFileInfo {
    id: number;
    filename: string;
    original_filename: string;
    file_path: string;
}

export default function Omnibox({ onOpenChat, disabled, uploadedFiles: externalUploadedFiles, onUploadedFilesChange }: OmniboxProps) {
    const [inputValue, setInputValue] = React.useState('');
    const [isUploading, setIsUploading] = React.useState(false);
    const fileInputRef = React.useRef<HTMLInputElement>(null);
    
    // Use external state if provided, otherwise use internal state
    const uploadedFiles = externalUploadedFiles ?? [];
    const setUploadedFiles = onUploadedFilesChange ?? (() => {});

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        if (!e.target.files || e.target.files.length === 0) return;

        const token = localStorage.getItem('access_token');
        if (!token) {
            alert('请先登录后再上传文件');
            return;
        }

        setIsUploading(true);
        const newFiles = Array.from(e.target.files);

        try {
            for (const file of newFiles) {
                const formData = new FormData();
                formData.append('file', file);

                const response = await fetch('http://localhost:8000/api/upload', {
                    method: 'POST',
                    headers: {
                        'Authorization': `Bearer ${token}`,
                    },
                    body: formData,
                });

                if (response.ok) {
                    const data: UploadedFileInfo = await response.json();
                    console.log('File upload response:', data);
                    console.log('Current uploadedFiles before update:', uploadedFiles);
                    const newFiles = [...uploadedFiles, data];
                    console.log('New uploadedFiles after update:', newFiles);
                    setUploadedFiles(newFiles);
                } else {
                    const error = await response.text();
                    alert(`文件上传失败: ${file.name} - ${error}`);
                }
            }
        } catch (error) {
            console.error('File upload error:', error);
            alert('文件上传失败，请重试');
        } finally {
            setIsUploading(false);
            // Reset file input
            if (fileInputRef.current) {
                fileInputRef.current.value = '';
            }
        }
    };

    const handleRemoveFile = (index: number) => {
        setUploadedFiles(uploadedFiles.filter((_, i) => i !== index));
    };

    const handleSubmit = () => {
        console.log('=== handleSubmit called ===');
        console.log('inputValue:', inputValue);
        console.log('uploadedFiles.length:', uploadedFiles.length);
        console.log('uploadedFiles:', uploadedFiles);
        
        if ((inputValue.trim() || uploadedFiles.length > 0) && onOpenChat && !disabled) {
            const filePaths = uploadedFiles.map(f => {
                console.log('Processing file:', f);
                console.log('file.file_path:', f.file_path);
                return f.file_path;
            });
            
            console.log('Omnibox handleSubmit - uploadedFiles:', uploadedFiles);
            console.log('Omnibox handleSubmit - filePaths:', filePaths);
            
            onOpenChat(inputValue, filePaths.length > 0 ? filePaths : undefined);
            setInputValue('');
            // Files will be cleared by parent component after successful send
        } else {
            console.log('Submit blocked - conditions not met');
            console.log('  inputValue.trim():', inputValue.trim());
            console.log('  uploadedFiles.length:', uploadedFiles.length);
            console.log('  onOpenChat:', !!onOpenChat);
            console.log('  disabled:', disabled);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const formatFileSize = (bytes: number): string => {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    };

    return (
        <div className={styles.container}>
            <div className={styles.box}>
                {uploadedFiles.length > 0 && (
                    <div className={styles.fileList}>
                        {uploadedFiles.map((file, index) => (
                            <div key={file.id} className={styles.fileItem}>
                                <Paperclip size={14} />
                                <span className={styles.fileName}>{file.original_filename}</span>
                                <button
                                    className={styles.removeFile}
                                    onClick={() => handleRemoveFile(index)}
                                    title="移除文件"
                                >
                                    <X size={14} />
                                </button>
                            </div>
                        ))}
                    </div>
                )}
                {isUploading && (
                    <div className={styles.uploadingIndicator}>
                        <span>正在上传...</span>
                    </div>
                )}
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
                        <input
                            ref={fileInputRef}
                            type="file"
                            multiple
                            onChange={handleFileSelect}
                            style={{ display: 'none' }}
                        />
                        <button 
                            className={styles.iconButton} 
                            title="上传文件"
                            onClick={() => fileInputRef.current?.click()}
                        >
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

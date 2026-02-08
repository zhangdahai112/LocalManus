'use client';

import React, { useState, useEffect } from 'react';
import { Plus, Edit2, Trash2, Folder } from 'lucide-react';
import * as Icons from 'lucide-react';
import Sidebar from '../components/Sidebar';
import UserStatus from '../components/UserStatus';
import { getApiBaseUrl } from '../utils/api';
import styles from './projects.module.css';

interface Project {
  id: number;
  user_id: number;
  name: string;
  description: string;
  color: string;
  icon: string;
  created_at: string;
  updated_at: string;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    color: '#3b82f6',
    icon: 'Folder'
  });

  const colors = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#14b8a6', '#f97316'];

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    const token = localStorage.getItem('access_token');
    const baseUrl = getApiBaseUrl();
    const response = await fetch(`${baseUrl}/api/projects`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    if (response.ok) {
      const data = await response.json();
      setProjects(data);
    }
  };

  const handleCreate = () => {
    setEditingProject(null);
    setFormData({ name: '', description: '', color: '#3b82f6', icon: 'Folder' });
    setShowModal(true);
  };

  const handleEdit = (project: Project, e: React.MouseEvent) => {
    e.stopPropagation();
    setEditingProject(project);
    setFormData({
      name: project.name,
      description: project.description || '',
      color: project.color,
      icon: project.icon
    });
    setShowModal(true);
  };

  const handleDelete = async (id: number, e?: React.MouseEvent) => {
    e?.stopPropagation();
    if (!confirm('确定要删除这个项目吗？')) return;
    
    const token = localStorage.getItem('access_token');
    const baseUrl = getApiBaseUrl();
    const response = await fetch(`${baseUrl}/api/projects/${id}`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    if (response.ok) {
      fetchProjects();
    }
  };

  const handleSubmit = async () => {
    const token = localStorage.getItem('access_token');
    const baseUrl = getApiBaseUrl();
    const url = editingProject 
      ? `${baseUrl}/api/projects/${editingProject.id}`
      : `${baseUrl}/api/projects`;
    const method = editingProject ? 'PUT' : 'POST';

    const response = await fetch(url, {
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(formData)
    });

    if (response.ok) {
      fetchProjects();
      setShowModal(false);
    }
  };

  const getIconComponent = (iconName: string) => {
    const IconComponent = (Icons as any)[iconName];
    return IconComponent ? <IconComponent size={24} /> : <Folder size={24} />;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
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
            <h1 className={styles.title}>我的项目</h1>
            <p className={styles.subtitle}>组织和管理您的工作项目</p>
          </div>
          <button className={styles.createButton} onClick={handleCreate}>
            <Plus size={20} />
            新建项目
          </button>
        </header>

        {loading ? (
          <div className={styles.loading}>正在加载项目...</div>
        ) : projects.length === 0 ? (
          <div className={styles.empty}>
            <div className={styles.emptyIcon}>📁</div>
            <div className={styles.emptyText}>还没有项目，点击上方按钮创建第一个项目</div>
          </div>
        ) : (
          <div className={styles.projectsGrid}>
            {projects.map((project) => (
              <div key={project.id} className={styles.projectCard}>
                <div 
                  className={styles.projectIcon}
                  style={{ backgroundColor: `${project.color}20`, color: project.color }}
                >
                  {getIconComponent(project.icon)}
                </div>
                <h3 className={styles.projectName}>{project.name}</h3>
                <p className={styles.projectDescription}>{project.description || '暂无描述'}</p>
                
                <div className={styles.projectFooter}>
                  <span className={styles.projectDate}>
                    {formatDate(project.updated_at)}
                  </span>
                  <div className={styles.projectActions}>
                    <button 
                      className={styles.actionButton}
                      onClick={(e) => handleEdit(project, e)}
                      title="编辑项目"
                    >
                      <Edit2 size={16} />
                    </button>
                    <button 
                      className={`${styles.actionButton} ${styles.deleteButton}`}
                      onClick={(e) => handleDelete(project.id, e)}
                      title="删除项目"
                    >
                      <Trash2 size={16} />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {showModal && (
          <div className={styles.modal} onClick={() => setShowModal(false)}>
            <div className={styles.modalContent} onClick={(e) => e.stopPropagation()}>
              <h2 className={styles.modalHeader}>
                {editingProject ? '编辑项目' : '新建项目'}
              </h2>

              <div className={styles.formGroup}>
                <label className={styles.label}>项目名称</label>
                <input
                  className={styles.input}
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  placeholder="输入项目名称"
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>项目描述</label>
                <textarea
                  className={styles.textarea}
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  placeholder="简要描述项目内容"
                />
              </div>

              <div className={styles.formGroup}>
                <label className={styles.label}>主题颜色</label>
                <div className={styles.colorPicker}>
                  {colors.map((color) => (
                    <div
                      key={color}
                      className={`${styles.colorOption} ${formData.color === color ? styles.selected : ''}`}
                      style={{ backgroundColor: color }}
                      onClick={() => setFormData({ ...formData, color })}
                    />
                  ))}
                </div>
              </div>

              <div className={styles.modalFooter}>
                <button className={styles.cancelButton} onClick={() => setShowModal(false)}>
                  取消
                </button>
                <button 
                  className={styles.submitButton} 
                  onClick={handleSubmit}
                  disabled={!formData.name.trim()}
                >
                  {editingProject ? '保存' : '创建'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </main>
  );
}

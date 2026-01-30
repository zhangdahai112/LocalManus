import React, { useState, useEffect } from 'react';
import { Users, Calendar, Bell, Plus, Share2, LogIn, User } from 'lucide-react';
import styles from './userStatus.module.css';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
}

export default function UserStatus() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [registerForm, setRegisterForm] = useState({ 
    username: '', 
    email: '', 
    full_name: '', 
    password: '', 
    confirm_password: '' 
  });
  const [isRegisterMode, setIsRegisterMode] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    // Check if user is already logged in
    const token = localStorage.getItem('access_token');
    if (token) {
      fetchCurrentUser(token);
    }
  }, []);

  const fetchCurrentUser = async (token: string) => {
    try {
      const response = await fetch('http://localhost:8000/api/me', {
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
      
      const response = await fetch('http://localhost:8000/api/login', {
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
      const response = await fetch('http://localhost:8000/api/register', {
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
  };

  if (isLoggedIn && currentUser) {
    return (
      <div className={styles.container}>
        <div className={styles.actionGroup}>
          <button className={styles.iconButton}>
            <Share2 size={18} />
            <span>分享</span>
          </button>
          <button className={styles.iconButton}>
            <Calendar size={18} />
          </button>
          <button className={styles.iconButton}>
            <Bell size={18} />
          </button>
        </div>
        
        <div className={styles.tokenBadge}>
          <Plus size={14} color="#666" />
          <span className={styles.tokenValue}>500</span>
        </div>

        <div className={styles.userMenu}>
          <div className={styles.avatar}>
            <span>{currentUser.full_name?.charAt(0) || currentUser.username.charAt(0)}</span>
          </div>
          <div className={styles.userInfo}>
            <div className={styles.userName}>{currentUser.full_name || currentUser.username}</div>
            <div className={styles.userEmail}>{currentUser.email}</div>
          </div>
          <button className={styles.logoutButton} onClick={handleLogout}>
            Logout
          </button>
        </div>
      </div>
    );
  }

  return (
    <>
      <div className={styles.container}>
        <div className={styles.actionGroup}>
          <button className={styles.iconButton}>
            <Share2 size={18} />
            <span>分享</span>
          </button>
          <button className={styles.iconButton}>
            <Calendar size={18} />
          </button>
          <button className={styles.iconButton}>
            <Bell size={18} />
          </button>
        </div>
        
        <div className={styles.tokenBadge}>
          <Plus size={14} color="#666" />
          <span className={styles.tokenValue}>500</span>
        </div>

        <button 
          className={styles.loginButton} 
          onClick={() => setShowLoginModal(true)}
        >
          <LogIn size={18} />
          登录
        </button>
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
    </>
  );
}
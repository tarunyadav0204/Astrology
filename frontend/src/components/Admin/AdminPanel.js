import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminService } from '../../services/adminService';
import AdminChatHistory from './AdminChatHistory';
import AdminCreditLedger from './AdminCreditLedger';
import AdminDailyActivity from './AdminDailyActivity';
import AdminCreditsDashboard from './AdminCreditsDashboard';
import AdminGooglePlayRefund from './AdminGooglePlayRefund';
import ChatFeedback from './ChatFeedback';
import ChatErrors from './ChatErrors';
import AdminChatAnalysis from './AdminChatAnalysis';
import AdminTerms from './AdminTerms';
import BlogDashboard from '../Blog/BlogDashboard';
import NavigationHeader from '../Shared/NavigationHeader';
import './AdminPanel.css';

const AdminPanel = ({ user, onLogout, onAdminClick, onLogin, showLoginButton, onHomeClick }) => {
  const navigate = useNavigate();
  
  const handleHomeClick = () => {
    if (onHomeClick) {
      onHomeClick();
    } else {
      navigate('/');
    }
  };
  const [activeTab, setActiveTab] = useState('users');
  const [activeSubTab, setActiveSubTab] = useState('management');
  const [users, setUsers] = useState([]);
  const [userFacts, setUserFacts] = useState([]);
  const [factsSearch, setFactsSearch] = useState('');
  const [factsPage, setFactsPage] = useState(1);
  const [factsTotalPages, setFactsTotalPages] = useState(1);
  const [factsLoading, setFactsLoading] = useState(false);
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [editingSubscription, setEditingSubscription] = useState(null);
  const [pendingSubscription, setPendingSubscription] = useState(null);
  const [promoCodes, setPromoCodes] = useState([]);
  const [creditStats, setCreditStats] = useState({});
  const [newPromoCode, setNewPromoCode] = useState({ code: '', credits: 100, max_uses: 1, max_uses_per_user: 1 });
  const [creditSettings, setCreditSettings] = useState([]);
  const [editingPromoCode, setEditingPromoCode] = useState(null);
  const [editFormData, setEditFormData] = useState({});
  const [deleteConfirmation, setDeleteConfirmation] = useState(null);
  const [creditRequests, setCreditRequests] = useState([]);
  const [statusFilter, setStatusFilter] = useState('all');
  const [approvingRequest, setApprovingRequest] = useState(null);
  const [approvalData, setApprovalData] = useState({ amount: 0, notes: '' });
  const [showApprovalModal, setShowApprovalModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [adminSettings, setAdminSettings] = useState([]);
  const [debugLogging, setDebugLogging] = useState(false);
  const [androidMinVersion, setAndroidMinVersion] = useState('');
  const [iosMinVersion, setIosMinVersion] = useState('');
  const [notifUserId, setNotifUserId] = useState('');
  const [notifTitle, setNotifTitle] = useState('');
  const [notifBody, setNotifBody] = useState('');
  const [notifQuestion, setNotifQuestion] = useState('');
  const [notifNativeId, setNotifNativeId] = useState('');
  const [notifSending, setNotifSending] = useState(false);
  const [notifResult, setNotifResult] = useState(null);

  useEffect(() => {
    if (activeTab === 'users') {
      if (activeSubTab === 'management') {
        fetchUsers();
        fetchSubscriptionPlans();
      } else if (activeSubTab === 'facts') {
        fetchUserFacts();
      }
    } else if (activeTab === 'charts' || activeTab === 'notifications') {
      fetchCharts();
    } else if (activeTab === 'credits') {
      if (activeSubTab === 'management') {
        fetchPromoCodes();
        fetchCreditStats();
        fetchCreditSettings();
      } else if (activeSubTab === 'requests') {
        fetchCreditRequests();
      }
    } else if (activeTab === 'chat') {
      // Chat history will be loaded by AdminChatHistory component
    } else if (activeTab === 'ledger') {
      // Credit ledger will be loaded by AdminCreditLedger component
    } else if (activeTab === 'settings') {
      fetchAdminSettings();
    } else if (activeTab === 'notifications') {
      fetchUsers();
    }
  }, [activeTab, activeSubTab]);

  const fetchAdminSettings = async () => {
    try {
      const response = await fetch('/api/admin/settings', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setAdminSettings(data.settings || []);
      const debugSetting = data.settings.find(s => s.key === 'debug_logging_enabled');
      setDebugLogging(debugSetting?.value === 'true');
      const androidMin = data.settings.find(s => s.key === 'min_android_version_code');
      const iosMin = data.settings.find(s => s.key === 'min_ios_build_number');
      setAndroidMinVersion(androidMin?.value ?? '');
      setIosMinVersion(iosMin?.value ?? '');
    } catch (error) {
      console.error('Error fetching admin settings:', error);
    }
  };

  const handleToggleDebugLogging = async () => {
    const newValue = !debugLogging;
    try {
      const response = await fetch('/api/admin/settings/debug_logging_enabled', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          key: 'debug_logging_enabled',
          value: newValue ? 'true' : 'false',
          description: 'Enable complete Gemini request/response logging'
        })
      });
      if (response.ok) {
        setDebugLogging(newValue);
        alert(`Debug logging ${newValue ? 'enabled' : 'disabled'}`);
      }
    } catch (error) {
      console.error('Error updating debug logging:', error);
    }
  };

  const handleSaveAppVersionConfig = async () => {
    const token = localStorage.getItem('token');
    const androidValue = androidMinVersion?.toString().trim();
    const iosValue = iosMinVersion?.toString().trim();

    const payloads = [];
    if (androidValue !== '') {
      payloads.push({
        key: 'min_android_version_code',
        value: androidValue,
        description: 'Minimum required Android versionCode for mobile app',
      });
    }
    if (iosValue !== '') {
      payloads.push({
        key: 'min_ios_build_number',
        value: iosValue,
        description: 'Minimum required iOS build number for mobile app',
      });
    }

    try {
      await Promise.all(
        payloads.map((p) =>
          fetch(`/api/admin/settings/${p.key}`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`,
            },
            body: JSON.stringify(p),
          })
        )
      );
      alert('App version config saved. Users below these versions will be forced to update.');
    } catch (error) {
      console.error('Error saving app version config:', error);
      alert('Failed to save app version config.');
    }
  };

  const fetchSubscriptionPlans = async () => {
    try {
      const data = await adminService.getSubscriptionPlans();
      setSubscriptionPlans(data.plans || []);
    } catch (error) {
      console.error('Error fetching subscription plans:', error);
    }
  };

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await adminService.getAllUsers();
      setUsers(data.users || []);
    } catch (error) {
      console.error('Error fetching users:', error);
      setUsers([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchUserFacts = async () => {
    setFactsLoading(true);
    try {
      const response = await fetch(`/api/admin/facts?search=${factsSearch}&page=${factsPage}&limit=20`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setUserFacts(data.facts || []);
      setFactsTotalPages(data.total_pages || 1);
    } catch (error) {
      console.error('Error fetching user facts:', error);
      setUserFacts([]);
    } finally {
      setFactsLoading(false);
    }
  };

  const fetchCharts = async () => {
    setLoading(true);
    try {
      const data = await adminService.getAllCharts();
      setCharts(data.charts || []);
    } catch (error) {
      console.error('Error fetching charts:', error);
      setCharts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateUser = async (phone, updates) => {
    try {
      await adminService.updateUser(phone, updates);
      fetchUsers();
      setEditingUser(null);
    } catch (error) {
      console.error('Error updating user:', error);
    }
  };

  const handleUpdateSubscription = async (userId, platform, planName) => {
    try {
      await adminService.updateUserSubscription(userId, {
        platform: platform,
        plan_name: planName
      });
      fetchUsers();
      setEditingSubscription(null);
      setPendingSubscription(null);
    } catch (error) {
      console.error('Error updating subscription:', error);
    }
  };

  const handleSaveSubscription = () => {
    if (pendingSubscription) {
      const { userId, platform, planName } = pendingSubscription;
      handleUpdateSubscription(userId, platform, planName);
    }
  };

  const handleCancelSubscription = () => {
    setEditingSubscription(null);
    setPendingSubscription(null);
  };

  const handleDeleteChart = async (chartId) => {
    if (window.confirm('Are you sure you want to delete this chart?')) {
      try {
        await adminService.deleteChart(chartId);
        fetchCharts();
      } catch (error) {
        console.error('Error deleting chart:', error);
      }
    }
  };

  const fetchPromoCodes = async () => {
    try {
      const response = await fetch('/api/credits/admin/promo-codes', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setPromoCodes(data.promo_codes || []);
    } catch (error) {
      console.error('Error fetching promo codes:', error);
    }
  };

  const fetchCreditStats = async () => {
    try {
      const response = await fetch('/api/credits/admin/stats', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setCreditStats(data);
    } catch (error) {
      console.error('Error fetching credit stats:', error);
    }
  };

  const handleCreatePromoCode = async () => {
    try {
      const response = await fetch('/api/credits/admin/promo-codes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(newPromoCode)
      });
      
      if (response.ok) {
        setNewPromoCode({ code: '', credits: 100, max_uses: 1 });
        fetchPromoCodes();
        fetchCreditStats();
      }
    } catch (error) {
      console.error('Error creating promo code:', error);
    }
  };

  const handleBulkPromoCodes = async () => {
    const prefix = prompt('Enter prefix for bulk codes (e.g., SPECIAL):');
    const count = parseInt(prompt('How many codes to create?', '10'));
    const credits = parseInt(prompt('Credits per code:', '50'));
    
    if (prefix && count && credits) {
      try {
        const response = await fetch('/api/credits/admin/bulk-promo-codes', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          },
          body: JSON.stringify({ prefix, count, credits, max_uses: 1, max_uses_per_user: 1 })
        });
        
        if (response.ok) {
          const data = await response.json();
          alert(`Created ${data.codes.length} promo codes`);
          fetchPromoCodes();
          fetchCreditStats();
        }
      } catch (error) {
        console.error('Error creating bulk promo codes:', error);
      }
    }
  };

  const fetchCreditSettings = async () => {
    try {
      const response = await fetch('/api/credits/admin/settings', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setCreditSettings(data.settings || []);
    } catch (error) {
      console.error('Error fetching credit settings:', error);
    }
  };

  const handleUpdateSettings = async () => {
    try {
      const response = await fetch('/api/credits/admin/settings', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ settings: creditSettings })
      });
      
      if (response.ok) {
        alert('Settings updated successfully');
        fetchCreditSettings();
      }
    } catch (error) {
      console.error('Error updating settings:', error);
    }
  };

  const handleSettingChange = (key, value) => {
    setCreditSettings(prev => 
      prev.map(setting => 
        setting.key === key ? { ...setting, value: parseInt(value) } : setting
      )
    );
  };

  const handleUpdatePromoCode = async (code, updates) => {
    if (!updates.credits || updates.credits < 1 || !updates.max_uses || updates.max_uses < 1) {
      alert('Credits and max uses must be positive numbers');
      return;
    }
    
    try {
      const response = await fetch(`/api/credits/admin/promo-codes/${code}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify(updates)
      });
      
      if (response.ok) {
        fetchPromoCodes();
        fetchCreditStats();
        setEditingPromoCode(null);
        setEditFormData({});
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to update promo code');
      }
    } catch (error) {
      console.error('Error updating promo code:', error);
      alert('Error updating promo code');
    }
  };

  const startEditingPromoCode = (code) => {
    setEditingPromoCode(code.code);
    setEditFormData({
      credits: code.credits,
      max_uses: code.max_uses,
      is_active: code.is_active
    });
  };

  const handleDeletePromoCode = (code) => {
    setDeleteConfirmation(code);
  };

  const confirmDelete = async () => {
    const code = deleteConfirmation;
    setDeleteConfirmation(null);
    
    try {
      const response = await fetch('/api/credits/admin/delete-promo-code', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ code: code })
      });
      
      if (response.ok) {
        fetchPromoCodes();
        fetchCreditStats();
        alert('Promo code deleted successfully');
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to delete promo code');
      }
    } catch (error) {
      console.error('Error deleting promo code:', error);
      alert('Error deleting promo code: ' + error.message);
    }
  };

  const cancelDelete = () => {
    setDeleteConfirmation(null);
  };

  const handleSendNotification = async () => {
    const userId = notifUserId ? parseInt(notifUserId, 10) : 0;
    if (!userId || !notifTitle.trim() || !notifBody.trim()) {
      const msg = 'Please select a user and enter both title and body.';
      setNotifResult({ ok: false, message: msg });
      console.warn('[Admin Notifications] Validation failed:', msg);
      return;
    }
    setNotifSending(true);
    setNotifResult(null);
    console.log('[Admin Notifications] Sending to user_id=', userId, 'title=', notifTitle.trim().slice(0, 50));
    try {
      const response = await fetch('/api/nudge/admin/send', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          user_id: userId,
          title: notifTitle.trim().slice(0, 100),
          body: notifBody.trim().slice(0, 200),
          ...(notifQuestion.trim() && { question: notifQuestion.trim().slice(0, 500) }),
          ...(notifNativeId && { native_id: parseInt(notifNativeId, 10) }),
        }),
      });
      let data;
      try {
        data = await response.json();
      } catch (_) {
        const text = await response.text();
        console.error('[Admin Notifications] Non-JSON response:', response.status, text?.slice(0, 200));
        setNotifResult({ ok: false, message: `Server error ${response.status}: ${text?.slice(0, 100) || 'Invalid response'}` });
        return;
      }
      if (!response.ok) {
        const message = data.detail || data.message || 'Failed to send';
        console.error('[Admin Notifications] Failed:', response.status, data);
        setNotifResult({ ok: false, message: typeof message === 'string' ? message : JSON.stringify(message) });
        return;
      }
      console.log('[Admin Notifications] Success:', data);
      setNotifResult(data);
      if (data.ok) {
        setNotifTitle('');
        setNotifBody('');
        setNotifQuestion('');
        setNotifNativeId('');
      }
    } catch (err) {
      console.error('[Admin Notifications] Request error:', err);
      setNotifResult({ ok: false, message: err.message || 'Request failed' });
    } finally {
      setNotifSending(false);
    }
  };

  const fetchCreditRequests = async () => {
    try {
      const response = await fetch('/api/credits/requests/all', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setCreditRequests(data.requests || []);
    } catch (error) {
      console.error('Error fetching credit requests:', error);
    }
  };

  const handleApproveRequest = async (requestId, amount, notes) => {
    try {
      const response = await fetch('/api/credits/requests/approve', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          request_id: requestId,
          approved_amount: amount,
          admin_notes: notes
        })
      });
      
      if (response.ok) {
        fetchCreditRequests();
        setShowApprovalModal(false);
        setSelectedRequest(null);
        setApprovalData({ amount: 0, notes: '' });
        
        // Trigger credit update event for the user whose credits were approved
        window.dispatchEvent(new CustomEvent('creditUpdated'));
        
        alert('Request approved successfully');
      }
    } catch (error) {
      console.error('Error approving request:', error);
    }
  };

  const openApprovalModal = (request) => {
    setSelectedRequest(request);
    setApprovalData({ amount: request.requested_amount, notes: '' });
    setShowApprovalModal(true);
  };

  const handleRejectRequest = async (requestId, notes) => {
    try {
      const response = await fetch('/api/credits/requests/reject', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          request_id: requestId,
          admin_notes: notes
        })
      });
      
      if (response.ok) {
        fetchCreditRequests();
        alert('Request rejected');
      }
    } catch (error) {
      console.error('Error rejecting request:', error);
    }
  };

  return (
    <div className="admin-panel">
      <NavigationHeader 
        compact={true}
        showZodiacSelector={false}
        user={user}
        onAdminClick={onAdminClick}
        onLogout={onLogout || (() => {
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          handleHomeClick();
        })}
        onLogin={onLogin || (() => handleHomeClick())}
        showLoginButton={showLoginButton}
        onHomeClick={handleHomeClick}
      />
      <div className="admin-content-wrapper">

      <div className="admin-tabs">
        <button 
          className={`tab ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          Users
        </button>
        <button 
          className={`tab ${activeTab === 'charts' ? 'active' : ''}`}
          onClick={() => setActiveTab('charts')}
        >
          Charts
        </button>
        <button 
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          Chat History
        </button>
        <button 
          className={`tab ${activeTab === 'credits' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('credits');
            setActiveSubTab('management');
          }}
        >
          Credits
        </button>
        <button 
          className={`tab ${activeTab === 'analysis' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('analysis');
            setActiveSubTab('feedback');
          }}
        >
          Analysis
        </button>
        <button 
          className={`tab ${activeTab === 'terms' ? 'active' : ''}`}
          onClick={() => setActiveTab('terms')}
        >
          Terms
        </button>
        <button 
          className={`tab ${activeTab === 'errors' ? 'active' : ''}`}
          onClick={() => setActiveTab('errors')}
        >
          Errors
        </button>
        <button 
          className={`tab ${activeTab === 'blog' ? 'active' : ''}`}
          onClick={() => setActiveTab('blog')}
        >
          Blog
        </button>
        <button 
          className={`tab ${activeTab === 'notifications' ? 'active' : ''}`}
          onClick={() => setActiveTab('notifications')}
        >
          Notifications
        </button>
        <button 
          className={`tab ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => setActiveTab('settings')}
        >
          Settings
        </button>
      </div>

      {/* Credit Sub-tabs */}
      {activeTab === 'credits' && (
        <div className="admin-subtabs">
          <button 
            className={`subtab ${activeSubTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('dashboard')}
          >
            Dashboard
          </button>
          <button 
            className={`subtab ${activeSubTab === 'management' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('management')}
          >
            Management
          </button>
          <button 
            className={`subtab ${activeSubTab === 'ledger' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('ledger')}
          >
            Ledger
          </button>
          <button 
            className={`subtab ${activeSubTab === 'daily' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('daily')}
          >
            Daily
          </button>
          <button 
            className={`subtab ${activeSubTab === 'requests' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('requests')}
          >
            Requests
          </button>
          <button 
            className={`subtab ${activeSubTab === 'playRefund' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('playRefund')}
          >
            Google Play refund
          </button>
        </div>
      )}

      {/* Users Sub-tabs */}
      {activeTab === 'users' && (
        <div className="admin-subtabs">
          <button 
            className={`subtab ${activeSubTab === 'management' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('management')}
          >
            User Management
          </button>
          <button 
            className={`subtab ${activeSubTab === 'facts' ? 'active' : ''}`}
            onClick={() => {
              setActiveSubTab('facts');
              setFactsPage(1);
            }}
          >
            Facts
          </button>
        </div>
      )}

      {/* Analysis Sub-tabs */}
      {activeTab === 'analysis' && (
        <div className="admin-subtabs">
          <button 
            className={`subtab ${activeSubTab === 'feedback' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('feedback')}
          >
            Chat Feedback
          </button>
          <button 
            className={`subtab ${activeSubTab === 'chatAnalysis' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('chatAnalysis')}
          >
            Chat Analysis
          </button>
        </div>
      )}

      <div className="admin-content">
        {activeTab === 'users' && activeSubTab === 'management' && (
          <div className="users-management">
            <h2>User Management</h2>
            {loading ? (
              <div className="loading">Loading users...</div>
            ) : (
              <div className="users-table">
                <table>
                  <thead>
                    <tr>
                      <th>Phone</th>
                      <th>Name</th>
                      <th>Role</th>
                      <th>Subscriptions</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.map(user => (
                      <tr key={user.phone}>
                        <td>{user.phone}</td>
                        <td>{user.name}</td>
                        <td>
                          {editingUser === user.phone ? (
                            <select 
                              defaultValue={user.role || 'user'}
                              onChange={(e) => handleUpdateUser(user.phone, { role: e.target.value })}
                            >
                              <option value="user">User</option>
                              <option value="admin">Admin</option>
                            </select>
                          ) : (
                            user.role || 'user'
                          )}
                        </td>
                        <td>
                          <div className="subscriptions">
                            {user.subscriptions && Object.keys(user.subscriptions).length > 0 ? (
                              Object.entries(user.subscriptions).map(([platform, sub]) => (
                                <div key={platform} className="subscription-item">
                                  {editingSubscription === `${user.userid}-${platform}` ? (
                                    <div className="subscription-edit">
                                      <select 
                                        defaultValue={sub.plan_name}
                                        onChange={(e) => setPendingSubscription({
                                          userId: user.userid,
                                          platform: platform,
                                          planName: e.target.value
                                        })}
                                      >
                                        {subscriptionPlans
                                          .filter(plan => plan.platform === platform)
                                          .map(plan => (
                                            <option key={plan.plan_name} value={plan.plan_name}>
                                              {plan.plan_name}
                                            </option>
                                          ))
                                        }
                                      </select>
                                      <button onClick={handleSaveSubscription} className="save-btn">Save</button>
                                      <button onClick={handleCancelSubscription} className="cancel-btn">Cancel</button>
                                    </div>
                                  ) : (
                                    <span 
                                      className={`subscription ${sub.status}`}
                                      onClick={() => setEditingSubscription(`${user.userid}-${platform}`)}
                                      style={{ cursor: 'pointer' }}
                                    >
                                      {platform}: {sub.plan_name}
                                    </span>
                                  )}
                                </div>
                              ))
                            ) : (
                              <div>
                                <span>None</span>
                                <button 
                                  onClick={() => setEditingSubscription(`${user.userid}-new`)}
                                  className="add-subscription-btn"
                                >
                                  Add
                                </button>
                                {editingSubscription === `${user.userid}-new` && (
                                  <div className="new-subscription">
                                    <select 
                                      onChange={(e) => {
                                        const [platform, planName] = e.target.value.split('|');
                                        if (platform && planName) {
                                          setPendingSubscription({
                                            userId: user.userid,
                                            platform: platform,
                                            planName: planName
                                          });
                                        }
                                      }}
                                    >
                                      <option value="">Select Plan</option>
                                      {subscriptionPlans.map(plan => (
                                        <option key={`${plan.platform}-${plan.plan_name}`} value={`${plan.platform}|${plan.plan_name}`}>
                                          {plan.platform}: {plan.plan_name}
                                        </option>
                                      ))}
                                    </select>
                                    <button onClick={handleSaveSubscription} className="save-btn">Save</button>
                                    <button onClick={handleCancelSubscription} className="cancel-btn">Cancel</button>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </td>
                        <td>{new Date(user.created_at).toLocaleDateString()}</td>
                        <td>
                          <button 
                            onClick={() => setEditingUser(editingUser === user.phone ? null : user.phone)}
                            className="edit-btn"
                          >
                            {editingUser === user.phone ? 'Cancel' : 'Edit'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'users' && activeSubTab === 'facts' && (
          <div className="facts-management">
            <h2>User Facts</h2>
            
            <div className="facts-search">
              <input
                type="text"
                placeholder="Search by username, phone, or native name..."
                value={factsSearch}
                onChange={(e) => setFactsSearch(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && fetchUserFacts()}
              />
              <button onClick={fetchUserFacts}>Search</button>
            </div>

            {factsLoading ? (
              <div className="loading">Loading facts...</div>
            ) : userFacts.length === 0 ? (
              <p>No facts found</p>
            ) : (
              <div className="facts-table">
                <table>
                  <thead>
                    <tr>
                      <th>Username</th>
                      <th>Phone</th>
                      <th>Native Name</th>
                      <th>Category</th>
                      <th>Fact</th>
                      <th>Extracted</th>
                    </tr>
                  </thead>
                  <tbody>
                    {userFacts.map((fact, idx) => (
                      <tr key={idx}>
                        <td>{fact.username}</td>
                        <td>{fact.phone}</td>
                        <td>{fact.native_name}</td>
                        <td><span className={`category-badge ${fact.category}`}>{fact.category}</span></td>
                        <td>{fact.fact}</td>
                        <td>{new Date(fact.extracted_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {factsTotalPages > 1 && (
              <div className="pagination">
                <button 
                  onClick={() => setFactsPage(p => Math.max(1, p - 1))}
                  disabled={factsPage === 1}
                >
                  Previous
                </button>
                <span>Page {factsPage} of {factsTotalPages}</span>
                <button 
                  onClick={() => setFactsPage(p => Math.min(factsTotalPages, p + 1))}
                  disabled={factsPage === factsTotalPages}
                >
                  Next
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'charts' && (
          <div className="charts-management">
            <h2>Birth Charts Management</h2>
            {loading ? (
              <div className="loading">Loading charts...</div>
            ) : (
              <div className="charts-table">
                <table>
                  <thead>
                    <tr>
                      <th>Chart ID</th>
                      <th>Name</th>
                      <th>Gender</th>
                      <th>Owner Phone</th>
                      <th>Owner Name</th>
                      <th>Birth Date</th>
                      <th>Birth Time</th>
                      <th>Location</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {charts.map(chart => (
                      <tr key={chart.id}>
                        <td>{chart.id}</td>
                        <td>{chart.name}</td>
                        <td>{chart.gender || 'Not specified'}</td>
                        <td>{chart.user_phone}</td>
                        <td>{chart.user_name}</td>
                        <td>{chart.date}</td>
                        <td>{chart.time}</td>
                        <td>{chart.place || `${chart.latitude?.toFixed(2)}, ${chart.longitude?.toFixed(2)}`}</td>
                        <td>{new Date(chart.created_at).toLocaleString()}</td>
                        <td>
                          <button 
                            onClick={() => handleDeleteChart(chart.id)}
                            className="delete-btn"
                          >
                            Delete
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'chat' && (
          <AdminChatHistory />
        )}

        {activeTab === 'ledger' && (
          <AdminCreditLedger />
        )}

        {activeTab === 'credits' && activeSubTab === 'management' && (
          <div className="credits-management">
            <h2>Credit Management</h2>
            
            <div className="credit-settings">
              <h3>Feature Costs</h3>
              <div className="settings-form">
                {creditSettings.map(setting => (
                  <div key={setting.key} className="setting-item">
                    <label>{setting.description}</label>
                    <input
                      type="number"
                      value={setting.value}
                      onChange={(e) => handleSettingChange(setting.key, e.target.value)}
                      min="1"
                    />
                  </div>
                ))}
                <button onClick={handleUpdateSettings} className="update-settings-btn">
                  Update Costs
                </button>
              </div>
            </div>

            <div className="credit-stats">
              <h3>Statistics</h3>
              <div className="stats-grid">
                <div className="stat-card">
                  <h4>Total Codes</h4>
                  <p>{creditStats.total_codes || 0}</p>
                </div>
                <div className="stat-card">
                  <h4>Active Codes</h4>
                  <p>{creditStats.active_codes || 0}</p>
                </div>
                <div className="stat-card">
                  <h4>Used Codes</h4>
                  <p>{creditStats.used_codes || 0}</p>
                </div>
                <div className="stat-card">
                  <h4>Credits Distributed</h4>
                  <p>{creditStats.total_credits_distributed || 0}</p>
                </div>
              </div>
            </div>

            <div className="promo-code-creation">
              <h3>Create Promo Code</h3>
              <div className="create-form">
                <div className="form-field">
                  <label>Code</label>
                  <input
                    type="text"
                    placeholder="e.g., WELCOME123"
                    value={newPromoCode.code}
                    onChange={(e) => setNewPromoCode({...newPromoCode, code: e.target.value.toUpperCase()})}
                  />
                </div>
                <div className="form-field">
                  <label>Credits</label>
                  <input
                    type="number"
                    placeholder="100"
                    value={newPromoCode.credits}
                    onChange={(e) => setNewPromoCode({...newPromoCode, credits: parseInt(e.target.value)})}
                  />
                </div>
                <div className="form-field">
                  <label>Max Uses (Total)</label>
                  <input
                    type="number"
                    placeholder="1"
                    value={newPromoCode.max_uses}
                    onChange={(e) => setNewPromoCode({...newPromoCode, max_uses: parseInt(e.target.value)})}
                  />
                </div>
                <div className="form-field">
                  <label>Max Uses Per User</label>
                  <input
                    type="number"
                    placeholder="1"
                    value={newPromoCode.max_uses_per_user}
                    onChange={(e) => setNewPromoCode({...newPromoCode, max_uses_per_user: parseInt(e.target.value)})}
                  />
                </div>
                <div className="form-buttons">
                  <button onClick={handleCreatePromoCode} className="create-btn">
                    Create Code
                  </button>
                  <button onClick={handleBulkPromoCodes} className="bulk-btn">
                    Create Bulk Codes
                  </button>
                </div>
              </div>
            </div>

            <div className="promo-codes-list">
              <h3>Promo Codes</h3>
              <div className="codes-table">
                <table>
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Credits</th>
                      <th>Max Uses (Total)</th>
                      <th>Max Uses Per User</th>
                      <th>Used Count</th>
                      <th>Status</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {promoCodes.map(code => (
                      <tr key={code.code}>
                        <td><strong>{code.code}</strong></td>
                        <td>
                          {editingPromoCode === code.code ? (
                            <input
                              type="number"
                              value={editFormData.credits || code.credits}
                              onChange={(e) => setEditFormData({...editFormData, credits: parseInt(e.target.value)})}
                              style={{ width: '80px' }}
                            />
                          ) : (
                            code.credits
                          )}
                        </td>
                        <td>
                          {editingPromoCode === code.code ? (
                            <input
                              type="number"
                              value={editFormData.max_uses || code.max_uses}
                              onChange={(e) => setEditFormData({...editFormData, max_uses: parseInt(e.target.value)})}
                              style={{ width: '60px' }}
                            />
                          ) : (
                            code.max_uses
                          )}
                        </td>
                        <td>
                          {editingPromoCode === code.code ? (
                            <input
                              type="number"
                              value={editFormData.max_uses_per_user || code.max_uses_per_user}
                              onChange={(e) => setEditFormData({...editFormData, max_uses_per_user: parseInt(e.target.value)})}
                              style={{ width: '60px' }}
                            />
                          ) : (
                            code.max_uses_per_user
                          )}
                        </td>
                        <td>{code.used_count}</td>
                        <td>
                          {editingPromoCode === code.code ? (
                            <select
                              value={editFormData.is_active !== undefined ? (editFormData.is_active ? '1' : '0') : (code.is_active ? '1' : '0')}
                              onChange={(e) => setEditFormData({...editFormData, is_active: e.target.value === '1'})}
                            >
                              <option value="1">Active</option>
                              <option value="0">Inactive</option>
                            </select>
                          ) : (
                            <span className={`status ${code.is_active ? 'active' : 'inactive'}`}>
                              {code.is_active ? 'Active' : 'Inactive'}
                            </span>
                          )}
                        </td>
                        <td>{new Date(code.created_at).toLocaleString()}</td>
                        <td>
                          {editingPromoCode === code.code ? (
                            <div>
                              <button 
                                onClick={() => handleUpdatePromoCode(code.code, editFormData)}
                                className="save-btn"
                              >
                                Save
                              </button>
                              <button 
                                onClick={() => {
                                  setEditingPromoCode(null);
                                  setEditFormData({});
                                }}
                                className="cancel-btn"
                              >
                                Cancel
                              </button>
                            </div>
                          ) : (
                            <div>
                              <button 
                                onClick={() => startEditingPromoCode(code)}
                                className="edit-btn"
                              >
                                Edit
                              </button>
                              <button 
                                onClick={() => handleDeletePromoCode(code.code)}
                                className="delete-btn"
                              >
                                Delete
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'credits' && activeSubTab === 'dashboard' && (
          <AdminCreditsDashboard />
        )}

        {activeTab === 'credits' && activeSubTab === 'ledger' && (
          <AdminCreditLedger />
        )}

        {activeTab === 'credits' && activeSubTab === 'daily' && (
          <AdminDailyActivity />
        )}

        {activeTab === 'credits' && activeSubTab === 'playRefund' && (
          <AdminGooglePlayRefund />
        )}

        {activeTab === 'credits' && activeSubTab === 'requests' && (
            <div className="credit-requests-management">
            <h2>Credit Requests</h2>
            
            {/* Status Filter */}
            <div className="filter-section">
              <label htmlFor="statusFilter">Filter by Status:</label>
              <select 
                id="statusFilter"
                value={statusFilter} 
                onChange={(e) => setStatusFilter(e.target.value)}
                className="status-filter"
              >
                <option value="all">All Requests</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
            
            {creditRequests.filter(request => 
              statusFilter === 'all' || request.status === statusFilter
            ).length === 0 ? (
              <p>No {statusFilter === 'all' ? '' : statusFilter} credit requests</p>
            ) : (
              <div className="requests-table">
                <table>
                  <thead>
                    <tr>
                      <th>User</th>
                      <th>Requested Amount</th>
                      <th>Reason</th>
                      <th>Status</th>
                      <th>Approved Amount</th>
                      <th>Admin Notes</th>
                      <th>Date</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {creditRequests
                      .filter(request => statusFilter === 'all' || request.status === statusFilter)
                      .map(request => (
                      <tr key={request.id}>
                        <td>{request.user_name}</td>
                        <td>{request.requested_amount} credits</td>
                        <td>{request.reason}</td>
                        <td>
                          <span className={`status-badge status-${request.status}`}>
                            {request.status.toUpperCase()}
                          </span>
                        </td>
                        <td>{request.approved_amount || '-'}</td>
                        <td>{request.admin_notes || '-'}</td>
                        <td>{new Date(request.created_at).toLocaleDateString()}</td>
                        <td>
                          {request.status === 'pending' ? (
                            <div className="request-actions">
                              <button 
                                onClick={() => openApprovalModal(request)}
                                className="approve-btn"
                              >
                                Approve
                              </button>
                              <button 
                                onClick={() => {
                                  const notes = prompt('Rejection reason (optional):');
                                  if (notes !== null) {
                                    handleRejectRequest(request.id, notes);
                                  }
                                }}
                                className="reject-btn"
                              >
                                Reject
                              </button>
                            </div>
                          ) : (
                            <span className="processed-status">{request.status}</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'analysis' && activeSubTab === 'feedback' && (
          <ChatFeedback />
        )}

        {activeTab === 'analysis' && activeSubTab === 'chatAnalysis' && (
          <AdminChatAnalysis />
        )}

        {activeTab === 'errors' && (
          <ChatErrors />
        )}

        {activeTab === 'terms' && (
          <AdminTerms />
        )}

        {activeTab === 'blog' && (
          <BlogDashboard />
        )}

        {activeTab === 'notifications' && (
          <div className="notifications-admin">
            <h2>Send Push Notification</h2>
            <p className="notifications-description">
              Send a custom push notification to a user&apos;s mobile device. They must have the app installed and have allowed notifications.
            </p>
            <div className="notifications-form">
              <div className="form-field">
                <label>User</label>
                <select
                  value={notifUserId}
                  onChange={(e) => setNotifUserId(e.target.value)}
                  disabled={loading}
                >
                  <option value="">Select user...</option>
                  {users.map((u) => (
                    <option key={u.userid} value={u.userid}>
                      {u.name || 'No name'} ({u.phone})
                    </option>
                  ))}
                </select>
              </div>
              <div className="form-field">
                <label>Title (max 100 chars)</label>
                <input
                  type="text"
                  placeholder="Notification title"
                  value={notifTitle}
                  onChange={(e) => setNotifTitle(e.target.value)}
                  maxLength={100}
                />
              </div>
              <div className="form-field">
                <label>Body (max 200 chars)</label>
                <textarea
                  placeholder="Message body"
                  value={notifBody}
                  onChange={(e) => setNotifBody(e.target.value)}
                  maxLength={200}
                  rows={3}
                />
              </div>
              <div className="form-field">
                <label>Question (optional, max 500 chars)</label>
                <input
                  type="text"
                  placeholder="Pre-fill chat when user taps notification"
                  value={notifQuestion}
                  onChange={(e) => setNotifQuestion(e.target.value)}
                  maxLength={500}
                />
              </div>
              <div className="form-field">
                <label>For native (optional)</label>
                <select
                  value={notifNativeId}
                  onChange={(e) => setNotifNativeId(e.target.value)}
                  disabled={loading || !notifUserId}
                >
                  <option value="">Any — use user&apos;s current selection</option>
                  {(charts || [])
                    .filter((c) => Number(c.userid) === Number(notifUserId))
                    .map((c) => (
                      <option key={c.id} value={c.id}>
                        {c.name || 'Unnamed'} (id: {c.id})
                      </option>
                    ))}
                </select>
                <small className="form-hint">When user taps, app will switch to this native before opening chat.</small>
              </div>
              <div className="form-buttons">
                <button
                  type="button"
                  onClick={handleSendNotification}
                  disabled={notifSending || !notifUserId || !notifTitle.trim() || !notifBody.trim()}
                  className="create-btn"
                >
                  {notifSending ? 'Sending...' : 'Send Notification'}
                </button>
              </div>
            </div>
            {notifResult && (
              <div className={`notif-result ${notifResult.ok ? 'success' : 'error'}`}>
                {notifResult.ok ? (
                  <>
                    <strong>Done.</strong> {notifResult.message}
                    {notifResult.tokens_found === 0 && ' User has no registered devices.'}
                  </>
                ) : (
                  <strong>{notifResult.message}</strong>
                )}
              </div>
            )}
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="admin-settings">
            <h2>System Settings</h2>
            
            <div className="settings-section">
              <h3>Debug & Logging</h3>
              <div className="setting-item">
                <div className="setting-info">
                  <strong>Gemini Debug Logging</strong>
                  <p>Enable complete request/response logging for Gemini AI chat</p>
                </div>
                <label className="toggle-switch">
                  <input 
                    type="checkbox" 
                    checked={debugLogging}
                    onChange={handleToggleDebugLogging}
                  />
                  <span className="toggle-slider"></span>
                </label>
              </div>
            </div>

            <div className="settings-section">
              <h3>App Version Config</h3>
              <p className="settings-hint">
                Set the minimum allowed app versions. Users on older builds will see a blocking “Update required” screen.
                Leave a field empty to disable the gate for that platform.
              </p>
              <div className="setting-item">
                <div className="setting-info">
                  <strong>Android min versionCode</strong>
                  <p>Current Google Play versionCode to require or higher (e.g. 77).</p>
                </div>
                <input
                  type="number"
                  value={androidMinVersion}
                  onChange={(e) => setAndroidMinVersion(e.target.value)}
                  placeholder="e.g. 77"
                  style={{ width: '120px' }}
                />
              </div>
              <div className="setting-item">
                <div className="setting-info">
                  <strong>iOS min build number</strong>
                  <p>Current App Store build number to require or higher (e.g. 77).</p>
                </div>
                <input
                  type="number"
                  value={iosMinVersion}
                  onChange={(e) => setIosMinVersion(e.target.value)}
                  placeholder="e.g. 77"
                  style={{ width: '120px' }}
                />
              </div>
              <div className="form-buttons" style={{ marginTop: '12px' }}>
                <button type="button" className="create-btn" onClick={handleSaveAppVersionConfig}>
                  Save App Version Config
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
      </div>
      
      {showApprovalModal && selectedRequest && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '30px',
            borderRadius: '10px',
            minWidth: '400px',
            maxWidth: '500px'
          }}>
            <h3 style={{ marginTop: 0, color: '#e91e63' }}>Approve Credit Request</h3>
            <div style={{ marginBottom: '15px' }}>
              <strong>User:</strong> {selectedRequest.user_name}<br/>
              <strong>Requested:</strong> {selectedRequest.requested_amount} credits<br/>
              <strong>Reason:</strong> {selectedRequest.reason}
            </div>
            
            <div style={{ marginBottom: '15px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Amount to Approve:</label>
              <input
                type="number"
                value={approvalData.amount}
                onChange={(e) => setApprovalData({...approvalData, amount: parseInt(e.target.value) || 0})}
                min="0"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px'
                }}
              />
            </div>
            
            <div style={{ marginBottom: '20px' }}>
              <label style={{ display: 'block', marginBottom: '5px', fontWeight: 'bold' }}>Admin Notes (optional):</label>
              <textarea
                value={approvalData.notes}
                onChange={(e) => setApprovalData({...approvalData, notes: e.target.value})}
                rows="3"
                style={{
                  width: '100%',
                  padding: '8px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                  resize: 'vertical'
                }}
              />
            </div>
            
            <div style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
              <button 
                onClick={() => {
                  setShowApprovalModal(false);
                  setSelectedRequest(null);
                  setApprovalData({ amount: 0, notes: '' });
                }}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#ccc',
                  color: 'black',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button 
                onClick={() => handleApproveRequest(selectedRequest.id, approvalData.amount, approvalData.notes)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#4CAF50',
                  color: 'white',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Approve {approvalData.amount} Credits
              </button>
            </div>
          </div>
        </div>
      )}
      
      {deleteConfirmation && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            padding: '20px',
            borderRadius: '8px',
            textAlign: 'center',
            minWidth: '300px'
          }}>
            <h3>Confirm Delete</h3>
            <p>Are you sure you want to delete promo code <strong>{deleteConfirmation}</strong>?</p>
            <div style={{ marginTop: '20px' }}>
              <button 
                onClick={confirmDelete}
                style={{
                  backgroundColor: '#f44336',
                  color: 'white',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  marginRight: '10px',
                  cursor: 'pointer'
                }}
              >
                Delete
              </button>
              <button 
                onClick={cancelDelete}
                style={{
                  backgroundColor: '#ccc',
                  color: 'black',
                  border: 'none',
                  padding: '8px 16px',
                  borderRadius: '4px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminPanel;
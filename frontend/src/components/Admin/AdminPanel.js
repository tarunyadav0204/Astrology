import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminService } from '../../services/adminService';
import AdminChatHistory from './AdminChatHistory';
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
  const [users, setUsers] = useState([]);
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [editingSubscription, setEditingSubscription] = useState(null);
  const [pendingSubscription, setPendingSubscription] = useState(null);
  const [promoCodes, setPromoCodes] = useState([]);
  const [creditStats, setCreditStats] = useState({});
  const [newPromoCode, setNewPromoCode] = useState({ code: '', credits: 100, max_uses: 1 });
  const [creditSettings, setCreditSettings] = useState([]);

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
      fetchSubscriptionPlans();
    } else if (activeTab === 'charts') {
      fetchCharts();
    } else if (activeTab === 'credits') {
      fetchPromoCodes();
      fetchCreditStats();
      fetchCreditSettings();
    }
  }, [activeTab]);

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
          body: JSON.stringify({ prefix, count, credits, max_uses: 1 })
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

  return (
    <div className="admin-panel">
      <NavigationHeader 
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
          User Management
        </button>
        <button 
          className={`tab ${activeTab === 'charts' ? 'active' : ''}`}
          onClick={() => setActiveTab('charts')}
        >
          Birth Charts Management
        </button>
        <button 
          className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
          onClick={() => setActiveTab('chat')}
        >
          Chat History
        </button>
        <button 
          className={`tab ${activeTab === 'credits' ? 'active' : ''}`}
          onClick={() => setActiveTab('credits')}
        >
          Credit Management
        </button>
      </div>

      <div className="admin-content">
        {activeTab === 'users' && (
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
                      <th>Owner</th>
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
                        <td>{chart.date}</td>
                        <td>{chart.time}</td>
                        <td>{chart.place || `${chart.latitude?.toFixed(2)}, ${chart.longitude?.toFixed(2)}`}</td>
                        <td>{new Date(chart.created_at).toLocaleDateString()}</td>
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

        {activeTab === 'credits' && (
          <div className="credits-management">
            <h2>Credit Management</h2>
            
            <div className="credit-settings">
              <h3>Chat Question Cost</h3>
              <div className="settings-form">
                {creditSettings.filter(setting => setting.key === 'chat_question_cost').map(setting => (
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
                  Update Cost
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
                  <label>Max Uses Per User</label>
                  <input
                    type="number"
                    placeholder="1"
                    value={newPromoCode.max_uses}
                    onChange={(e) => setNewPromoCode({...newPromoCode, max_uses: parseInt(e.target.value)})}
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
                      <th>Max Uses Per User</th>
                      <th>Used Count</th>
                      <th>Status</th>
                      <th>Created</th>
                    </tr>
                  </thead>
                  <tbody>
                    {promoCodes.map(code => (
                      <tr key={code.code}>
                        <td><strong>{code.code}</strong></td>
                        <td>{code.credits}</td>
                        <td>{code.max_uses}</td>
                        <td>{code.used_count}</td>
                        <td>
                          <span className={`status ${code.is_active ? 'active' : 'inactive'}`}>
                            {code.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td>{new Date(code.created_at).toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
      </div>
    </div>
  );
};

export default AdminPanel;
import React, { useState, useEffect } from 'react';
import { adminService } from '../../services/adminService';
import './AdminPanel.css';

const AdminPanel = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('users');
  const [users, setUsers] = useState([]);
  const [charts, setCharts] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [editingSubscription, setEditingSubscription] = useState(null);
  const [pendingSubscription, setPendingSubscription] = useState(null);

  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
      fetchSubscriptionPlans();
    } else if (activeTab === 'charts') {
      fetchCharts();
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

  return (
    <div className="admin-panel">
      <div className="admin-header">
        <h1>Admin Panel</h1>
        <button onClick={onLogout} className="logout-btn">Logout</button>
      </div>

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
      </div>
    </div>
  );
};

export default AdminPanel;
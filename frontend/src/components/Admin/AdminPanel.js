import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminService, getAdminAuthHeaders, getDeviceId } from '../../services/adminService';
import AdminChatHistory from './AdminChatHistory';
import AdminCreditLedger from './AdminCreditLedger';
import AdminDailyActivity from './AdminDailyActivity';
import AdminActivity from './AdminActivity';
import AdminCreditsDashboard from './AdminCreditsDashboard';
import AdminUserCreditManagement from './AdminUserCreditManagement';
import AdminGooglePlayRefund from './AdminGooglePlayRefund';
import ChatFeedback from './ChatFeedback';
import ChatErrors from './ChatErrors';
import AdminChatPerformance from './AdminChatPerformance';
import AdminChatPerformanceCharts from './AdminChatPerformanceCharts';
import AdminChatAnalysis from './AdminChatAnalysis';
import AdminTerms from './AdminTerms';
import BlogDashboard from '../Blog/BlogDashboard';
import NavigationHeader from '../Shared/NavigationHeader';
import './AdminPanel.css';

/** API may return boolean, 0/1, or legacy strings for promo_codes.is_active */
function promoCodeIsActive(value) {
  if (value === true || value === 1) return true;
  if (value === false || value === 0 || value == null) return false;
  if (typeof value === 'string') {
    const s = value.trim().toLowerCase();
    if (s === '0' || s === 'false' || s === 'f' || s === 'no' || s === '') return false;
    return s === '1' || s === 'true' || s === 't' || s === 'yes';
  }
  return Boolean(value);
}

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
  const [usersSearchPhone, setUsersSearchPhone] = useState('');
  const [usersSearchName, setUsersSearchName] = useState('');
  const [usersSearchRole, setUsersSearchRole] = useState('all');
  const [usersSearchSubscription, setUsersSearchSubscription] = useState('all');
  const [usersSearchCreatedStart, setUsersSearchCreatedStart] = useState('');
  const [usersSearchCreatedEnd, setUsersSearchCreatedEnd] = useState('');
  const [usersPage, setUsersPage] = useState(1);
  const [usersTotal, setUsersTotal] = useState(0);
  const [usersTotalPages, setUsersTotalPages] = useState(0);
  const [usersLimit] = useState(25);
  const [userFacts, setUserFacts] = useState([]);
  const [factsSearch, setFactsSearch] = useState('');
  const [factsPage, setFactsPage] = useState(1);
  const [factsTotalPages, setFactsTotalPages] = useState(1);
  const [factsLoading, setFactsLoading] = useState(false);
  const [charts, setCharts] = useState([]);
  const [chartsSearchName, setChartsSearchName] = useState('');
  const [chartsSearchPhone, setChartsSearchPhone] = useState('');
  const [chartsPage, setChartsPage] = useState(1);
  const [chartsTotal, setChartsTotal] = useState(0);
  const [chartsTotalPages, setChartsTotalPages] = useState(0);
  const [chartsLimit] = useState(100);
  const [sharingChartId, setSharingChartId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [subscriptionPlans, setSubscriptionPlans] = useState([]);
  const [editingSubscription, setEditingSubscription] = useState(null);
  const [pendingSubscription, setPendingSubscription] = useState(null);
  const [seedVipLoading, setSeedVipLoading] = useState(false);
  const [editingPlanId, setEditingPlanId] = useState(null);
  const [editingPlanDiscount, setEditingPlanDiscount] = useState('');
  const [savingPlanDiscount, setSavingPlanDiscount] = useState(false);
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
  const [geminiModelOptions, setGeminiModelOptions] = useState([]);
  const [geminiChatModel, setGeminiChatModel] = useState('');
  const [geminiPremiumModel, setGeminiPremiumModel] = useState('');
  const [geminiAnalysisModel, setGeminiAnalysisModel] = useState('');
  const [geminiModelsSaving, setGeminiModelsSaving] = useState(false);
  const [podcastProvider, setPodcastProvider] = useState('tts');
  const [podcastProviderSaving, setPodcastProviderSaving] = useState(false);
  const [allowedDevices, setAllowedDevices] = useState([]);
  const [allowedDevicesLoading, setAllowedDevicesLoading] = useState(false);
  const [newAllowedDeviceId, setNewAllowedDeviceId] = useState('');
  const [newAllowedDeviceLabel, setNewAllowedDeviceLabel] = useState('');
  const [newAllowedDeviceForUserId, setNewAllowedDeviceForUserId] = useState('');
  const [blogPosts, setBlogPosts] = useState([]);
  const [notifUserId, setNotifUserId] = useState('');
  const [notifTitle, setNotifTitle] = useState('');
  const [notifBody, setNotifBody] = useState('');
  const [notifQuestion, setNotifQuestion] = useState('');
  const [notifNativeId, setNotifNativeId] = useState('');
  const [notifSending, setNotifSending] = useState(false);
  const [notifResult, setNotifResult] = useState(null);
  const [selectedNotifUserIds, setSelectedNotifUserIds] = useState([]); // multi-select
  const [notifSearchName, setNotifSearchName] = useState('');
  const [notifPage, setNotifPage] = useState(1);
  const [notifTotal, setNotifTotal] = useState(0);
  const [notifTotalPages, setNotifTotalPages] = useState(0);
  const [notifUserIdsWithTokens, setNotifUserIdsWithTokens] = useState([]); // userids who have accepted notifications
  const [notifSubTab, setNotifSubTab] = useState('custom'); // 'custom' | 'blog'
  const [blogNotifSelectedId, setBlogNotifSelectedId] = useState('');
  const [blogNotifAudience, setBlogNotifAudience] = useState('all'); // 'all' | 'eligible'
  const [selectedBlogNotifUserIds, setSelectedBlogNotifUserIds] = useState([]); // multi-select for blog tab
  const [blogNotifSending, setBlogNotifSending] = useState(false);
  const [blogNotifResult, setBlogNotifResult] = useState(null);
  const [redditDrafts, setRedditDrafts] = useState([]);
  const [redditDraftsLoading, setRedditDraftsLoading] = useState(false);
  const [redditCollecting, setRedditCollecting] = useState(false);
  const [redditCollectResult, setRedditCollectResult] = useState(null);
  const [redditEditingId, setRedditEditingId] = useState(null);
  const [redditEditMarkdown, setRedditEditMarkdown] = useState('');
  const [deviceAccessStatus, setDeviceAccessStatus] = useState('pending'); // 'pending' | 'allowed' | 'blocked'
  const [blockedDeviceId, setBlockedDeviceId] = useState(null);
  const [blockedUserId, setBlockedUserId] = useState(null);

  const checkDeviceAccess = React.useCallback(async () => {
    setDeviceAccessStatus('pending');
    try {
      const res = await fetch('/api/admin/allowed-devices', { headers: getAdminAuthHeaders() });
      if (res.status === 403) {
        const body = await res.json().catch(() => ({}));
        if (body.detail === 'Device not allowed') {
          setDeviceAccessStatus('blocked');
          setBlockedDeviceId(body.device_id ?? getDeviceId());
          setBlockedUserId(body.user_id ?? null);
          return;
        }
      }
      setDeviceAccessStatus('allowed');
    } catch {
      setDeviceAccessStatus('allowed');
    }
  }, []);

  useEffect(() => {
    checkDeviceAccess();
  }, [checkDeviceAccess]);

  const fetchRedditDrafts = async () => {
    setRedditDraftsLoading(true);
    try {
      const res = await fetch('/api/admin/reddit/answers/drafts?limit=50', {
        headers: getAdminAuthHeaders(),
      });
      const data = await res.json();
      setRedditDrafts(data.drafts || []);
    } catch (e) {
      console.error('Fetch Reddit drafts failed:', e);
      setRedditDrafts([]);
    } finally {
      setRedditDraftsLoading(false);
    }
  };

  const runRedditCollect = async () => {
    setRedditCollecting(true);
    setRedditCollectResult(null);
    try {
      const res = await fetch('/api/admin/reddit/collect?days_back=7&limit_per_sub=100', {
        method: 'POST',
        headers: getAdminAuthHeaders(),
      });
      const data = await res.json();
      if (res.ok) {
        setRedditCollectResult(data);
        fetchRedditDrafts();
      } else {
        setRedditCollectResult({ error: data.detail || 'Collect failed' });
      }
    } catch (e) {
      setRedditCollectResult({ error: e.message || 'Request failed' });
    } finally {
      setRedditCollecting(false);
    }
  };

  const approveRedditAnswer = async (answerId, editedMarkdown) => {
    try {
      const res = await fetch(`/api/admin/reddit/answers/${answerId}/approve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAdminAuthHeaders(),
        },
        body: JSON.stringify({ edited_markdown: editedMarkdown }),
      });
      if (res.ok) {
        setRedditEditingId(null);
        fetchRedditDrafts();
      } else {
        const d = await res.json();
        alert(d.detail || 'Approve failed');
      }
    } catch (e) {
      alert(e.message || 'Request failed');
    }
  };

  const rejectRedditAnswer = async (answerId) => {
    if (!window.confirm('Reject this draft? It will not be posted.')) return;
    try {
      const res = await fetch(`/api/admin/reddit/answers/${answerId}/reject`, {
        method: 'POST',
        headers: getAdminAuthHeaders(),
      });
      if (res.ok) {
        setRedditEditingId(null);
        fetchRedditDrafts();
      }
    } catch (e) {
      alert(e.message || 'Request failed');
    }
  };

  useEffect(() => {
    if (activeTab === 'users') {
      if (activeSubTab === 'management') {
        fetchUsers();
        fetchSubscriptionPlans();
      } else if (activeSubTab === 'facts') {
        fetchUserFacts();
      }
    } else if (activeTab === 'charts') {
      fetchCharts();
    } else if (activeTab === 'credits') {
      if (activeSubTab === 'management') {
        fetchPromoCodes();
        fetchCreditStats();
        fetchCreditSettings();
        fetchSubscriptionPlans();
      } else if (activeSubTab === 'requests') {
        fetchCreditRequests();
      }
    } else if (activeTab === 'chat') {
      // Chat history will be loaded by AdminChatHistory component
    } else if (activeTab === 'ledger') {
      // Credit ledger will be loaded by AdminCreditLedger component
    } else if (activeTab === 'settings') {
      fetchAdminSettings();
      fetchAllowedDevices();
    } else if (activeTab === 'reddit') {
      fetchRedditDrafts();
    } else if (activeTab === 'notifications') {
      fetchUsersForNotifications();
      fetchNotifUserIdsWithTokens();
      fetchBlogPosts();
    }
  }, [activeTab, activeSubTab]);

  const fetchAllowedDevices = async () => {
    setAllowedDevicesLoading(true);
    try {
      const data = await adminService.getAllowedDevices();
      setAllowedDevices(data.devices || []);
    } catch (e) {
      console.error('Failed to fetch allowed devices', e);
      setAllowedDevices([]);
    } finally {
      setAllowedDevicesLoading(false);
    }
  };

  const fetchAdminSettings = async () => {
    try {
      const response = await fetch('/api/admin/settings', {
        headers: getAdminAuthHeaders()
      });
      const data = await response.json();
      setAdminSettings(data.settings || []);
      const debugSetting = data.settings.find(s => s.key === 'debug_logging_enabled');
      setDebugLogging(debugSetting?.value === 'true');
      const androidMin = data.settings.find(s => s.key === 'min_android_version_code');
      const iosMin = data.settings.find(s => s.key === 'min_ios_build_number');
      setAndroidMinVersion(androidMin?.value ?? '');
      setIosMinVersion(iosMin?.value ?? '');
      setGeminiModelOptions(data.gemini_model_options || []);
      setGeminiChatModel(data.gemini_chat_model || '');
      setGeminiPremiumModel(data.gemini_premium_model || '');
      setGeminiAnalysisModel(data.gemini_analysis_model || '');
      setPodcastProvider(data.podcast_provider || 'tts');
    } catch (error) {
      console.error('Error fetching admin settings:', error);
    }
  };

  const fetchBlogPosts = async () => {
    try {
      const response = await fetch('/api/blog/posts?status=published&limit=100', {
        headers: getAdminAuthHeaders(),
      });
      if (!response.ok) {
        console.error('Failed to fetch blog posts for notifications:', response.status);
        return;
      }
      const data = await response.json();
      if (Array.isArray(data)) {
        setBlogPosts(data);
      } else if (Array.isArray(data.posts)) {
        setBlogPosts(data.posts);
      }
    } catch (e) {
      console.error('Error fetching blog posts for notifications:', e);
    }
  };

  const handleSaveGeminiModels = async () => {
    setGeminiModelsSaving(true);
    try {
      const headers = { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' };
      const [chatRes, premiumRes, analysisRes] = await Promise.all([
        fetch('/api/admin/settings/gemini_chat_model', {
          method: 'PUT',
          headers,
          body: JSON.stringify({
            key: 'gemini_chat_model',
            value: geminiChatModel,
            description: 'Gemini model for standard chat',
          }),
        }),
        fetch('/api/admin/settings/gemini_premium_model', {
          method: 'PUT',
          headers,
          body: JSON.stringify({
            key: 'gemini_premium_model',
            value: geminiPremiumModel,
            description: 'Gemini model for premium chat',
          }),
        }),
        fetch('/api/admin/settings/gemini_analysis_model', {
          method: 'PUT',
          headers,
          body: JSON.stringify({
            key: 'gemini_analysis_model',
            value: geminiAnalysisModel,
            description: 'Gemini model for analysis (health, wealth, career, karma, physical, events, etc.)',
          }),
        }),
      ]);
      if (!chatRes.ok || !premiumRes.ok || !analysisRes.ok) {
        const chatErr = await chatRes.json().catch(() => ({}));
        const premiumErr = await premiumRes.json().catch(() => ({}));
        const analysisErr = await analysisRes.json().catch(() => ({}));
        console.error('Save failed:', chatErr, premiumErr, analysisErr);
        alert('Failed to save: ' + (chatErr.detail || premiumErr.detail || analysisErr.detail || 'check console'));
        return;
      }
      alert('Gemini models saved. New requests will use the selected models immediately.');
    } catch (error) {
      console.error('Error saving Gemini models:', error);
      alert('Failed to save Gemini models.');
    } finally {
      setGeminiModelsSaving(false);
    }
  };

  const handleToggleDebugLogging = async () => {
    const newValue = !debugLogging;
    try {
      const response = await fetch('/api/admin/settings/debug_logging_enabled', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAdminAuthHeaders()
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
              ...getAdminAuthHeaders(),
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

  const fetchUsers = async (pageOverride) => {
    setLoading(true);
    const page = pageOverride !== undefined ? pageOverride : usersPage;
    if (pageOverride !== undefined) setUsersPage(page);
    try {
      const params = {
        phone: usersSearchPhone.trim() || undefined,
        name: usersSearchName.trim() || undefined,
        role: usersSearchRole === 'all' ? undefined : usersSearchRole,
        subscription: usersSearchSubscription === 'all' ? undefined : usersSearchSubscription,
        created_from: usersSearchCreatedStart.trim() || undefined,
        created_to: usersSearchCreatedEnd.trim() || undefined,
        page,
        limit: usersLimit,
      };
      const data = await adminService.getAllUsers(params);
      setUsers(data.users || []);
      setUsersTotal(data.total ?? 0);
      setUsersTotalPages(data.total_pages ?? 0);
    } catch (error) {
      console.error('Error fetching users:', error);
      setUsers([]);
      setUsersTotal(0);
      setUsersTotalPages(0);
    } finally {
      setLoading(false);
    }
  };

  const fetchUsersForNotifications = async (pageOverride = null) => {
    setLoading(true);
    const page = pageOverride != null ? pageOverride : notifPage;
    if (pageOverride != null) setNotifPage(page);
    try {
      const params = {
        page,
        limit: 100,
        name: notifSearchName.trim() || undefined,
      };
      const data = await adminService.getAllUsers(params);
      setUsers(data.users || []);
      setNotifTotal(data.total ?? 0);
      setNotifTotalPages(data.total_pages ?? 0);
    } catch (error) {
      console.error('Error fetching users for notifications:', error);
      setUsers([]);
      setNotifTotal(0);
      setNotifTotalPages(0);
    } finally {
      setLoading(false);
    }
  };

  const fetchNotifUserIdsWithTokens = async () => {
    try {
      const tokenRes = await fetch('/api/nudge/admin/user-ids-with-tokens', {
        headers: getAdminAuthHeaders(),
      });
      if (tokenRes.ok) {
        const tokenData = await tokenRes.json();
        setNotifUserIdsWithTokens(tokenData.user_ids || []);
      } else {
        setNotifUserIdsWithTokens([]);
      }
    } catch (e) {
      setNotifUserIdsWithTokens([]);
    }
  };

  const fetchUserFacts = async () => {
    setFactsLoading(true);
    try {
      const response = await fetch(`/api/admin/facts?search=${factsSearch}&page=${factsPage}&limit=20`, {
        headers: getAdminAuthHeaders()
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

  const fetchCharts = async (pageOverride = null) => {
    setLoading(true);
    const page = pageOverride != null ? pageOverride : chartsPage;
    if (pageOverride != null) setChartsPage(page);
    try {
      const data = await adminService.getAllCharts({
        name: chartsSearchName.trim() || undefined,
        phone: chartsSearchPhone.trim() || undefined,
        page,
        limit: chartsLimit,
      });
      setCharts(data.charts || []);
      setChartsTotal(data.total ?? 0);
      setChartsTotalPages(data.total_pages ?? 0);
    } catch (error) {
      console.error('Error fetching charts:', error);
      setCharts([]);
      setChartsTotal(0);
      setChartsTotalPages(0);
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

  const handleUpdateSubscription = async (userId, platform, planName, durationDays) => {
    try {
      const payload = { platform, plan_name: planName };
      if (durationDays != null && durationDays > 0) payload.duration_days = durationDays;
      await adminService.updateUserSubscription(userId, payload);
      fetchUsers();
      setEditingSubscription(null);
      setPendingSubscription(null);
    } catch (error) {
      console.error('Error updating subscription:', error);
    }
  };

  const handleSaveSubscription = () => {
    if (pendingSubscription) {
      const { userId, platform, planName, duration_days } = pendingSubscription;
      handleUpdateSubscription(userId, platform, planName, duration_days);
    }
  };

  const handleCancelSubscription = () => {
    setEditingSubscription(null);
    setPendingSubscription(null);
  };

  const handleSavePlanDiscount = async (planId) => {
    const value = parseInt(editingPlanDiscount, 10);
    if (isNaN(value) || value < 0 || value > 100) {
      alert('Discount must be 0–100');
      return;
    }
    setSavingPlanDiscount(true);
    try {
      await adminService.updateSubscriptionPlan(planId, { discount_percent: value });
      setEditingPlanId(null);
      setEditingPlanDiscount('');
      fetchSubscriptionPlans();
    } catch (error) {
      console.error('Error updating plan discount:', error);
      alert(error.message || 'Failed to update discount');
    } finally {
      setSavingPlanDiscount(false);
    }
  };

  const handleShareForInvestigation = async (chartId) => {
    setSharingChartId(chartId);
    try {
      const res = await adminService.shareChartForInvestigation(chartId);
      alert(res.message || `Chart copied to ${res.copied_count} admin(s) for investigation.`);
    } catch (error) {
      console.error('Error sharing chart:', error);
      alert(error.message || 'Failed to share chart');
    } finally {
      setSharingChartId(null);
    }
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
        headers: getAdminAuthHeaders()
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
        headers: getAdminAuthHeaders()
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
          ...getAdminAuthHeaders()
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
            ...getAdminAuthHeaders()
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
        headers: getAdminAuthHeaders()
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
          ...getAdminAuthHeaders()
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
        setting.key === key ? { ...setting, value: parseInt(value) || 0 } : setting
      )
    );
  };

  const vipTiers = ['Silver', 'Gold', 'Platinum'].map(name => {
    const plan = (subscriptionPlans || []).find(
      p => (p.tier_name || p.plan_name || '').toLowerCase().includes(name.toLowerCase())
    );
    return { name, discount: plan ? (plan.discount_percent ?? 0) : 0 };
  });

  const calcVipPrice = (price, discountPercent) => {
    const p = Number(price);
    if (!p || p <= 0) return '—';
    return Math.max(1, Math.round(p * (100 - discountPercent) / 100));
  };

  const handleSettingDiscountChange = (key, discountValue) => {
    const parsed = discountValue === '' || discountValue === undefined ? null : parseInt(discountValue, 10);
    setCreditSettings(prev =>
      prev.map(setting =>
        setting.key === key ? { ...setting, discount: parsed } : setting
      )
    );
  };

  const handleUpdatePromoCode = async (code, updates) => {
    const row = promoCodes.find((p) => p.code === code);
    if (!row) {
      alert('Promo code not found in table; refresh and try again.');
      return;
    }
    const credits = updates.credits != null ? Number(updates.credits) : Number(row.credits);
    const maxUses = updates.max_uses != null ? Number(updates.max_uses) : Number(row.max_uses);
    const maxPerUser =
      updates.max_uses_per_user != null ? Number(updates.max_uses_per_user) : Number(row.max_uses_per_user ?? 1);
    const isActive = updates.is_active != null ? Boolean(updates.is_active) : promoCodeIsActive(row.is_active);

    if (!Number.isFinite(credits) || credits < 1 || !Number.isFinite(maxUses) || maxUses < 1) {
      alert('Credits and max uses must be positive numbers');
      return;
    }
    if (!Number.isFinite(maxPerUser) || maxPerUser < 1) {
      alert('Max uses per user must be at least 1');
      return;
    }

    const payload = {
      credits,
      max_uses: maxUses,
      max_uses_per_user: maxPerUser,
      is_active: isActive,
    };

    try {
      const response = await fetch(`/api/credits/admin/promo-codes/${encodeURIComponent(code)}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          ...getAdminAuthHeaders()
        },
        body: JSON.stringify(payload)
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
      max_uses_per_user: code.max_uses_per_user ?? 1,
      is_active: promoCodeIsActive(code.is_active),
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
          ...getAdminAuthHeaders()
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
    const userIds = selectedNotifUserIds.map((id) => parseInt(id, 10)).filter(Boolean);
    if (!userIds.length || !notifTitle.trim() || !notifBody.trim()) {
      const msg = 'Please select at least one user and enter both title and body.';
      setNotifResult({ ok: false, message: msg });
      console.warn('[Admin Notifications] Validation failed:', msg);
      return;
    }
    setNotifSending(true);
    setNotifResult(null);
    console.log('[Admin Notifications] Sending to user_ids=', userIds, 'title=', notifTitle.trim().slice(0, 50));
    try {
      let totalSent = 0;
      let totalTokensFound = 0;
      for (const userId of userIds) {
        const response = await fetch('/api/nudge/admin/send', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...getAdminAuthHeaders(),
          },
          body: JSON.stringify({
            user_id: userId,
            title: notifTitle.trim().slice(0, 100),
            body: notifBody.trim().slice(0, 200),
            ...(notifQuestion.trim() && { question: notifQuestion.trim().slice(0, 500) }),
            ...(notifNativeId && userIds.length === 1 && { native_id: parseInt(notifNativeId, 10) }),
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
          console.error('[Admin Notifications] Failed for user_id=', userId, response.status, data);
          setNotifResult({ ok: false, message: typeof message === 'string' ? message : JSON.stringify(message) });
          return;
        }
        totalSent += data.sent || 0;
        totalTokensFound += data.tokens_found || 0;
      }
      const summary = {
        ok: true,
        sent: totalSent,
        tokens_found: totalTokensFound,
        message: `Notifications sent. Devices reached: ${totalSent} of ${totalTokensFound}.`,
      };
      console.log('[Admin Notifications] Success batch:', summary);
      setNotifResult(summary);
      setNotifTitle('');
      setNotifBody('');
      setNotifQuestion('');
      setNotifNativeId('');
    } catch (err) {
      console.error('[Admin Notifications] Request error:', err);
      setNotifResult({ ok: false, message: err.message || 'Request failed' });
    } finally {
      setNotifSending(false);
    }
  };

  const handleSendBlogNotification = async () => {
    const blogId = blogNotifSelectedId ? parseInt(blogNotifSelectedId, 10) : 0;
    if (!blogId) {
      setBlogNotifResult({ ok: false, message: 'Please select a blog post.' });
      return;
    }
    setBlogNotifSending(true);
    setBlogNotifResult(null);
    console.log('[Admin Blog Notifications] Sending blog_id=', blogId, 'audience=', blogNotifAudience);
    try {
      const response = await fetch('/api/nudge/admin/send-blog', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...getAdminAuthHeaders(),
        },
        body: JSON.stringify({
          blog_id: blogId,
          audience: blogNotifAudience, // 'all' or 'eligible'
          user_ids: selectedBlogNotifUserIds,
        }),
      });
      let data;
      try {
        data = await response.json();
      } catch (_) {
        const text = await response.text();
        console.error('[Admin Blog Notifications] Non-JSON response:', response.status, text?.slice(0, 200));
        setBlogNotifResult({ ok: false, message: `Server error ${response.status}: ${text?.slice(0, 100) || 'Invalid response'}` });
        return;
      }
      if (!response.ok) {
        const message = data.detail || data.message || 'Failed to send';
        console.error('[Admin Blog Notifications] Failed:', response.status, data);
        setBlogNotifResult({ ok: false, message: typeof message === 'string' ? message : JSON.stringify(message) });
        return;
      }
      console.log('[Admin Blog Notifications] Success:', data);
      setBlogNotifResult(data);
      if (data.ok) {
        setBlogNotifSelectedId('');
      }
    } catch (err) {
      console.error('[Admin Blog Notifications] Request error:', err);
      setBlogNotifResult({ ok: false, message: err.message || 'Request failed' });
    } finally {
      setBlogNotifSending(false);
    }
  };

  const fetchCreditRequests = async () => {
    try {
      const response = await fetch('/api/credits/requests/all', {
        headers: getAdminAuthHeaders()
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
          ...getAdminAuthHeaders()
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
          ...getAdminAuthHeaders()
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
      {deviceAccessStatus === 'pending' && (
        <div className="admin-device-check">
          <p>Checking access…</p>
        </div>
      )}
      {deviceAccessStatus === 'blocked' && (
        <div className="admin-device-blocked">
          <h2>Admin access restricted</h2>
          {blockedUserId != null && (
            <p className="admin-device-blocked-id">
              <strong>User ID:</strong> <code>{blockedUserId}</code>
              <button
                type="button"
                className="copy-device-id-btn"
                onClick={() => {
                  navigator.clipboard?.writeText(String(blockedUserId)).then(() => alert('Copied.')).catch(() => alert('Copy failed.'));
                }}
              >
                Copy
              </button>
            </p>
          )}
          <p className="admin-device-blocked-id">
            <strong>Device ID:</strong>{' '}
            <code>{blockedDeviceId || getDeviceId()}</code>
            <button
              type="button"
              className="copy-device-id-btn"
              onClick={() => {
                const id = blockedDeviceId || getDeviceId();
                navigator.clipboard?.writeText(id).then(() => alert('Copied.')).catch(() => alert('Copy failed.'));
              }}
            >
              Copy
            </button>
          </p>
        </div>
      )}
      {deviceAccessStatus === 'allowed' && (
      <>
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
          className={`tab ${activeTab === 'performance' ? 'active' : ''}`}
          onClick={() => {
            setActiveTab('performance');
            setActiveSubTab('list');
          }}
        >
          Chat Performance
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
          className={`tab ${activeTab === 'reddit' ? 'active' : ''}`}
          onClick={() => setActiveTab('reddit')}
        >
          Reddit
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
            className={`subtab ${activeSubTab === 'userCredits' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('userCredits')}
          >
            User Credit Management
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
          <button 
            className={`subtab ${activeSubTab === 'activity' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('activity')}
          >
            Activity
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

      {/* Chat Performance Sub-tabs */}
      {activeTab === 'performance' && (
        <div className="admin-subtabs">
          <button 
            className={`subtab ${activeSubTab === 'list' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('list')}
          >
            List
          </button>
          <button 
            className={`subtab ${activeSubTab === 'charts' ? 'active' : ''}`}
            onClick={() => setActiveSubTab('charts')}
          >
            Charts
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
              <>
                <div className="users-management-filters">
                  <label>
                    <span>Phone</span>
                    <input
                      type="text"
                      placeholder="Search by phone"
                      value={usersSearchPhone}
                      onChange={(e) => setUsersSearchPhone(e.target.value)}
                    />
                  </label>
                  <label>
                    <span>Name</span>
                    <input
                      type="text"
                      placeholder="Search by name"
                      value={usersSearchName}
                      onChange={(e) => setUsersSearchName(e.target.value)}
                    />
                  </label>
                  <label>
                    <span>Role</span>
                    <select
                      value={usersSearchRole}
                      onChange={(e) => setUsersSearchRole(e.target.value)}
                    >
                      <option value="all">All</option>
                      <option value="user">User</option>
                      <option value="admin">Admin</option>
                    </select>
                  </label>
                  <label>
                    <span>Subscription</span>
                    <select
                      value={usersSearchSubscription}
                      onChange={(e) => setUsersSearchSubscription(e.target.value)}
                    >
                      <option value="all">All</option>
                      <option value="none">None</option>
                      {subscriptionPlans && [...new Set(subscriptionPlans.map((p) => p.plan_name || p.tier_name).filter(Boolean))].map((planName) => (
                        <option key={planName} value={planName}>{planName}</option>
                      ))}
                    </select>
                  </label>
                  <label>
                    <span>Created from</span>
                    <input
                      type="date"
                      value={usersSearchCreatedStart}
                      onChange={(e) => setUsersSearchCreatedStart(e.target.value)}
                    />
                  </label>
                  <label>
                    <span>Created to</span>
                    <input
                      type="date"
                      value={usersSearchCreatedEnd}
                      onChange={(e) => setUsersSearchCreatedEnd(e.target.value)}
                    />
                  </label>
                  <button type="button" className="users-search-btn" onClick={() => fetchUsers(1)}>
                    Search
                  </button>
                </div>
                <div className="users-seed-vip">
                  <span>Don&apos;t see VIP Silver / Gold / Platinum in the subscription dropdown? </span>
                  <button
                    type="button"
                    className="users-seed-vip-btn"
                    disabled={seedVipLoading}
                    onClick={async () => {
                      setSeedVipLoading(true);
                      try {
                        await adminService.seedVipSubscriptionPlans();
                        await fetchSubscriptionPlans();
                        await fetchUsers(usersPage);
                      } catch (e) {
                        alert(e.message || 'Failed to seed VIP plans');
                      } finally {
                        setSeedVipLoading(false);
                      }
                    }}
                  >
                    {seedVipLoading ? 'Seeding…' : 'Seed VIP plans (Silver, Gold, Platinum)'}
                  </button>
                </div>
                <div className="users-table">
                <table>
                  <thead>
                    <tr>
                      <th>Phone</th>
                      <th>Name</th>
                      <th>Email</th>
                      <th>Role</th>
                      <th>Subscriptions</th>
                      <th>Created</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {users.length === 0 ? (
                      <tr><td colSpan={7} className="users-table-empty">No users match the search.</td></tr>
                    ) : (
                      users.map(user => (
                      <tr key={user.phone}>
                        <td>{user.phone}</td>
                        <td>{user.name || user.phone || '—'}</td>
                        <td>{user.email || '—'}</td>
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
                                        defaultValue={`${platform}|${sub.plan_name}`}
                                        onChange={(e) => {
                                          const val = e.target.value;
                                          if (val.includes('|')) {
                                            const [p, pn] = val.split('|');
                                            setPendingSubscription({ userId: user.userid, platform: p, planName: pn });
                                          } else {
                                            setPendingSubscription({ userId: user.userid, platform: platform, planName: val });
                                          }
                                        }}
                                      >
                                        {subscriptionPlans.map(plan => (
                                          <option key={`${plan.platform}-${plan.plan_name}`} value={`${plan.platform}|${plan.plan_name}`}>
                                            {plan.platform}: {plan.tier_name || plan.plan_name}
                                          </option>
                                        ))}
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
                                            platform,
                                            planName,
                                            duration_days: 30
                                          });
                                        }
                                      }}
                                    >
                                      <option value="">Select Plan</option>
                                      {subscriptionPlans.map(plan => (
                                        <option key={`${plan.platform}-${plan.plan_name}`} value={`${plan.platform}|${plan.plan_name}`}>
                                          {plan.platform}: {plan.tier_name || plan.plan_name}
                                        </option>
                                      ))}
                                    </select>
                                    {pendingSubscription?.planName && (
                                      <label className="new-subscription-duration">
                                        <span>Duration (days)</span>
                                        <input
                                          type="number"
                                          min={1}
                                          max={3660}
                                          value={pendingSubscription.duration_days ?? 30}
                                          onChange={(e) => setPendingSubscription(prev => ({ ...prev, duration_days: parseInt(e.target.value, 10) || 30 }))}
                                        />
                                        <small>e.g. 30 = 1 month, 365 = 1 year</small>
                                      </label>
                                    )}
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
                      ))
                    )}
                  </tbody>
                </table>
                {usersTotalPages > 0 && (
                  <div className="users-pagination">
                    <span className="users-pagination-info">
                      Page {usersPage} of {usersTotalPages} ({usersTotal} total)
                    </span>
                    <button
                      type="button"
                      className="users-pagination-btn"
                      disabled={usersPage <= 1 || loading}
                      onClick={() => fetchUsers(usersPage - 1)}
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      className="users-pagination-btn"
                      disabled={usersPage >= usersTotalPages || loading}
                      onClick={() => fetchUsers(usersPage + 1)}
                    >
                      Next
                    </button>
                  </div>
                )}
              </div>
              </>
            )}
          </div>
        )}

        {activeTab === 'users' && activeSubTab === 'activity' && (
          <AdminActivity />
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
            <div className="charts-filters">
              <label>
                <span>Owner name</span>
                <input
                  type="text"
                  placeholder="Search by name"
                  value={chartsSearchName}
                  onChange={(e) => setChartsSearchName(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchCharts(1)}
                />
              </label>
              <label>
                <span>Owner phone</span>
                <input
                  type="text"
                  placeholder="Search by phone"
                  value={chartsSearchPhone}
                  onChange={(e) => setChartsSearchPhone(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && fetchCharts(1)}
                />
              </label>
              <button type="button" className="users-search-btn" onClick={() => fetchCharts(1)}>
                Search
              </button>
            </div>
            {loading ? (
              <div className="loading">Loading charts...</div>
            ) : (
              <>
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
                        <td className="charts-actions-cell">
                          <button
                            type="button"
                            className="share-investigation-btn"
                            onClick={() => handleShareForInvestigation(chart.id)}
                            disabled={sharingChartId === chart.id}
                            title="Share for investigation (copy to all admins)"
                          >
                            {sharingChartId === chart.id ? (
                              <span className="charts-btn-spinner" aria-hidden />
                            ) : (
                              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><path d="m8.59 13.51 6.82 3.98M15.41 6.51l-6.82 3.98"/></svg>
                            )}
                          </button>
                          <button
                            type="button"
                            onClick={() => handleDeleteChart(chart.id)}
                            className="delete-btn"
                            title="Delete chart"
                          >
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M3 6h18"/><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6"/><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2"/><line x1="10" y1="11" x2="10" y2="17"/><line x1="14" y1="11" x2="14" y2="17"/></svg>
                          </button>
                        </td>
                      </tr>
                    ))}
                    </tbody>
                  </table>
                </div>
                {chartsTotalPages > 0 && (
                  <div className="charts-pagination">
                    <span className="charts-pagination-info">
                      Page {chartsPage} of {chartsTotalPages} ({chartsTotal} total)
                    </span>
                    <button
                      type="button"
                      className="charts-pagination-btn"
                      disabled={chartsPage <= 1 || loading}
                      onClick={() => fetchCharts(chartsPage - 1)}
                    >
                      Previous
                    </button>
                    <button
                      type="button"
                      className="charts-pagination-btn"
                      disabled={chartsPage >= chartsTotalPages || loading}
                      onClick={() => fetchCharts(chartsPage + 1)}
                    >
                      Next
                    </button>
                  </div>
                )}
              </>
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
              <p className="credit-settings-hint">Set original price and optional discounted price (credits). VIP columns show auto-calculated price for plan holders (updates as you type).</p>
              <div className="settings-form settings-form-table">
                <table className="feature-costs-table">
                  <thead>
                    <tr>
                      <th className="feature-costs-th-name">Feature</th>
                      <th className="feature-costs-th">Price</th>
                      <th className="feature-costs-th">Discount</th>
                      {vipTiers.map(t => (
                        <th key={t.name} className="feature-costs-th" title={`${t.name}: ${t.discount}% off`}>{t.name}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {creditSettings.map(setting => (
                      <tr key={setting.key}>
                        <td className="feature-costs-td-name" title={setting.key}>{setting.description}</td>
                        <td className="feature-costs-td">
                          <input
                            type="number"
                            value={setting.value}
                            onChange={(e) => handleSettingChange(setting.key, e.target.value)}
                            min="1"
                            placeholder="—"
                            title="Original cost (credits)"
                            aria-label={`${setting.description} price`}
                            className="feature-costs-input"
                          />
                        </td>
                        <td className="feature-costs-td">
                          <input
                            type="number"
                            value={setting.discount ?? ''}
                            onChange={(e) => handleSettingDiscountChange(setting.key, e.target.value)}
                            min="0"
                            placeholder="—"
                            title="Discounted cost (empty = no discount)"
                            aria-label={`${setting.description} discount`}
                            className="feature-costs-input"
                          />
                        </td>
                        {vipTiers.map(t => (
                          <td key={t.name} className="feature-costs-td-vip" title={`${t.name} (${t.discount}% off): ${calcVipPrice(setting.value, t.discount)} credits`}>
                            {calcVipPrice(setting.value, t.discount)}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
                <button onClick={handleUpdateSettings} className="update-settings-btn">
                  Update Costs
                </button>
              </div>
            </div>

            <div className="subscription-plan-discounts credit-settings">
              <h3>Subscription plan discounts</h3>
              <p className="credit-settings-hint">Discount % applied to all feature costs for users on that plan. 0 = full price.</p>
              <div className="settings-form settings-form-table subscription-plan-table">
                <div className="settings-table-header subscription-plan-header">
                  <span className="settings-th-feature">Plan</span>
                  <span className="settings-th-platform">Platform</span>
                  <span className="settings-th-discount">Discount %</span>
                  <span className="settings-th-actions">Actions</span>
                </div>
                {(subscriptionPlans || []).map((plan, index) => {
                  const planId = plan.plan_id ?? plan.id;
                  const rowKey = planId != null ? String(planId) : `plan-${plan.platform}-${plan.tier_name || plan.plan_name || index}-${index}`;
                  const isEditingThis = editingPlanId != null && (planId != null ? editingPlanId == planId : editingPlanId === rowKey);
                  return (
                    <div key={rowKey} className="setting-row subscription-plan-row">
                      <label className="setting-row-label" title={plan.google_play_product_id || ''}>
                        {plan.tier_name || plan.plan_name}
                      </label>
                      <span className="subscription-plan-platform">{plan.platform}</span>
                      <div className="subscription-plan-discount-cell">
                        {isEditingThis ? (
                          <input
                            type="number"
                            min={0}
                            max={100}
                            value={editingPlanDiscount}
                            onChange={(e) => setEditingPlanDiscount(e.target.value)}
                            className="setting-input-small"
                            aria-label={`Discount for ${plan.tier_name || plan.plan_name}`}
                          />
                        ) : (
                          <span>{plan.discount_percent ?? 0}%</span>
                        )}
                      </div>
                      <div className="plan-discount-actions">
                        {isEditingThis ? (
                          <>
                            <button
                              type="button"
                              onClick={() => handleSavePlanDiscount(planId != null ? planId : rowKey)}
                              className="save-btn plan-discount-btn"
                              disabled={savingPlanDiscount}
                            >
                              {savingPlanDiscount ? 'Saving…' : 'Save'}
                            </button>
                            <button
                              type="button"
                              onClick={() => { setEditingPlanId(null); setEditingPlanDiscount(''); }}
                              className="cancel-btn plan-discount-btn"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <button
                            type="button"
                            onClick={() => {
                              setEditingPlanId(planId ?? rowKey);
                              setEditingPlanDiscount(String(plan.discount_percent ?? 0));
                            }}
                            className="edit-btn plan-discount-btn"
                          >
                            Edit
                          </button>
                        )}
                      </div>
                    </div>
                  );
                })}
                {(!subscriptionPlans || subscriptionPlans.length === 0) && (
                  <p className="credit-settings-hint">No subscription plans found. Run backend migration to seed VIP plans.</p>
                )}
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
                              value={editFormData.credits ?? code.credits}
                              onChange={(e) => setEditFormData({...editFormData, credits: parseInt(e.target.value, 10)})}
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
                              value={editFormData.max_uses ?? code.max_uses}
                              onChange={(e) => setEditFormData({...editFormData, max_uses: parseInt(e.target.value, 10)})}
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
                              value={editFormData.max_uses_per_user ?? code.max_uses_per_user}
                              onChange={(e) => setEditFormData({...editFormData, max_uses_per_user: parseInt(e.target.value, 10)})}
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
                              value={
                                editFormData.is_active !== undefined
                                  ? (editFormData.is_active ? '1' : '0')
                                  : (promoCodeIsActive(code.is_active) ? '1' : '0')
                              }
                              onChange={(e) => setEditFormData({ ...editFormData, is_active: e.target.value === '1' })}
                            >
                              <option value="1">Active</option>
                              <option value="0">Inactive</option>
                            </select>
                          ) : (
                            <span className={`status ${promoCodeIsActive(code.is_active) ? 'active' : 'inactive'}`}>
                              {promoCodeIsActive(code.is_active) ? 'Active' : 'Inactive'}
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

        {activeTab === 'credits' && activeSubTab === 'userCredits' && (
          <AdminUserCreditManagement />
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

        {activeTab === 'performance' && activeSubTab === 'list' && (
          <AdminChatPerformance />
        )}
        {activeTab === 'performance' && activeSubTab === 'charts' && (
          <AdminChatPerformanceCharts />
        )}

        {activeTab === 'terms' && (
          <AdminTerms />
        )}

        {activeTab === 'blog' && (
          <BlogDashboard embeddedInAdmin />
        )}

        {activeTab === 'notifications' && (
          <div className="notifications-admin">
            <h2>Notifications</h2>
            <div className="notifications-tabs">
              <button
                type="button"
                className={`sub-tab ${notifSubTab === 'custom' ? 'active' : ''}`}
                onClick={() => setNotifSubTab('custom')}
              >
                Custom notifications
              </button>
              <button
                type="button"
                className={`sub-tab ${notifSubTab === 'blog' ? 'active' : ''}`}
                onClick={() => setNotifSubTab('blog')}
              >
                Blog notifications
              </button>
            </div>

            {notifSubTab === 'custom' && (
              <>
                <p className="notifications-description">
                  Send a custom push notification to selected users. They must have the app installed and have allowed notifications.
                </p>
                <div className="notifications-form">
                  <div className="form-field">
                    <label>Recipients</label>
                    <div className="notif-search-row">
                      <input
                        type="text"
                        placeholder="Search by name (DB search)"
                        value={notifSearchName}
                        onChange={(e) => setNotifSearchName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && fetchUsersForNotifications(1)}
                        className="notif-search-input"
                      />
                      <button type="button" className="notif-search-btn" onClick={() => fetchUsersForNotifications(1)}>
                        Search
                      </button>
                    </div>
                    <div className="notif-user-list">
                      <table className="notif-user-table">
                        <thead>
                          <tr>
                            <th className="notif-th-checkbox">
                              <input
                                type="checkbox"
                                id="notif-select-all"
                                checked={users.length > 0 && users.every((u) => selectedNotifUserIds.includes(u.userid))}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    const pageIds = new Set(users.map((u) => u.userid));
                                    setSelectedNotifUserIds((prev) => [...new Set([...prev, ...pageIds])]);
                                  } else {
                                    const pageIds = new Set(users.map((u) => u.userid));
                                    setSelectedNotifUserIds((prev) => prev.filter((id) => !pageIds.has(id)));
                                  }
                                }}
                              />
                            </th>
                            <th className="notif-th-name">Name</th>
                            <th className="notif-th-phone">Phone</th>
                            <th className="notif-th-notifications">Notifications</th>
                          </tr>
                        </thead>
                        <tbody>
                          {users.map((u) => {
                            const id = u.userid;
                            const checked = selectedNotifUserIds.includes(id);
                            const hasTokens = notifUserIdsWithTokens.includes(id);
                            return (
                              <tr key={id} className="notif-user-row">
                                <td className="notif-td-checkbox">
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={(e) => {
                                      if (e.target.checked) {
                                        setSelectedNotifUserIds((prev) => [...prev, id]);
                                      } else {
                                        setSelectedNotifUserIds((prev) => prev.filter((v) => v !== id));
                                      }
                                    }}
                                  />
                                </td>
                                <td className="notif-td-name">{u.name || 'No name'}</td>
                                <td className="notif-td-phone">{u.phone}</td>
                                <td className="notif-td-notifications">{hasTokens ? 'Yes' : 'No'}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                    {notifTotalPages > 0 && (
                      <div className="notif-pagination">
                        <span className="notif-pagination-info">
                          Page {notifPage} of {notifTotalPages} ({notifTotal} total)
                        </span>
                        <button
                          type="button"
                          className="notif-pagination-btn"
                          disabled={notifPage <= 1 || loading}
                          onClick={() => fetchUsersForNotifications(notifPage - 1)}
                        >
                          Previous
                        </button>
                        <button
                          type="button"
                          className="notif-pagination-btn"
                          disabled={notifPage >= notifTotalPages || loading}
                          onClick={() => fetchUsersForNotifications(notifPage + 1)}
                        >
                          Next
                        </button>
                      </div>
                    )}
                    <div className="notif-user-summary">{selectedNotifUserIds.length} selected</div>
                    <small className="form-hint">
                      Only users with registered device tokens will actually receive a push notification.
                    </small>
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
                      disabled={loading || selectedNotifUserIds.length !== 1}
                    >
                      <option value="">Any — use user&apos;s current selection</option>
                      {(charts || [])
                        .filter((c) => Number(c.userid) === Number(selectedNotifUserIds[0]))
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
                      disabled={notifSending || selectedNotifUserIds.length === 0 || !notifTitle.trim() || !notifBody.trim()}
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
              </>
            )}

            {notifSubTab === 'blog' && (
              <>
                <p className="notifications-description">
                  Send a notification for a published blog post. The blog&apos;s title and image will be used in the notification.
                </p>
                <div className="notifications-form">
                  <div className="form-field">
                    <label>Recipients</label>
                    <div className="notif-search-row">
                      <input
                        type="text"
                        placeholder="Search by name (DB search)"
                        value={notifSearchName}
                        onChange={(e) => setNotifSearchName(e.target.value)}
                        onKeyDown={(e) => e.key === 'Enter' && fetchUsersForNotifications(1)}
                        className="notif-search-input"
                      />
                      <button type="button" className="notif-search-btn" onClick={() => fetchUsersForNotifications(1)}>
                        Search
                      </button>
                    </div>
                    <div className="notif-user-list">
                      <table className="notif-user-table">
                        <thead>
                          <tr>
                            <th className="notif-th-checkbox">
                              <input
                                type="checkbox"
                                id="blog-notif-select-all"
                                checked={users.length > 0 && users.every((u) => selectedBlogNotifUserIds.includes(u.userid))}
                                onChange={(e) => {
                                  if (e.target.checked) {
                                    const pageIds = new Set(users.map((u) => u.userid));
                                    setSelectedBlogNotifUserIds((prev) => [...new Set([...prev, ...pageIds])]);
                                  } else {
                                    const pageIds = new Set(users.map((u) => u.userid));
                                    setSelectedBlogNotifUserIds((prev) => prev.filter((id) => !pageIds.has(id)));
                                  }
                                }}
                              />
                            </th>
                            <th className="notif-th-name">Name</th>
                            <th className="notif-th-phone">Phone</th>
                          </tr>
                        </thead>
                        <tbody>
                          {users.map((u) => {
                            const id = u.userid;
                            const checked = selectedBlogNotifUserIds.includes(id);
                            return (
                              <tr key={id} className="notif-user-row">
                                <td className="notif-td-checkbox">
                                  <input
                                    type="checkbox"
                                    checked={checked}
                                    onChange={(e) => {
                                      if (e.target.checked) {
                                        setSelectedBlogNotifUserIds((prev) => [...prev, id]);
                                      } else {
                                        setSelectedBlogNotifUserIds((prev) => prev.filter((v) => v !== id));
                                      }
                                    }}
                                  />
                                </td>
                                <td className="notif-td-name">{u.name || 'No name'}</td>
                                <td className="notif-td-phone">{u.phone}</td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                    {notifTotalPages > 0 && (
                      <div className="notif-pagination">
                        <span className="notif-pagination-info">
                          Page {notifPage} of {notifTotalPages} ({notifTotal} total)
                        </span>
                        <button
                          type="button"
                          className="notif-pagination-btn"
                          disabled={notifPage <= 1 || loading}
                          onClick={() => fetchUsersForNotifications(notifPage - 1)}
                        >
                          Previous
                        </button>
                        <button
                          type="button"
                          className="notif-pagination-btn"
                          disabled={notifPage >= notifTotalPages || loading}
                          onClick={() => fetchUsersForNotifications(notifPage + 1)}
                        >
                          Next
                        </button>
                      </div>
                    )}
                    <div className="notif-user-summary">{selectedBlogNotifUserIds.length} selected</div>
                    <small className="form-hint">
                      If no users are selected, the notification will be sent based on the audience setting below.
                    </small>
                  </div>
                  <div className="form-field">
                    <label>Blog post</label>
                    <select
                      value={blogNotifSelectedId}
                      onChange={(e) => setBlogNotifSelectedId(e.target.value)}
                      disabled={!blogPosts.length}
                    >
                      <option value="">Select blog…</option>
                      {blogPosts
                        .filter((p) => p.status === 'published')
                        .map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.title}
                          </option>
                        ))}
                    </select>
                    <small className="form-hint">
                      Only published blog posts are shown. Manage blogs in the Blog tab.
                    </small>
                  </div>
                  <div className="form-field">
                    <label>Audience</label>
                    <select
                      value={blogNotifAudience}
                      onChange={(e) => setBlogNotifAudience(e.target.value)}
                    >
                      <option value="all">All users</option>
                      <option value="eligible">Only users with registered push tokens</option>
                    </select>
                  </div>
                  <div className="form-buttons">
                    <button
                      type="button"
                      onClick={handleSendBlogNotification}
                      disabled={blogNotifSending || !blogNotifSelectedId}
                      className="create-btn"
                    >
                      {blogNotifSending ? 'Sending…' : 'Send Blog Notification'}
                    </button>
                  </div>
                </div>
                {blogNotifResult && (
                  <div className={`notif-result ${blogNotifResult.ok ? 'success' : 'error'}`}>
                    <strong>{blogNotifResult.message}</strong>
                  </div>
                )}
              </>
            )}
          </div>
        )}

        {activeTab === 'reddit' && (
          <div className="admin-settings">
            <h2>Reddit Outreach</h2>
            <div className="settings-section">
              <h3>Collect questions</h3>
              <p className="settings-hint">
                Fetch recent posts from astrology subreddits (last 7 days). Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in backend .env.
              </p>
              <div className="form-buttons" style={{ marginBottom: 12 }}>
                <button type="button" className="create-btn" onClick={runRedditCollect} disabled={redditCollecting}>
                  {redditCollecting ? 'Collecting…' : 'Run collector (last 7 days)'}
                </button>
              </div>
              {redditCollectResult && (
                <div style={{ padding: 12, background: redditCollectResult.error ? '#fff0f0' : '#f0f8f0', borderRadius: 8, marginTop: 8 }}>
                  {redditCollectResult.error ? (
                    <strong>Error:</strong>
                  ) : null}
                  {redditCollectResult.error ? ` ${redditCollectResult.error}` : null}
                  {redditCollectResult.ok && (
                    <>Collected {redditCollectResult.collected} posts, {redditCollectResult.with_birth_data} with birth data.</>
                  )}
                </div>
              )}
            </div>
            <div className="settings-section">
              <h3>Draft answers (human review)</h3>
              <p className="settings-hint">Review and approve or reject draft answers before they are posted to Reddit.</p>
              {redditDraftsLoading ? (
                <p>Loading drafts…</p>
              ) : redditDrafts.length === 0 ? (
                <p>No draft answers to review.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
                  {redditDrafts.map((d) => (
                    <div key={d.answer_id} style={{ border: '1px solid #ddd', borderRadius: 8, padding: 16, background: '#fafafa' }}>
                      <div style={{ marginBottom: 12 }}>
                        <strong>r/{d.subreddit}</strong>
                        {d.url && (
                          <a href={d.url} target="_blank" rel="noopener noreferrer" style={{ marginLeft: 8 }}>Open post</a>
                        )}
                      </div>
                      <div style={{ marginBottom: 8 }}>
                        <strong>Question:</strong>
                        <div style={{ whiteSpace: 'pre-wrap', marginTop: 4, padding: 8, background: '#fff', borderRadius: 4 }}>{d.title || '(no title)'}{(d.body || '').slice(0, 500)}{(d.body && d.body.length > 500) ? '…' : ''}</div>
                      </div>
                      <div style={{ marginBottom: 12 }}>
                        <strong>Draft answer:</strong>
                        {redditEditingId === d.answer_id ? (
                          <div style={{ marginTop: 4 }}>
                            <textarea
                              value={redditEditMarkdown}
                              onChange={(e) => setRedditEditMarkdown(e.target.value)}
                              rows={8}
                              style={{ width: '100%', padding: 8, borderRadius: 4 }}
                            />
                            <div style={{ marginTop: 8 }}>
                              <button type="button" className="create-btn" onClick={() => approveRedditAnswer(d.answer_id, redditEditMarkdown)}>Approve &amp; save</button>
                              <button type="button" style={{ marginLeft: 8 }} onClick={() => { setRedditEditingId(null); setRedditEditMarkdown(''); }}>Cancel</button>
                            </div>
                          </div>
                        ) : (
                          <div style={{ whiteSpace: 'pre-wrap', marginTop: 4, padding: 8, background: '#fff', borderRadius: 4 }}>{(d.draft_markdown || '').slice(0, 1500)}{(d.draft_markdown && d.draft_markdown.length > 1500) ? '…' : ''}</div>
                        )}
                      </div>
                      {redditEditingId !== d.answer_id && (
                        <div>
                          <button type="button" className="create-btn" onClick={() => { setRedditEditingId(d.answer_id); setRedditEditMarkdown(d.draft_markdown || ''); }}>Edit &amp; approve</button>
                          <button type="button" style={{ marginLeft: 8 }} onClick={() => rejectRedditAnswer(d.answer_id)}>Reject</button>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'settings' && (
          <div className="admin-settings">
            <h2>System Settings</h2>

            <div className="settings-section">
              <h3>Gemini Models</h3>
              <p className="settings-hint">
                Choose which Gemini models to use. Chat (standard/premium) for conversations; Analysis for health, wealth, career, karma, physical, events, etc. Changes apply to new requests immediately.
              </p>
              <div className="setting-item">
                <div className="setting-info">
                  <strong>Chat model (standard)</strong>
                  <p>Model for standard astrological chat.</p>
                </div>
                <select
                  value={geminiChatModel}
                  onChange={(e) => setGeminiChatModel(e.target.value)}
                  style={{ minWidth: '280px' }}
                >
                  {geminiModelOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div className="setting-item">
                <div className="setting-info">
                  <strong>Chat model (premium)</strong>
                  <p>Model for premium / deeper chat analysis.</p>
                </div>
                <select
                  value={geminiPremiumModel}
                  onChange={(e) => setGeminiPremiumModel(e.target.value)}
                  style={{ minWidth: '280px' }}
                >
                  {geminiModelOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div className="setting-item">
                <div className="setting-info">
                  <strong>Analysis model</strong>
                  <p>Model for health, wealth, career, karma, physical, event predictor, blank chart, ashtakavarga, fact extraction, etc.</p>
                </div>
                <select
                  value={geminiAnalysisModel}
                  onChange={(e) => setGeminiAnalysisModel(e.target.value)}
                  style={{ minWidth: '280px' }}
                >
                  {geminiModelOptions.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
              </div>
              <div className="form-buttons" style={{ marginTop: '12px' }}>
                <button type="button" className="create-btn" onClick={handleSaveGeminiModels} disabled={geminiModelsSaving}>
                  {geminiModelsSaving ? 'Saving…' : 'Save Gemini Models'}
                </button>
              </div>
            </div>
            
            <div className="settings-section">
              <h3>Podcast provider</h3>
              <p className="settings-hint">
                When a user requests a podcast and it is not cached, the app uses this method to generate it.
                TTS: Gemini script + Google Text-to-Speech. Notebook LM: Discovery Engine Podcast API (full message as context, no script step).
              </p>
              <div className="setting-item">
                <div className="setting-info">
                  <strong>Provider</strong>
                  <p>Choose which backend to use for new podcast generation.</p>
                </div>
                <select
                  value={podcastProvider}
                  onChange={(e) => setPodcastProvider(e.target.value)}
                  style={{ minWidth: '220px' }}
                >
                  <option value="tts">TTS (Gemini script + Google TTS)</option>
                  <option value="notebook_lm">Notebook LM (Discovery Engine API)</option>
                </select>
              </div>
              <div className="form-buttons" style={{ marginTop: '12px' }}>
                <button type="button" className="create-btn" onClick={async () => {
                  setPodcastProviderSaving(true);
                  try {
                    const res = await fetch('/api/admin/settings/podcast_provider', {
                      method: 'PUT',
                      headers: { ...getAdminAuthHeaders(), 'Content-Type': 'application/json' },
                      body: JSON.stringify({
                        key: 'podcast_provider',
                        value: podcastProvider,
                        description: 'Podcast generation: tts or notebook_lm',
                      }),
                    });
                    if (!res.ok) {
                      const err = await res.json().catch(() => ({}));
                      alert('Failed to save: ' + (err.detail || res.status));
                      return;
                    }
                    alert('Podcast provider saved. New podcast requests will use the selected method.');
                  } catch (e) {
                    console.error(e);
                    alert('Failed to save podcast provider.');
                  } finally {
                    setPodcastProviderSaving(false);
                  }
                }} disabled={podcastProviderSaving}>
                  {podcastProviderSaving ? 'Saving…' : 'Save podcast provider'}
                </button>
              </div>
            </div>

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

            <div className="settings-section">
              <h3>Admin device allowlist</h3>
              <p className="settings-hint">
                Devices are bound to your account: only you can use devices you register. Add this device with one click, or add another device&apos;s ID manually (e.g. from another browser). Empty list = any device allowed (bootstrap).
              </p>
              <p className="allowed-device-id">
                <strong>This device ID:</strong> <code>{getDeviceId()}</code>
                <button
                  type="button"
                  className="register-this-device-btn small"
                  style={{ marginLeft: '12px' }}
                  onClick={async () => {
                    try {
                      await adminService.registerThisDevice();
                      await fetchAllowedDevices();
                    } catch (e) {
                      alert(e.message || 'Failed to register');
                    }
                  }}
                >
                  Register this device
                </button>
              </p>
              {allowedDevicesLoading ? (
                <p>Loading…</p>
              ) : (
                <>
                  <table className="allowed-devices-table">
                    <thead>
                      <tr>
                        <th>Device ID</th>
                        <th>Label</th>
                        <th>Added</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {allowedDevices.length === 0 ? (
                        <tr><td colSpan={4}>No devices in allowlist. Add one below or via DB.</td></tr>
                      ) : (
                        allowedDevices.map((d) => (
                          <tr key={d.id}>
                            <td><code className="device-id-cell">{d.device_id}</code></td>
                            <td>{d.label || '—'}</td>
                            <td>{d.created_at || '—'}</td>
                            <td>
                              <button
                                type="button"
                                className="delete-btn small"
                                onClick={async () => {
                                  try {
                                    await adminService.removeAllowedDeviceById(d.id);
                                    await fetchAllowedDevices();
                                  } catch (e) {
                                    alert(e.message || 'Failed to remove');
                                  }
                                }}
                              >
                                Remove
                              </button>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                  <div className="allowed-devices-add">
                    <label>
                      <span>Device ID:</span>
                      <input
                        type="text"
                        value={newAllowedDeviceId}
                        onChange={(e) => setNewAllowedDeviceId(e.target.value)}
                        placeholder="e.g. web-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                        style={{ width: '320px', marginLeft: '8px' }}
                      />
                    </label>
                    <label style={{ marginLeft: '12px' }}>
                      <span>For user ID (blank = you):</span>
                      <input
                        type="text"
                        inputMode="numeric"
                        value={newAllowedDeviceForUserId}
                        onChange={(e) => setNewAllowedDeviceForUserId(e.target.value)}
                        placeholder="Other admin's user ID"
                        style={{ width: '100px', marginLeft: '8px' }}
                      />
                    </label>
                    <label style={{ marginLeft: '12px' }}>
                      <span>Label (optional):</span>
                      <input
                        type="text"
                        value={newAllowedDeviceLabel}
                        onChange={(e) => setNewAllowedDeviceLabel(e.target.value)}
                        placeholder="e.g. Office laptop"
                        style={{ width: '140px', marginLeft: '8px' }}
                      />
                    </label>
                    <button
                      type="button"
                      className="create-btn"
                      style={{ marginLeft: '12px' }}
                      disabled={!newAllowedDeviceId.trim()}
                      onClick={async () => {
                        try {
                          const forId = newAllowedDeviceForUserId.trim() ? newAllowedDeviceForUserId.trim() : null;
                          await adminService.addAllowedDevice(newAllowedDeviceId.trim(), newAllowedDeviceLabel.trim() || undefined, forId);
                          setNewAllowedDeviceId('');
                          setNewAllowedDeviceLabel('');
                          setNewAllowedDeviceForUserId('');
                          await fetchAllowedDevices();
                        } catch (e) {
                          alert(e.message || 'Failed to add device');
                        }
                      }}
                    >
                      Add device
                    </button>
                  </div>
                </>
              )}
            </div>
          </div>
        )}
      </div>
      </>
      )}
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
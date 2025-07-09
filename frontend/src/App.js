import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios defaults
axios.defaults.baseURL = API;

// =================== CONTEXTS ===================

// Auth Context
const AuthContext = React.createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [userType, setUserType] = useState(null); // 'client' or 'admin'
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const storedUserType = localStorage.getItem('userType');
    if (token && storedUserType) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      setUserType(storedUserType);
      fetchUserProfile(storedUserType);
    } else {
      setLoading(false);
    }
  }, []);

  const fetchUserProfile = async (type) => {
    try {
      const endpoint = type === 'admin' ? '/admin/auth/me' : '/auth/me';
      const response = await axios.get(endpoint);
      setUser(response.data);
    } catch (error) {
      console.error('Error fetching user profile:', error);
      localStorage.removeItem('token');
      localStorage.removeItem('userType');
      delete axios.defaults.headers.common['Authorization'];
    } finally {
      setLoading(false);
    }
  };

  const login = async (email, password, type = 'client') => {
    try {
      const endpoint = type === 'admin' ? '/admin/auth/login' : '/auth/login';
      const response = await axios.post(endpoint, { email, password });
      const { access_token } = response.data;
      
      localStorage.setItem('token', access_token);
      localStorage.setItem('userType', type);
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`;
      
      setUserType(type);
      await fetchUserProfile(type);
      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('userType');
    delete axios.defaults.headers.common['Authorization'];
    setUser(null);
    setUserType(null);
  };

  return (
    <AuthContext.Provider value={{ user, userType, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  );
};

// Toast Notification Context
const ToastContext = React.createContext();

const ToastProvider = ({ children }) => {
  const [toasts, setToasts] = useState([]);

  const addToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(toast => toast.id !== id));
    }, 3000);
  };

  const removeToast = (id) => {
    setToasts(prev => prev.filter(toast => toast.id !== id));
  };

  return (
    <ToastContext.Provider value={{ addToast, removeToast }}>
      {children}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div
            key={toast.id}
            className={`px-4 py-2 rounded-md shadow-md text-white ${
              toast.type === 'success' ? 'bg-green-500' : 'bg-red-500'
            }`}
          >
            {toast.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
};

// =================== ROUTING LOGIC ===================

const AppRouter = () => {
  const { userType, loading } = React.useContext(AuthContext);
  
  // Determine if user is accessing admin area
  const isAdminPath = window.location.pathname.startsWith('/admin');
  
  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading...</p>
        </div>
      </div>
    );
  }

  // If accessing admin area
  if (isAdminPath) {
    if (!userType || userType !== 'admin') {
      return <AdminLogin />;
    }
    return <AdminDashboard />;
  }

  // If accessing client area
  if (!userType || userType !== 'client') {
    return <ClientLogin />;
  }
  return <ClientApp />;
};

// =================== LOGIN COMPONENTS ===================

// Client Login Component (existing)
const ClientLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = React.useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const success = await login(email, password, 'client');
    if (!success) {
      setError('Invalid email or password');
    }
    setLoading(false);
  };

  const handleDemoLogin = async () => {
    setLoading(true);
    // First seed demo data
    try {
      await axios.post('/seed');
    } catch (err) {
      console.log('Demo data might already exist');
    }
    
    const success = await login('demo@take2studio.com', 'demo123', 'client');
    if (!success) {
      setError('Demo login failed');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900">Take 2 Studio</h1>
          <p className="mt-2 text-sm text-gray-600">Client Portal</p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                Email address
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            {error && (
              <div className="text-red-600 text-sm">{error}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-300" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or</span>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <button
                onClick={handleDemoLogin}
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                Try Demo Account
              </button>
              <a
                href="/admin"
                className="w-full flex justify-center py-2 px-4 border border-blue-300 rounded-md shadow-sm text-sm font-medium text-blue-700 bg-blue-50 hover:bg-blue-100 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Admin Login
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Admin Login Component (new)
const AdminLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { login } = React.useContext(AuthContext);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const success = await login(email, password, 'admin');
    if (!success) {
      setError('Invalid admin credentials');
    }
    setLoading(false);
  };

  const handleDemoAdminLogin = async () => {
    setLoading(true);
    // First seed demo data
    try {
      await axios.post('/seed');
    } catch (err) {
      console.log('Demo data might already exist');
    }
    
    const success = await login('admin@take2studio.com', 'admin123', 'admin');
    if (!success) {
      setError('Demo admin login failed');
    }
    setLoading(false);
  };

  return (
    <div className="min-h-screen bg-gray-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white">Take 2 Studio</h1>
          <p className="mt-2 text-sm text-gray-300">Admin Dashboard</p>
        </div>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
        <div className="bg-gray-800 py-8 px-4 shadow sm:rounded-lg sm:px-10">
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-300">
                Admin Email
              </label>
              <div className="mt-1">
                <input
                  id="email"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 bg-gray-700 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-300">
                Password
              </label>
              <div className="mt-1">
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none block w-full px-3 py-2 border border-gray-600 rounded-md shadow-sm placeholder-gray-400 bg-gray-700 text-white focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                />
              </div>
            </div>

            {error && (
              <div className="text-red-400 text-sm">{error}</div>
            )}

            <div>
              <button
                type="submit"
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                {loading ? 'Signing in...' : 'Sign in'}
              </button>
            </div>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-600" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-gray-800 text-gray-400">Or</span>
              </div>
            </div>

            <div className="mt-6 space-y-3">
              <button
                onClick={handleDemoAdminLogin}
                disabled={loading}
                className="w-full flex justify-center py-2 px-4 border border-gray-600 rounded-md shadow-sm text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
              >
                Try Demo Admin
              </button>
              <a
                href="/"
                className="w-full flex justify-center py-2 px-4 border border-blue-600 rounded-md shadow-sm text-sm font-medium text-blue-400 bg-blue-900 hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Client Portal
              </a>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// =================== ADMIN DASHBOARD ===================

const AdminDashboard = () => {
  const { user, logout } = React.useContext(AuthContext);
  const { addToast } = React.useContext(ToastContext);
  const [currentPage, setCurrentPage] = useState('overview');
  const [dashboardStats, setDashboardStats] = useState(null);
  const [clients, setClients] = useState([]);
  const [materials, setMaterials] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, clientsRes, materialsRes, campaignsRes] = await Promise.all([
        axios.get('/admin/dashboard/stats'),
        axios.get('/admin/clients'),
        axios.get('/admin/materials'),
        axios.get('/admin/campaigns')
      ]);
      
      setDashboardStats(statsRes.data);
      setClients(clientsRes.data);
      setMaterials(materialsRes.data);
      setCampaigns(campaignsRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      addToast('Error loading dashboard data', 'error');
    } finally {
      setLoading(false);
    }
  };

  const renderPage = () => {
    switch (currentPage) {
      case 'clients':
        return <AdminClientsPage clients={clients} onRefresh={fetchDashboardData} />;
      case 'materials':
        return <AdminMaterialsPage materials={materials} clients={clients} onRefresh={fetchDashboardData} />;
      case 'campaigns':
        return <AdminCampaignsPage campaigns={campaigns} clients={clients} onRefresh={fetchDashboardData} />;
      case 'documents':
        return <AdminDocumentsPage documents={documents} clients={clients} onRefresh={fetchDashboardData} />;
      case 'calendar':
        return <AdminCalendarPage materials={materials} campaigns={campaigns} />;
      default:
        return <AdminOverviewPage stats={dashboardStats} clients={clients} materials={materials} campaigns={campaigns} />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading admin dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <div className="w-64 bg-gray-900 text-white">
        <div className="p-4">
          <h1 className="text-xl font-bold">Take 2 Studio</h1>
          <p className="text-sm text-gray-400">Admin Dashboard</p>
        </div>
        
        <nav className="mt-8">
          {[
            { id: 'overview', label: 'Overview', icon: '🏠' },
            { id: 'clients', label: 'Clientes', icon: '👥' },
            { id: 'materials', label: 'Materiais', icon: '🎬' },
            { id: 'campaigns', label: 'Campanhas', icon: '📊' },
            { id: 'documents', label: 'Documentos', icon: '📁' },
            { id: 'calendar', label: 'Calendário', icon: '📅' }
          ].map(item => (
            <button
              key={item.id}
              onClick={() => setCurrentPage(item.id)}
              className={`w-full flex items-center px-4 py-3 text-left hover:bg-gray-800 ${
                currentPage === item.id ? 'bg-gray-800 border-r-2 border-blue-500' : ''
              }`}
            >
              <span className="mr-3">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
        
        <div className="absolute bottom-4 left-4 right-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium">{user?.name}</p>
              <p className="text-xs text-gray-400">{user?.role}</p>
            </div>
            <button
              onClick={logout}
              className="text-gray-400 hover:text-white"
              title="Logout"
            >
              🚪
            </button>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">
        {renderPage()}
      </div>
    </div>
  );
};

// Admin Overview Page
const AdminOverviewPage = ({ stats, clients, materials, campaigns }) => {
  const pendingApprovals = materials.filter(m => m.status === 'awaiting_approval');
  const recentMaterials = materials.slice(0, 5);
  const activeCampaigns = campaigns.filter(c => c.status === 'active');

  return (
    <div className="p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Dashboard Overview</h1>
        <p className="mt-2 text-gray-600">Manage all your clients and projects</p>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-blue-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">👥</span>
              </div>
            </div>
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Clientes Ativos</div>
              <div className="text-2xl font-bold text-gray-900">{stats?.active_clients || 0}</div>
              <div className="text-xs text-gray-500">de {stats?.total_clients || 0} total</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-orange-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">⏳</span>
              </div>
            </div>
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Aguardando Aprovação</div>
              <div className="text-2xl font-bold text-gray-900">{stats?.pending_approvals || 0}</div>
              <div className="text-xs text-gray-500">materiais pendentes</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">📊</span>
              </div>
            </div>
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Campanhas Ativas</div>
              <div className="text-2xl font-bold text-gray-900">{stats?.active_campaigns || 0}</div>
              <div className="text-xs text-gray-500">em execução</div>
            </div>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className="w-8 h-8 bg-purple-500 rounded-lg flex items-center justify-center">
                <span className="text-white text-sm">🎬</span>
              </div>
            </div>
            <div className="ml-4">
              <div className="text-sm font-medium text-gray-500">Total Materiais</div>
              <div className="text-2xl font-bold text-gray-900">{stats?.total_materials || 0}</div>
              <div className="text-xs text-gray-500">todos os clientes</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Pending Approvals */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Aprovações Pendentes</h3>
              <p className="mt-1 text-sm text-gray-500">Materiais aguardando aprovação dos clientes</p>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {pendingApprovals.length > 0 ? (
                  pendingApprovals.map((material) => (
                    <div key={material.id} className="flex items-center justify-between p-4 bg-orange-50 rounded-lg">
                      <div className="flex items-center">
                        {material.file_url && (
                          <img
                            src={material.file_url}
                            alt={material.title}
                            className="h-12 w-12 rounded-lg object-cover mr-4"
                          />
                        )}
                        <div>
                          <p className="font-medium text-gray-900">{material.title}</p>
                          <p className="text-sm text-gray-600">{material.client_name}</p>
                          <p className="text-xs text-gray-500">
                            Agendado: {new Date(material.scheduled_date).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-orange-100 text-orange-800">
                          Aguardando Aprovação
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="text-center py-8">
                    <p className="text-gray-500">Nenhuma aprovação pendente</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Recent Activity */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Atividade Recente</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {recentMaterials.map((material) => (
                  <div key={material.id} className="flex items-start">
                    <div className="flex-shrink-0">
                      <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 text-xs">🎬</span>
                      </div>
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">{material.title}</p>
                      <p className="text-xs text-gray-600">{material.client_name}</p>
                      <p className="text-xs text-gray-500">
                        {new Date(material.created_at).toLocaleDateString()}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Active Campaigns Summary */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Campanhas Ativas</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {activeCampaigns.slice(0, 3).map((campaign) => (
                  <div key={campaign.id} className="border-l-4 border-green-400 pl-4">
                    <p className="font-medium text-gray-900">{campaign.name}</p>
                    <p className="text-sm text-gray-600">{campaign.client_name}</p>
                    <div className="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                      <span>CTR: {campaign.ctr}%</span>
                      <span>Gasto: R$ {campaign.spend.toFixed(2)}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Admin Clients Page
const AdminClientsPage = ({ clients, onRefresh }) => {
  const { addToast } = React.useContext(ToastContext);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredClients = clients.filter(client =>
    client.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreateClient = async (clientData) => {
    try {
      await axios.post('/admin/clients', clientData);
      addToast('Cliente criado com sucesso!');
      setShowCreateForm(false);
      onRefresh();
    } catch (error) {
      console.error('Error creating client:', error);
      addToast('Erro ao criar cliente', 'error');
    }
  };

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestão de Clientes</h1>
          <p className="mt-2 text-gray-600">Gerencie todos os clientes da agência</p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
        >
          <span className="mr-2">+</span>
          Novo Cliente
        </button>
      </div>

      {/* Search */}
      <div className="mb-6">
        <div className="relative">
          <input
            type="text"
            placeholder="Buscar clientes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          <svg className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
      </div>

      {/* Clients List */}
      <div className="space-y-4">
        {filteredClients.map((client) => (
          <div key={client.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <span className="text-blue-600 font-bold text-lg">
                      {client.name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                </div>
                <div className="ml-4">
                  <h3 className="text-lg font-medium text-gray-900">{client.name}</h3>
                  <p className="text-sm text-gray-600">Projeto: {client.current_project}</p>
                  <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                    <span>Materiais: {client.materials_count}</span>
                    <span>Aprovações: {client.pending_approvals}</span>
                    <span>Campanhas: {client.active_campaigns}</span>
                  </div>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                  client.status === 'active' ? 'bg-green-100 text-green-800' : 
                  client.status === 'paused' ? 'bg-yellow-100 text-yellow-800' : 
                  'bg-gray-100 text-gray-800'
                }`}>
                  {client.status === 'active' ? '🟢 Ativo' : 
                   client.status === 'paused' ? '🟡 Em Pausa' : 
                   '⚫ Concluído'}
                </span>
                <button className="text-blue-600 hover:text-blue-800 text-sm font-medium">
                  👁️ Ver Portal
                </button>
                <button className="text-gray-600 hover:text-gray-800 text-sm font-medium">
                  ✏️ Editar
                </button>
                <button className="text-gray-600 hover:text-gray-800 text-sm font-medium">
                  📊 Relatório
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Create Client Modal */}
      {showCreateForm && (
        <CreateClientModal
          onClose={() => setShowCreateForm(false)}
          onSubmit={handleCreateClient}
        />
      )}
    </div>
  );
};

// Material Upload Modal
const MaterialUploadModal = ({ onClose, onSubmit, clients }) => {
  const [formData, setFormData] = useState({
    client_id: '',
    title: '',
    description: '',
    type: 'photo',
    scheduled_date: '',
    file_url: '',
    tags: []
  });
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [tagInput, setTagInput] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.client_id || !formData.title || !formData.scheduled_date) {
      alert('Por favor, preencha todos os campos obrigatórios');
      return;
    }

    setUploading(true);
    
    // Simulate file upload - in real app, would upload to storage service
    let fileUrl = formData.file_url;
    if (file) {
      // Create a temporary URL for demo purposes
      fileUrl = URL.createObjectURL(file);
    }

    const materialData = {
      ...formData,
      file_url: fileUrl,
      scheduled_date: new Date(formData.scheduled_date).toISOString(),
      tags: formData.tags.filter(tag => tag.trim() !== '')
    };

    try {
      await onSubmit(materialData);
    } catch (error) {
      console.error('Error uploading material:', error);
    } finally {
      setUploading(false);
    }
  };

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setFormData(prev => ({ ...prev, file_url: URL.createObjectURL(selectedFile) }));
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      setFile(droppedFile);
      setFormData(prev => ({ ...prev, file_url: URL.createObjectURL(droppedFile) }));
    }
  };

  const handleAddTag = (e) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim().replace('#', '');
      if (!formData.tags.includes(newTag)) {
        setFormData(prev => ({
          ...prev,
          tags: [...prev.tags, newTag]
        }));
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">Upload de Material</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Client Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Cliente *
              </label>
              <select
                value={formData.client_id}
                onChange={(e) => setFormData(prev => ({ ...prev, client_id: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                required
              >
                <option value="">Selecione um cliente</option>
                {clients.map(client => (
                  <option key={client.id} value={client.id}>
                    {client.name}
                  </option>
                ))}
              </select>
            </div>

            {/* Material Type */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tipo de Material
              </label>
              <div className="flex space-x-4">
                {[
                  { value: 'photo', label: 'Foto', icon: '📷' },
                  { value: 'video', label: 'Vídeo', icon: '🎬' },
                  { value: 'carousel', label: 'Carrossel', icon: '🔄' },
                  { value: 'story', label: 'Stories', icon: '📱' }
                ].map(type => (
                  <label key={type.value} className="flex items-center cursor-pointer">
                    <input
                      type="radio"
                      name="type"
                      value={type.value}
                      checked={formData.type === type.value}
                      onChange={(e) => setFormData(prev => ({ ...prev, type: e.target.value }))}
                      className="mr-2"
                    />
                    <span>{type.icon} {type.label}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* File Upload */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Arquivo
              </label>
              <div
                className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                  dragOver ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-gray-400'
                }`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => document.getElementById('file-input').click()}
              >
                <input
                  id="file-input"
                  type="file"
                  accept="image/*,video/*"
                  onChange={handleFileChange}
                  className="hidden"
                />
                
                {formData.file_url ? (
                  <div className="space-y-2">
                    <img
                      src={formData.file_url}
                      alt="Preview"
                      className="max-h-32 mx-auto rounded-lg"
                    />
                    <p className="text-sm text-gray-600">Arquivo selecionado</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center mx-auto">
                      <span className="text-2xl">📎</span>
                    </div>
                    <p className="text-gray-600">Arraste arquivo aqui ou clique</p>
                    <p className="text-sm text-gray-500">JPG, PNG, MP4, etc. (máx 100MB)</p>
                  </div>
                )}
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Título *
              </label>
              <input
                type="text"
                value={formData.title}
                onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: Post Instagram - Promoção Janeiro"
                required
              />
            </div>

            {/* Scheduled Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Data de Publicação *
              </label>
              <input
                type="datetime-local"
                value={formData.scheduled_date}
                onChange={(e) => setFormData(prev => ({ ...prev, scheduled_date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                required
              />
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Legenda
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                rows="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Legenda do post, roteiro, ou descrição detalhada..."
              />
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Tags
              </label>
              <div className="flex flex-wrap gap-2 mb-2">
                {formData.tags.map((tag, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                  >
                    #{tag}
                    <button
                      type="button"
                      onClick={() => handleRemoveTag(tag)}
                      className="ml-1 text-blue-600 hover:text-blue-800"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
              <input
                type="text"
                value={tagInput}
                onChange={(e) => setTagInput(e.target.value)}
                onKeyDown={handleAddTag}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Digite uma tag e pressione Enter"
              />
            </div>

            {/* Submit Buttons */}
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                disabled={uploading}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300 disabled:opacity-50"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={uploading}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
              >
                {uploading ? 'Enviando...' : 'Salvar'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Material Preview/Edit Modal
const MaterialPreviewEditModal = ({ material, onClose, onSubmit, clients }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [formData, setFormData] = useState({
    client_id: material.client_id,
    title: material.title,
    description: material.description,
    type: material.type,
    scheduled_date: material.scheduled_date ? material.scheduled_date.split('T')[0] + 'T' + material.scheduled_date.split('T')[1].slice(0, 5) : '',
    status: material.status,
    tags: material.tags || []
  });
  const [tagInput, setTagInput] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    const updateData = {
      ...formData,
      scheduled_date: new Date(formData.scheduled_date).toISOString()
    };

    try {
      await onSubmit(material.id, updateData);
      setIsEditing(false);
    } catch (error) {
      console.error('Error updating material:', error);
    }
  };

  const handleAddTag = (e) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      const newTag = tagInput.trim().replace('#', '');
      if (!formData.tags.includes(newTag)) {
        setFormData(prev => ({
          ...prev,
          tags: [...prev.tags, newTag]
        }));
      }
      setTagInput('');
    }
  };

  const handleRemoveTag = (tagToRemove) => {
    setFormData(prev => ({
      ...prev,
      tags: prev.tags.filter(tag => tag !== tagToRemove)
    }));
  };

  const getStatusColor = (status) => {
    const colors = {
      planned: 'bg-yellow-100 text-yellow-800',
      in_production: 'bg-blue-100 text-blue-800',
      awaiting_approval: 'bg-orange-100 text-orange-800',
      approved: 'bg-green-100 text-green-800',
      revision_requested: 'bg-red-100 text-red-800',
      published: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-center mb-6">
            <h2 className="text-xl font-semibold text-gray-900">
              {isEditing ? 'Editar Material' : 'Preview do Material'}
            </h2>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => setIsEditing(!isEditing)}
                className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                {isEditing ? 'Cancelar Edição' : 'Editar'}
              </button>
              <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Media Preview */}
            <div className="bg-gray-100 rounded-lg p-4 text-center">
              {material.file_url ? (
                <img
                  src={material.file_url}
                  alt={material.title}
                  className="max-w-full max-h-96 mx-auto rounded-lg object-cover"
                />
              ) : (
                <div className="w-32 h-32 bg-gray-200 rounded-lg flex items-center justify-center mx-auto">
                  <span className="text-4xl">📎</span>
                </div>
              )}
            </div>

            {/* Material Info */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Cliente</label>
                {isEditing ? (
                  <select
                    value={formData.client_id}
                    onChange={(e) => setFormData(prev => ({ ...prev, client_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    {clients.map(client => (
                      <option key={client.id} value={client.id}>
                        {client.name}
                      </option>
                    ))}
                  </select>
                ) : (
                  <p className="text-gray-900">{material.client_name}</p>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Tipo</label>
                <p className="text-gray-900">{material.type}</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Status</label>
                {isEditing ? (
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData(prev => ({ ...prev, status: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  >
                    <option value="planned">🟡 Planejado</option>
                    <option value="in_production">🔵 Em Produção</option>
                    <option value="awaiting_approval">🟠 Aguardando Aprovação</option>
                    <option value="approved">🟢 Aprovado</option>
                    <option value="revision_requested">🔴 Revisão Solicitada</option>
                    <option value="published">⚫ Publicado</option>
                  </select>
                ) : (
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(material.status)}`}>
                    {material.status.replace('_', ' ')}
                  </span>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Data de Publicação</label>
                {isEditing ? (
                  <input
                    type="datetime-local"
                    value={formData.scheduled_date}
                    onChange={(e) => setFormData(prev => ({ ...prev, scheduled_date: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                  />
                ) : (
                  <p className="text-gray-900">{new Date(material.scheduled_date).toLocaleString()}</p>
                )}
              </div>
            </div>

            {/* Title */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Título</label>
              {isEditing ? (
                <input
                  type="text"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <p className="text-gray-900">{material.title}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Legenda</label>
              {isEditing ? (
                <textarea
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  rows="4"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
              ) : (
                <p className="text-gray-900 bg-gray-50 p-3 rounded-md">{material.description}</p>
              )}
            </div>

            {/* Tags */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Tags</label>
              {isEditing ? (
                <div>
                  <div className="flex flex-wrap gap-2 mb-2">
                    {formData.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                      >
                        #{tag}
                        <button
                          type="button"
                          onClick={() => handleRemoveTag(tag)}
                          className="ml-1 text-blue-600 hover:text-blue-800"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                  <input
                    type="text"
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyDown={handleAddTag}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Digite uma tag e pressione Enter"
                  />
                </div>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {material.tags && material.tags.length > 0 ? (
                    material.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2 py-1 rounded-full text-sm bg-blue-100 text-blue-800"
                      >
                        #{tag}
                      </span>
                    ))
                  ) : (
                    <span className="text-gray-500">Nenhuma tag</span>
                  )}
                </div>
              )}
            </div>

            {/* Comments */}
            {material.comments && material.comments.length > 0 && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Comentários do Cliente</label>
                <div className="space-y-2">
                  {material.comments.map((comment, index) => (
                    <div key={index} className="bg-gray-50 p-3 rounded-md">
                      <p className="text-sm text-gray-900">{comment.text}</p>
                      <p className="text-xs text-gray-500 mt-1">
                        {comment.client_name} • {new Date(comment.timestamp).toLocaleString()}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Submit Buttons */}
            {isEditing && (
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={() => setIsEditing(false)}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Salvar Alterações
                </button>
              </div>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    contact_person: '',
    project_type: 'marketing_digital',
    visible_metrics: ['impressions', 'clicks', 'ctr', 'spend']
  });

  const handleSubmit = (e) => {
    e.preventDefault();
    onSubmit(formData);
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg max-w-md w-full mx-4">
        <div className="p-6">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold">Novo Cliente</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700">
              ✕
            </button>
          </div>
          
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Nome da Empresa
              </label>
              <input
                type="text"
                required
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email de Login
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Senha Inicial
              </label>
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Contato Principal
              </label>
              <input
                type="text"
                value={formData.contact_person}
                onChange={(e) => setFormData({...formData, contact_person: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Tipo de Projeto
              </label>
              <select
                value={formData.project_type}
                onChange={(e) => setFormData({...formData, project_type: e.target.value})}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              >
                <option value="marketing_digital">Marketing Digital</option>
                <option value="branding">Branding</option>
                <option value="ecommerce">E-commerce</option>
              </select>
            </div>
            
            <div className="flex justify-end space-x-3 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-md hover:bg-gray-300"
              >
                Cancelar
              </button>
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Criar Cliente
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

// Placeholder pages for other admin sections
// Placeholder pages for other admin sections
const AdminMaterialsPage = ({ materials, clients, onRefresh }) => {
  const { addToast } = React.useContext(ToastContext);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showPreviewModal, setShowPreviewModal] = useState(false);
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [selectedMaterials, setSelectedMaterials] = useState([]);
  const [filters, setFilters] = useState({
    client: 'all',
    status: 'all',
    type: 'all',
    search: ''
  });
  const [allMaterials, setAllMaterials] = useState(materials);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setAllMaterials(materials);
  }, [materials]);

  const handleUploadMaterial = async (materialData) => {
    try {
      setLoading(true);
      await axios.post('/admin/materials', materialData);
      addToast('Material enviado com sucesso! ✅');
      setShowUploadModal(false);
      onRefresh();
    } catch (error) {
      console.error('Error uploading material:', error);
      addToast('Erro ao enviar material', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateMaterial = async (materialId, updateData) => {
    try {
      setLoading(true);
      await axios.put(`/admin/materials/${materialId}`, updateData);
      addToast('Material atualizado com sucesso! 📊');
      setShowPreviewModal(false);
      onRefresh();
    } catch (error) {
      console.error('Error updating material:', error);
      addToast('Erro ao atualizar material', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteMaterial = async (materialId) => {
    if (!confirm('Tem certeza que deseja excluir este material?')) return;
    
    try {
      setLoading(true);
      await axios.delete(`/admin/materials/${materialId}`);
      addToast('Material excluído com sucesso! 🗑️');
      onRefresh();
    } catch (error) {
      console.error('Error deleting material:', error);
      addToast('Erro ao excluir material', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleBulkAction = async (action, newStatus = null) => {
    if (selectedMaterials.length === 0) {
      addToast('Selecione pelo menos um material', 'error');
      return;
    }

    if (action === 'delete' && !confirm(`Tem certeza que deseja excluir ${selectedMaterials.length} materiais?`)) {
      return;
    }

    try {
      setLoading(true);
      await axios.post('/admin/materials/bulk-actions', {
        action,
        material_ids: selectedMaterials,
        new_status: newStatus
      });
      addToast(`Ação realizada em ${selectedMaterials.length} materiais! ✅`);
      setSelectedMaterials([]);
      onRefresh();
    } catch (error) {
      console.error('Error performing bulk action:', error);
      addToast('Erro ao realizar ação em lote', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const filteredMaterials = allMaterials.filter(material => {
    if (filters.client !== 'all' && material.client_id !== filters.client) return false;
    if (filters.status !== 'all' && material.status !== filters.status) return false;
    if (filters.type !== 'all' && material.type !== filters.type) return false;
    if (filters.search && !material.title.toLowerCase().includes(filters.search.toLowerCase()) && 
        !material.description.toLowerCase().includes(filters.search.toLowerCase())) return false;
    return true;
  });

  const handleMaterialSelect = (materialId) => {
    setSelectedMaterials(prev => 
      prev.includes(materialId) 
        ? prev.filter(id => id !== materialId)
        : [...prev, materialId]
    );
  };

  const handleSelectAll = () => {
    if (selectedMaterials.length === filteredMaterials.length) {
      setSelectedMaterials([]);
    } else {
      setSelectedMaterials(filteredMaterials.map(m => m.id));
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      planned: 'bg-yellow-100 text-yellow-800',
      in_production: 'bg-blue-100 text-blue-800',
      awaiting_approval: 'bg-orange-100 text-orange-800',
      approved: 'bg-green-100 text-green-800',
      revision_requested: 'bg-red-100 text-red-800',
      published: 'bg-gray-100 text-gray-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = (status) => {
    const icons = {
      planned: '🟡',
      in_production: '🔵',
      awaiting_approval: '🟠',
      approved: '🟢',
      revision_requested: '🔴',
      published: '⚫'
    };
    return icons[status] || '⚪';
  };

  return (
    <div className="p-8">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Gestão de Materiais</h1>
          <p className="mt-2 text-gray-600">Upload, organize e gerencie todos os materiais dos clientes</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowUploadModal(true)}
            className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 flex items-center"
          >
            <span className="mr-2">🔵</span>
            Upload Material
          </button>
          <button className="bg-gray-600 text-white px-4 py-2 rounded-md hover:bg-gray-700 flex items-center">
            <span className="mr-2">📅</span>
            Agendar Lote
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex flex-wrap gap-4 mb-4">
          <div className="min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Cliente</label>
            <select
              value={filters.client}
              onChange={(e) => handleFilterChange('client', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Todos os Clientes</option>
              {clients.map(client => (
                <option key={client.id} value={client.id}>
                  {client.name} ({client.materials_count})
                </option>
              ))}
            </select>
          </div>

          <div className="min-w-[150px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={filters.status}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Todos</option>
              <option value="planned">🟡 Planejado</option>
              <option value="in_production">🔵 Em Produção</option>
              <option value="awaiting_approval">🟠 Aguardando Aprovação</option>
              <option value="approved">🟢 Aprovado</option>
              <option value="revision_requested">🔴 Revisão Solicitada</option>
              <option value="published">⚫ Publicado</option>
            </select>
          </div>

          <div className="min-w-[120px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Tipo</label>
            <select
              value={filters.type}
              onChange={(e) => handleFilterChange('type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            >
              <option value="all">Todos</option>
              <option value="photo">📷 Foto</option>
              <option value="video">🎬 Vídeo</option>
              <option value="carousel">🔄 Carrossel</option>
              <option value="story">📱 Stories</option>
            </select>
          </div>

          <div className="flex-1 min-w-[200px]">
            <label className="block text-sm font-medium text-gray-700 mb-1">Buscar</label>
            <div className="relative">
              <input
                type="text"
                placeholder="Buscar por título, legenda..."
                value={filters.search}
                onChange={(e) => handleFilterChange('search', e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
              <svg className="absolute left-3 top-2.5 h-4 w-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
          </div>
        </div>

        {/* Quick Status Filters */}
        <div className="flex flex-wrap gap-2">
          <span className="text-sm text-gray-500 mr-2">Filtros rápidos:</span>
          {[
            { key: 'all', label: 'Todos', icon: '📋' },
            { key: 'awaiting_approval', label: 'Pendentes', icon: '🟠' },
            { key: 'approved', label: 'Aprovados', icon: '🟢' },
            { key: 'revision_requested', label: 'Revisão', icon: '🔴' },
            { key: 'published', label: 'Publicados', icon: '⚫' }
          ].map(filter => (
            <button
              key={filter.key}
              onClick={() => handleFilterChange('status', filter.key)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-colors ${
                filters.status === filter.key
                  ? 'bg-blue-100 text-blue-800'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              {filter.icon} {filter.label}
            </button>
          ))}
        </div>
      </div>

      {/* Bulk Actions */}
      {selectedMaterials.length > 0 && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-blue-900">
              {selectedMaterials.length} material(is) selecionado(s)
            </span>
            <div className="flex space-x-2">
              <button
                onClick={() => handleBulkAction('approve')}
                className="px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700"
              >
                ✅ Aprovar
              </button>
              <button
                onClick={() => handleBulkAction('update_status', 'awaiting_approval')}
                className="px-3 py-1 bg-orange-600 text-white rounded text-sm hover:bg-orange-700"
              >
                📤 Enviar p/ Aprovação
              </button>
              <button
                onClick={() => handleBulkAction('delete')}
                className="px-3 py-1 bg-red-600 text-white rounded text-sm hover:bg-red-700"
              >
                🗑️ Excluir
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Materials List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h3 className="text-lg font-medium text-gray-900">
              Materiais ({filteredMaterials.length})
            </h3>
            <div className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={selectedMaterials.length === filteredMaterials.length && filteredMaterials.length > 0}
                onChange={handleSelectAll}
                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              />
              <label className="text-sm text-gray-600">Selecionar todos</label>
            </div>
          </div>
        </div>

        <div className="p-6">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Carregando materiais...</p>
            </div>
          ) : filteredMaterials.length === 0 ? (
            <div className="text-center py-8">
              <div className="w-24 h-24 bg-gray-100 rounded-lg flex items-center justify-center mx-auto mb-4">
                <span className="text-4xl">📂</span>
              </div>
              <p className="text-gray-500">Nenhum material encontrado para este filtro</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredMaterials.map((material) => (
                <div key={material.id} className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-3">
                    <input
                      type="checkbox"
                      checked={selectedMaterials.includes(material.id)}
                      onChange={() => handleMaterialSelect(material.id)}
                      className="mt-1 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                    />
                    <div className="flex-1 ml-3">
                      <div className="flex items-center mb-2">
                        {material.file_url && (
                          <img
                            src={material.file_url}
                            alt={material.title}
                            className="w-16 h-16 rounded-lg object-cover mr-3"
                          />
                        )}
                        <div className="flex-1">
                          <h4 className="font-medium text-gray-900 text-sm">{material.title}</h4>
                          <p className="text-xs text-gray-600">{material.client_name}</p>
                          <p className="text-xs text-gray-500">
                            📅 {new Date(material.scheduled_date).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      
                      <div className="flex items-center justify-between mb-2">
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(material.status)}`}>
                          {getStatusIcon(material.status)} {material.status.replace('_', ' ')}
                        </span>
                        <span className="text-xs text-gray-500">{material.type}</span>
                      </div>
                      
                      <p className="text-xs text-gray-600 mb-2 line-clamp-2">{material.description}</p>
                      
                      {material.tags && material.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-3">
                          {material.tags.slice(0, 3).map((tag, index) => (
                            <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs">
                              #{tag}
                            </span>
                          ))}
                          {material.tags.length > 3 && (
                            <span className="text-xs text-gray-500">+{material.tags.length - 3}</span>
                          )}
                        </div>
                      )}
                      
                      <div className="flex flex-wrap gap-2 text-xs">
                        <button
                          onClick={() => {
                            setSelectedMaterial(material);
                            setShowPreviewModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-800"
                        >
                          👁️ Preview
                        </button>
                        <button
                          onClick={() => {
                            setSelectedMaterial(material);
                            setShowPreviewModal(true);
                          }}
                          className="text-gray-600 hover:text-gray-800"
                        >
                          ✏️ Editar
                        </button>
                        {material.status === 'in_production' && (
                          <button
                            onClick={() => handleUpdateMaterial(material.id, { status: 'awaiting_approval' })}
                            className="text-orange-600 hover:text-orange-800"
                          >
                            📤 Enviar p/ Aprovação
                          </button>
                        )}
                        {material.status === 'awaiting_approval' && (
                          <button
                            onClick={() => handleUpdateMaterial(material.id, { status: 'approved' })}
                            className="text-green-600 hover:text-green-800"
                          >
                            ✅ Aprovar
                          </button>
                        )}
                        {material.comments && material.comments.length > 0 && (
                          <button className="text-purple-600 hover:text-purple-800">
                            💬 Comentários ({material.comments.length})
                          </button>
                        )}
                        <button
                          onClick={() => handleDeleteMaterial(material.id)}
                          className="text-red-600 hover:text-red-800"
                        >
                          🗑️ Excluir
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <MaterialUploadModal
          onClose={() => setShowUploadModal(false)}
          onSubmit={handleUploadMaterial}
          clients={clients}
        />
      )}

      {/* Preview/Edit Modal */}
      {showPreviewModal && selectedMaterial && (
        <MaterialPreviewEditModal
          material={selectedMaterial}
          onClose={() => {
            setShowPreviewModal(false);
            setSelectedMaterial(null);
          }}
          onSubmit={handleUpdateMaterial}
          clients={clients}
        />
      )}
    </div>
  );
};

const AdminCampaignsPage = ({ campaigns, clients }) => {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Gestão de Campanhas</h1>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-600">Total de {campaigns.length} campanhas</p>
        <div className="mt-4 space-y-4">
          {campaigns.map(campaign => (
            <div key={campaign.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-medium">{campaign.name}</h3>
                  <p className="text-gray-500">{campaign.client_name}</p>
                  <div className="mt-2 grid grid-cols-4 gap-4 text-sm">
                    <span>CTR: {campaign.ctr}%</span>
                    <span>CPC: R$ {campaign.cpc.toFixed(2)}</span>
                    <span>Impressões: {campaign.impressions.toLocaleString()}</span>
                    <span>Gasto: R$ {campaign.spend.toFixed(2)}</span>
                  </div>
                </div>
                <span className={`px-2 py-1 rounded text-xs ${
                  campaign.status === 'active' ? 'bg-green-100 text-green-800' :
                  'bg-gray-100 text-gray-800'
                }`}>
                  {campaign.status}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const AdminDocumentsPage = ({ documents, clients }) => {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Gestão de Documentos</h1>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-600">Sistema de upload e organização de documentos em desenvolvimento</p>
      </div>
    </div>
  );
};

const AdminCalendarPage = ({ materials, campaigns }) => {
  return (
    <div className="p-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-8">Calendário Unificado</h1>
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <p className="text-gray-600">Calendário com todos os materiais e campanhas em desenvolvimento</p>
      </div>
    </div>
  );
};

// =================== CLIENT APP (EXISTING) ===================

// Status Badge Component
const StatusBadge = ({ status }) => {
  const statusConfig = {
    planned: { color: 'bg-yellow-100 text-yellow-800', icon: '🟡', label: 'Planejado' },
    in_production: { color: 'bg-blue-100 text-blue-800', icon: '🔵', label: 'Em Produção' },
    awaiting_approval: { color: 'bg-orange-100 text-orange-800', icon: '🟠', label: 'Aguardando Aprovação' },
    approved: { color: 'bg-green-100 text-green-800', icon: '🟢', label: 'Aprovado' },
    revision_requested: { color: 'bg-red-100 text-red-800', icon: '🔴', label: 'Revisão Solicitada' },
    published: { color: 'bg-gray-100 text-gray-800', icon: '⚫', label: 'Publicado' }
  };

  const config = statusConfig[status] || statusConfig.planned;

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${config.color}`}>
      <span className="mr-1">{config.icon}</span>
      {config.label}
    </span>
  );
};

// Material Preview Modal Component (shortened for space)
const MaterialPreviewModal = ({ material, isOpen, onClose, onNext, onPrevious, onApprove, onRequestRevision }) => {
  const [comment, setComment] = useState('');
  const [showCommentForm, setShowCommentForm] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
      if (e.key === 'ArrowLeft' && onPrevious) onPrevious();
      if (e.key === 'ArrowRight' && onNext) onNext();
    };

    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen, onClose, onNext, onPrevious]);

  const handleRequestRevision = async (e) => {
    e.preventDefault();
    if (!comment.trim()) return;
    
    await onRequestRevision(comment);
    setComment('');
    setShowCommentForm(false);
  };

  if (!isOpen || !material) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl max-h-[90vh] w-full overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">{material.title}</h2>
          <button onClick={onClose} className="p-2 text-gray-500 hover:text-gray-700">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="p-6">
          {/* Media Preview */}
          {material.file_url && (
            <div className="mb-6">
              <div className="bg-gray-100 rounded-lg p-4 text-center">
                <img
                  src={material.file_url}
                  alt={material.title}
                  className="max-w-full max-h-96 mx-auto rounded-lg object-cover"
                />
              </div>
            </div>
          )}

          {/* Material Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Data</label>
              <p className="text-sm text-gray-900">{new Date(material.scheduled_date).toLocaleDateString()}</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
              <StatusBadge status={material.status} />
            </div>
          </div>

          {/* Description */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Legenda</label>
            <p className="text-sm text-gray-900 bg-gray-50 p-3 rounded-md">{material.description}</p>
          </div>

          {/* Action Buttons */}
          {material.status === 'awaiting_approval' && (
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                onClick={() => onApprove(material.id)}
                className="flex-1 flex items-center justify-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                ✅ Aprovar
              </button>
              <button
                onClick={() => setShowCommentForm(true)}
                className="flex-1 flex items-center justify-center px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700"
              >
                📝 Solicitar Revisão
              </button>
            </div>
          )}

          {/* Comment Form */}
          {showCommentForm && (
            <form onSubmit={handleRequestRevision} className="mt-4 p-4 bg-gray-50 rounded-md">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Descreva as mudanças necessárias:
              </label>
              <textarea
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows="3"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Ex: Poderia trocar a cor de fundo por algo mais vibrante..."
                required
              />
              <div className="mt-3 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setShowCommentForm(false)}
                  className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-orange-600 text-white rounded-md hover:bg-orange-700"
                >
                  Enviar Revisão
                </button>
              </div>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};

// Client App (existing functionality)
const ClientApp = () => {
  const { user, logout } = React.useContext(AuthContext);
  const { addToast } = React.useContext(ToastContext);
  const [materials, setMaterials] = useState([]);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [currentPage, setCurrentPage] = useState('dashboard');
  const [selectedMaterial, setSelectedMaterial] = useState(null);
  const [previewModalOpen, setPreviewModalOpen] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [materialsRes, campaignsRes] = await Promise.all([
        axios.get('/materials'),
        axios.get('/campaigns')
      ]);
      setMaterials(materialsRes.data);
      setCampaigns(campaignsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMaterialClick = (material) => {
    setSelectedMaterial(material);
    setPreviewModalOpen(true);
  };

  const handleApproveMaterial = async (materialId) => {
    try {
      await axios.post(`/materials/${materialId}/approve`);
      addToast('Material aprovado com sucesso! ✅');
      setPreviewModalOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error approving material:', error);
      addToast('Erro ao aprovar material', 'error');
    }
  };

  const handleRequestRevision = async (comment) => {
    try {
      await axios.post(`/materials/${selectedMaterial.id}/request-revision`, { text: comment });
      addToast('Comentário enviado para a equipe 📝');
      setPreviewModalOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error requesting revision:', error);
      addToast('Erro ao solicitar revisão', 'error');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading your dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">Take 2 Studio</h1>
              <span className="ml-2 text-sm text-gray-500">Client Portal</span>
            </div>
            <div className="flex items-center space-x-4">
              <span className="text-sm text-gray-700">Welcome, {user?.name}</span>
              <button onClick={logout} className="text-sm text-gray-500 hover:text-gray-700">
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Simple client dashboard */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900">Your Project Dashboard</h2>
          <p className="mt-2 text-gray-600">Track your marketing materials and campaign performance</p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-sm font-medium text-gray-500">Total Materials</div>
            <div className="text-2xl font-bold text-gray-900">{materials.length}</div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-sm font-medium text-gray-500">Published</div>
            <div className="text-2xl font-bold text-gray-900">
              {materials.filter(m => m.status === 'published').length}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-sm font-medium text-gray-500">Active Campaigns</div>
            <div className="text-2xl font-bold text-gray-900">
              {campaigns.filter(c => c.status === 'active').length}
            </div>
          </div>
          <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="text-sm font-medium text-gray-500">Awaiting Approval</div>
            <div className="text-2xl font-bold text-gray-900">
              {materials.filter(m => m.status === 'awaiting_approval').length}
            </div>
          </div>
        </div>

        {/* Recent Materials */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Materials</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {materials.slice(0, 5).map((material) => (
                <div
                  key={material.id}
                  onClick={() => handleMaterialClick(material)}
                  className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow cursor-pointer"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="text-sm font-medium text-gray-900">{material.title}</h3>
                      <p className="mt-1 text-sm text-gray-600">{material.description}</p>
                      <div className="mt-2 flex items-center space-x-2">
                        <StatusBadge status={material.status} />
                        <span className="text-xs text-gray-500">{material.type}</span>
                      </div>
                    </div>
                    {material.file_url && (
                      <div className="ml-4 flex-shrink-0">
                        <img
                          src={material.file_url}
                          alt={material.title}
                          className="h-12 w-12 rounded-lg object-cover"
                        />
                      </div>
                    )}
                  </div>
                  <div className="mt-3 text-xs text-gray-500">
                    Scheduled: {new Date(material.scheduled_date).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>

      {/* Material Preview Modal */}
      <MaterialPreviewModal
        material={selectedMaterial}
        isOpen={previewModalOpen}
        onClose={() => setPreviewModalOpen(false)}
        onApprove={handleApproveMaterial}
        onRequestRevision={handleRequestRevision}
      />
    </div>
  );
};

// =================== MAIN APP ===================

const App = () => {
  return (
    <AuthProvider>
      <ToastProvider>
        <AppRouter />
      </ToastProvider>
    </AuthProvider>
  );
};

export default App;
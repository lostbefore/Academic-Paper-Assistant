import { Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { FileText, Plus, BookOpen, Home, Search, Settings, LogOut, Loader2 } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import CreatePaper from './pages/CreatePaper';
import PaperViewer from './pages/PaperViewer';
import PaperList from './pages/PaperList';
import Login from './pages/Login';
import Literature from './pages/Literature';
import SettingsPage from './pages/Settings';
import { LanguageProvider, useLanguage } from './i18n';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import LanguageSwitcher from './components/LanguageSwitcher';
import ThemeToggle from './components/ThemeToggle';

function Layout() {
  const location = useLocation();
  const { t, language } = useLanguage();
  const { user, logout } = useAuth();
  const zh = language === 'chinese';

  const navItems = [
    { path: '/', icon: Home, label: zh ? '首页' : 'Home' },
    { path: '/papers', icon: BookOpen, label: t('nav.myPapers') as string },
    { path: '/create', icon: Plus, label: t('nav.newPaper') as string },
    { path: '/literature', icon: Search, label: zh ? '文献检索' : 'Literature' },
    { path: '/settings', icon: Settings, label: zh ? '设置' : 'Settings' },
  ];

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16 gap-4">
            <Link to="/" className="flex items-center gap-3 shrink-0">
              <div className="bg-primary-600 dark:bg-primary-500 p-2 rounded-lg">
                <FileText className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold text-gray-900 dark:text-gray-100 hidden sm:inline">
                {t('appName') as string}
              </span>
            </Link>

            <nav className="flex items-center gap-1 overflow-x-auto">
              {navItems.map((item) => {
                const Icon = item.icon;
                const isActive =
                  location.pathname === item.path ||
                  (item.path !== '/' && location.pathname.startsWith(item.path));
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg transition-colors whitespace-nowrap ${
                      isActive
                        ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium hidden md:inline">{item.label}</span>
                  </Link>
                );
              })}
            </nav>

            <div className="flex items-center gap-1 sm:gap-2 shrink-0">
              <LanguageSwitcher />
              <ThemeToggle />
              <div className="hidden sm:flex items-center gap-2 pl-2 ml-1 border-l border-gray-200 dark:border-gray-700">
                <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 flex items-center justify-center text-sm font-semibold">
                  {(user?.name || user?.email || '?').slice(0, 1).toUpperCase()}
                </div>
                <span className="text-sm text-gray-700 dark:text-gray-300 max-w-[8rem] truncate">
                  {user?.name || user?.email}
                </span>
                <button
                  onClick={logout}
                  title={zh ? '退出登录' : 'Sign out'}
                  className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-700 dark:text-gray-400"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/papers" element={<PaperList />} />
          <Route path="/create" element={<CreatePaper />} />
          <Route path="/papers/:id" element={<PaperViewer />} />
          <Route path="/literature" element={<Literature />} />
          <Route path="/settings" element={<SettingsPage />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5 flex flex-col sm:flex-row items-center justify-between gap-2 text-sm text-gray-500 dark:text-gray-400">
          <p>{t('footer.description') as string} · v2.0</p>
          <span>{t('footer.supports') as string}</span>
        </div>
      </footer>
    </div>
  );
}

function Protected() {
  const { user, loading } = useAuth();
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }
  if (!user) return <Navigate to="/login" replace />;
  return <Layout />;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<Protected />} />
    </Routes>
  );
}

function App() {
  return (
    <LanguageProvider>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </LanguageProvider>
  );
}

export default App;

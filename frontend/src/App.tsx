import { Routes, Route, Link, useLocation } from 'react-router-dom'
import { FileText, Plus, BookOpen, Home } from 'lucide-react'
import Dashboard from './pages/Dashboard'
import CreatePaper from './pages/CreatePaper'
import PaperViewer from './pages/PaperViewer'
import PaperList from './pages/PaperList'
import { LanguageProvider, useLanguage } from './i18n'
import LanguageSwitcher from './components/LanguageSwitcher'
import ThemeToggle from './components/ThemeToggle'

function AppContent() {
  const location = useLocation()
  const { t } = useLanguage()

  const navItems = [
    { path: '/', icon: Home, label: t('nav.home') as string },
    { path: '/papers', icon: BookOpen, label: t('nav.myPapers') as string },
    { path: '/create', icon: Plus, label: t('nav.newPaper') as string },
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
      {/* Header */}
      <header className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 sticky top-0 z-50 transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="bg-primary-600 dark:bg-primary-500 p-2 rounded-lg">
                <FileText className="w-6 h-6 text-white" />
              </div>
              <Link to="/" className="text-xl font-bold text-gray-900 dark:text-gray-100">
                {t('appName')}
              </Link>
            </div>
            <nav className="flex items-center gap-2">
              {navItems.map((item) => {
                const Icon = item.icon
                const isActive = location.pathname === item.path
                return (
                  <Link
                    key={item.path}
                    to={item.path}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-700 dark:text-primary-400'
                        : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span className="font-medium">{item.label}</span>
                  </Link>
                )
              })}
              <LanguageSwitcher />
              <ThemeToggle />
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/papers" element={<PaperList />} />
          <Route path="/create" element={<CreatePaper />} />
          <Route path="/papers/:id" element={<PaperViewer />} />
        </Routes>
      </main>

      {/* Footer */}
      <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 mt-auto transition-colors duration-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400">
            <p>{t('footer.description')}</p>
            <div className="flex items-center gap-4">
              <span>{t('footer.supports')}</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}

function App() {
  return (
    <LanguageProvider>
      <AppContent />
    </LanguageProvider>
  )
}

export default App
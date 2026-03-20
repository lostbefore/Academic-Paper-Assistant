import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Plus, FileText, BookOpen, Award, ArrowRight, Sparkles } from 'lucide-react';
import { paperApi } from '../services/api';
import { Paper, ApiStatus } from '../types';
import { useLanguage } from '../i18n';

export default function Dashboard() {
  const { t } = useLanguage();
  const [recentPapers, setRecentPapers] = useState<Paper[]>([]);
  const [status, setStatus] = useState<ApiStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      const [papersData, statusData] = await Promise.all([
        paperApi.getPapers(),
        paperApi.getStatus(),
      ]);
      setRecentPapers(papersData.slice(0, 5));
      setStatus(statusData);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const stats = [
    { label: t('dashboard.totalPapers'), value: recentPapers.length, icon: FileText },
    { label: t('dashboard.completed'), value: recentPapers.filter(p => p.status === 'completed').length, icon: Award },
    { label: t('dashboard.inProgress'), value: recentPapers.filter(p => p.status === 'generating' || p.status === 'writing' || p.status === 'reviewing').length, icon: Sparkles },
  ];

  const features = [
    {
      title: t('dashboard.features.generate.title'),
      description: t('dashboard.features.generate.desc'),
      icon: Plus,
      link: '/create',
      color: 'bg-primary-500',
    },
    {
      title: t('dashboard.features.manage.title'),
      description: t('dashboard.features.manage.desc'),
      icon: BookOpen,
      link: '/papers',
      color: 'bg-emerald-500',
    },
  ];

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'generating':
      case 'writing':
      case 'reviewing': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-primary-600 to-primary-700 rounded-2xl p-8 text-white">
        <h1 className="text-3xl font-bold mb-4">
          {t('dashboard.welcome')}
        </h1>
        <p className="text-primary-100 text-lg max-w-2xl mb-6">
          {t('dashboard.welcomeDesc')}
        </p>
        <div className="flex items-center gap-4">
          <Link
            to="/create"
            className="inline-flex items-center gap-2 bg-white text-primary-600 px-6 py-3 rounded-lg font-semibold hover:bg-primary-50 transition-colors"
          >
            <Plus className="w-5 h-5" />
            {t('dashboard.createNewPaper')}
          </Link>
          <Link
            to="/papers"
            className="inline-flex items-center gap-2 bg-primary-500 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-400 transition-colors"
          >
            {t('dashboard.viewPapers')}
            <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <div key={stat.label} className="card flex items-center gap-4">
              <div className="p-3 bg-primary-50 dark:bg-primary-900/30 rounded-lg">
                <Icon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stat.value}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{stat.label}</p>
              </div>
            </div>
          );
        })}
      </div>

      {/* Features */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {features.map((feature) => {
          const Icon = feature.icon;
          return (
            <Link
              key={feature.title}
              to={feature.link}
              className="card hover:shadow-md transition-shadow group"
            >
              <div className="flex items-start gap-4">
                <div className={`p-3 ${feature.color} rounded-lg`}>
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 group-hover:text-primary-600 dark:group-hover:text-primary-400 transition-colors">
                    {feature.title}
                  </h3>
                  <p className="text-gray-500 dark:text-gray-400 mt-1">{feature.description}</p>
                </div>
                <ArrowRight className="w-5 h-5 text-gray-400 dark:text-gray-500 group-hover:text-primary-600 dark:group-hover:text-primary-400 group-hover:translate-x-1 transition-all" />
              </div>
            </Link>
          );
        })}
      </div>

      {/* Recent Papers */}
      {recentPapers.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100">Recent Papers</h2>
            <Link to="/papers" className="text-primary-600 hover:text-primary-700 dark:text-primary-400 dark:hover:text-primary-300 font-medium">
              View All
            </Link>
          </div>
          <div className="space-y-3">
            {recentPapers.map((paper) => (
              <Link
                key={paper.id}
                to={`/papers/${paper.id}`}
                className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-600 transition-colors"
              >
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-gray-400 dark:text-gray-500" />
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-gray-100">{paper.title}</h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {new Date(paper.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <span className={`px-3 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(paper.status)}`}>
                  {t(`status.${paper.status}`)}
                </span>
              </Link>
            ))}
          </div>
        </div>
      )}

      {/* API Status */}
      {status && (
        <div className="card bg-gray-50 dark:bg-gray-800">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">{t('dashboard.apiConfig')}</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">{t('dashboard.apiKey')}:</span>
              <span className={`ml-2 font-medium ${status.api_key_configured ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {status.api_key_configured ? `✓ ${t('dashboard.configured')}` : `✗ ${t('dashboard.notConfigured')}`}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">{t('dashboard.model')}:</span>
              <span className="ml-2 font-medium text-gray-700 dark:text-gray-300">{status.model}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">{t('dashboard.apiBase')}:</span>
              <span className="ml-2 font-medium text-gray-700 dark:text-gray-300">{status.api_base}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">{t('dashboard.citationStyles')}:</span>
              <span className="ml-2 font-medium text-gray-700 dark:text-gray-300">{status.citation_styles.length}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">{t('dashboard.languages')}:</span>
              <span className="ml-2 font-medium text-gray-700 dark:text-gray-300">
                {status.language_options ? Object.keys(status.language_options).length : 2}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

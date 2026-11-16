import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  FileText,
  BookOpen,
  Clock,
  Sparkles,
  ArrowRight,
  Search,
  TrendingUp,
  AlertCircle,
} from 'lucide-react';
import { errorMessage, metaApi, paperApi } from '../services/api';
import type { ApiStatus, Paper, Stats } from '../types';
import { useLanguage } from '../i18n';
import { useAuth } from '../contexts/AuthContext';

export default function Dashboard() {
  const { t, language } = useLanguage();
  const { user } = useAuth();
  const zh = language === 'chinese';
  const [papers, setPapers] = useState<Paper[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [status, setStatus] = useState<ApiStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    (async () => {
      try {
        const [list, statsData, statusData] = await Promise.all([
          paperApi.list(),
          paperApi.stats(),
          metaApi.status(),
        ]);
        setPapers(list.slice(0, 5));
        setStats(statsData);
        setStatus(statusData);
      } catch (err) {
        setError(errorMessage(err));
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  const statusLabel = (s: string) => {
    const map: Record<string, [string, string]> = {
      queued: ['排队中', 'Queued'],
      running: ['生成中', 'Generating'],
      completed: ['已完成', 'Completed'],
      failed: ['失败', 'Failed'],
      cancelled: ['已取消', 'Cancelled'],
    };
    const entry = map[s] || [s, s];
    return zh ? entry[0] : entry[1];
  };

  const statusColor = (s: string) => {
    switch (s) {
      case 'completed': return 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300';
      case 'failed': return 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300';
      case 'cancelled': return 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300';
      default: return 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary-600" />
      </div>
    );
  }

  const cards = [
    { label: zh ? '论文总数' : 'Total papers', value: stats?.total ?? 0, icon: FileText },
    { label: zh ? '已完成' : 'Completed', value: stats?.completed ?? 0, icon: BookOpen },
    { label: zh ? '进行中' : 'In progress', value: stats?.running ?? 0, icon: Clock },
    { label: zh ? '累计字数' : 'Total words', value: (stats?.words ?? 0).toLocaleString(), icon: TrendingUp },
  ];

  return (
    <div className="space-y-8">
      <section className="rounded-2xl bg-gradient-to-r from-primary-600 to-indigo-700 p-8 text-white">
        <h1 className="text-2xl sm:text-3xl font-bold">
          {zh ? `${user?.name || '你好'}，今天想写点什么？` : `Hello ${user?.name || ''}, what are you writing today?`}
        </h1>
        <p className="mt-2 text-primary-100 max-w-2xl">
          {zh
            ? '输入选题，系统会先检索真实文献，再据此生成可编辑、可导出的完整论文初稿。'
            : 'Enter a topic: the system retrieves real literature first, then drafts a complete, editable manuscript.'}
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link to="/create" className="inline-flex items-center gap-2 bg-white text-primary-700 px-5 py-2.5 rounded-lg font-semibold hover:bg-primary-50">
            <Plus className="w-5 h-5" />{t('dashboard.createNewPaper') as string}
          </Link>
          <Link to="/literature" className="inline-flex items-center gap-2 bg-primary-500/60 border border-white/30 px-5 py-2.5 rounded-lg font-semibold hover:bg-primary-500/80">
            <Search className="w-5 h-5" />{zh ? '先查文献' : 'Search literature'}
          </Link>
        </div>
      </section>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />{error}
        </div>
      )}

      <section className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div key={card.label} className="card flex items-center gap-4">
              <div className="p-3 bg-primary-50 dark:bg-primary-900/30 rounded-lg">
                <Icon className="w-5 h-5 text-primary-600 dark:text-primary-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{card.value}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{card.label}</p>
              </div>
            </div>
          );
        })}
      </section>

      <section className="card">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            {t('dashboard.recentPapers') as string}
          </h2>
          <Link to="/papers" className="text-sm font-medium text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1">
            {t('dashboard.viewAll') as string}<ArrowRight className="w-4 h-4" />
          </Link>
        </div>
        {papers.length === 0 ? (
          <div className="text-center py-10 text-gray-500 dark:text-gray-400">
            <Sparkles className="w-10 h-10 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
            <p>{t('dashboard.noPapersYet') as string}</p>
          </div>
        ) : (
          <ul className="divide-y divide-gray-100 dark:divide-gray-700">
            {papers.map((paper) => (
              <li key={paper.id}>
                <Link to={`/papers/${paper.id}`} className="flex items-center justify-between py-3 group">
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 dark:text-gray-100 truncate group-hover:text-primary-600 dark:group-hover:text-primary-400">
                      {paper.title}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {new Date(paper.created_at).toLocaleString()} · {paper.word_count} {zh ? '字' : 'words'} · {(paper.request?.citation_style || '').toUpperCase()}
                    </p>
                  </div>
                  <span className={`ml-3 shrink-0 px-2.5 py-1 rounded-full text-xs font-medium ${statusColor(paper.status)}`}>
                    {statusLabel(paper.status)}
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      {status && (
        <section className="card bg-gray-50 dark:bg-gray-800/60">
          <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">
            {zh ? '运行环境' : 'Runtime'}
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-gray-500 dark:text-gray-400">{zh ? '大模型' : 'Model'}:</span>{' '}
              <span className="font-medium text-gray-700 dark:text-gray-200">{status.model}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">API:</span>{' '}
              <span className={`font-medium ${status.llm_configured ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {status.llm_configured ? (zh ? '已配置' : 'configured') : (zh ? '未配置' : 'missing')}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">{zh ? '文献源' : 'Sources'}:</span>{' '}
              <span className="font-medium text-gray-700 dark:text-gray-200">{status.literature_sources.length}</span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-400">{zh ? '版本' : 'Version'}:</span>{' '}
              <span className="font-medium text-gray-700 dark:text-gray-200">v{status.version}</span>
            </div>
          </div>
        </section>
      )}
    </div>
  );
}

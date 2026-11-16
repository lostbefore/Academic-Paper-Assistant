import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import {
  FileText,
  Plus,
  Trash2,
  Loader2,
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  Search,
} from 'lucide-react';
import { errorMessage, paperApi } from '../services/api';
import type { Paper } from '../types';
import { useLanguage } from '../i18n';

const FILTERS = ['all', 'completed', 'running', 'failed'] as const;
type Filter = (typeof FILTERS)[number];

export default function PaperList() {
  const { language } = useLanguage();
  const zh = language === 'chinese';
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [filter, setFilter] = useState<Filter>('all');
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');

  const load = async () => {
    try {
      setPapers(await paperApi.list());
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const remove = async (id: string) => {
    if (!confirm(zh ? '确定要删除这篇论文吗？此操作不可撤销。' : 'Delete this paper? This cannot be undone.')) return;
    setDeleting(id);
    try {
      await paperApi.remove(id);
      setPapers((list) => list.filter((p) => p.id !== id));
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setDeleting(null);
    }
  };

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return papers.filter((p) => {
      const matchFilter =
        filter === 'all' ||
        (filter === 'running' ? p.status === 'running' || p.status === 'queued' : p.status === filter);
      const matchQuery = !q || p.title.toLowerCase().includes(q);
      return matchFilter && matchQuery;
    });
  }, [papers, filter, query]);

  const statusMeta = (status: string) => {
    switch (status) {
      case 'completed':
        return { icon: CheckCircle, cls: 'text-green-500', badge: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300', label: zh ? '已完成' : 'Completed' };
      case 'failed':
        return { icon: XCircle, cls: 'text-red-500', badge: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300', label: zh ? '失败' : 'Failed' };
      case 'cancelled':
        return { icon: XCircle, cls: 'text-gray-400', badge: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300', label: zh ? '已取消' : 'Cancelled' };
      default:
        return { icon: Clock, cls: 'text-blue-500', badge: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300', label: zh ? '生成中' : 'Generating' };
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{zh ? '我的论文' : 'My Papers'}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">{papers.length} {zh ? '篇' : 'papers'}</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-gray-400" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={zh ? '搜索标题…' : 'Search title…'}
              className="input pl-9 py-2 w-48"
            />
          </div>
          <Link to="/create" className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" />{zh ? '新建' : 'New'}
          </Link>
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300">
          {error}
        </div>
      )}

      <div className="flex gap-2">
        {FILTERS.map((f) => (
          <button
            key={f}
            onClick={() => setFilter(f)}
            className={`px-3 py-1.5 rounded-lg text-sm font-medium ${
              filter === f
                ? 'bg-primary-600 text-white'
                : 'bg-white dark:bg-gray-800 text-gray-600 dark:text-gray-300 border border-gray-200 dark:border-gray-700'
            }`}
          >
            {f === 'all' ? (zh ? '全部' : 'All') : f === 'completed' ? (zh ? '已完成' : 'Completed') : f === 'running' ? (zh ? '进行中' : 'Running') : (zh ? '失败' : 'Failed')}
          </button>
        ))}
      </div>

      {visible.length === 0 ? (
        <div className="card text-center py-16">
          <FileText className="w-14 h-14 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">{zh ? '还没有论文' : 'No papers yet'}</h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6">{zh ? '从一个选题开始，系统会先检索文献再成稿。' : 'Start from a topic; literature is retrieved before drafting.'}</p>
          <Link to="/create" className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" />{zh ? '创建论文' : 'Create paper'}
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {visible.map((paper) => {
            const meta = statusMeta(paper.status);
            const Icon = meta.icon;
            return (
              <div key={paper.id} className="card hover:shadow-md transition-shadow">
                <div className="flex flex-wrap items-start justify-between gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-2">
                      <Icon className={`w-5 h-5 ${meta.cls}`} />
                      <Link to={`/papers/${paper.id}`} className="text-lg font-semibold text-gray-900 dark:text-gray-100 hover:text-primary-600 dark:hover:text-primary-400 truncate">
                        {paper.title}
                      </Link>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${meta.badge}`}>{meta.label}</span>
                      <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                        {paper.request?.language === 'chinese' ? '中文' : 'EN'}
                      </span>
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 dark:text-gray-400">
                      <span className="flex items-center gap-1"><Calendar className="w-4 h-4" />{new Date(paper.created_at).toLocaleDateString()}</span>
                      <span className="uppercase">{paper.request?.citation_style}</span>
                      <span>{paper.word_count} {zh ? '字' : 'words'}</span>
                      {paper.status !== 'completed' && paper.status !== 'failed' && (
                        <span className="flex items-center gap-2">
                          <span className="w-24 h-1.5 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                            <span className="block h-full bg-primary-500" style={{ width: `${paper.progress}%` }} />
                          </span>
                          {paper.progress}%
                        </span>
                      )}
                    </div>
                    {paper.status === 'failed' && paper.error && (
                      <p className="mt-2 text-sm text-red-600 dark:text-red-400 line-clamp-2">{paper.error}</p>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Link to={`/papers/${paper.id}`} className="btn-secondary flex items-center gap-2">
                      <FileText className="w-4 h-4" />{zh ? '查看' : 'Open'}
                    </Link>
                    <button
                      onClick={() => remove(paper.id)}
                      disabled={deleting === paper.id}
                      className="p-2.5 rounded-lg border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-300 hover:bg-red-50 hover:text-red-600 hover:border-red-300"
                      title={zh ? '删除' : 'Delete'}
                    >
                      {deleting === paper.id ? <Loader2 className="w-4 h-4 animate-spin" /> : <Trash2 className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

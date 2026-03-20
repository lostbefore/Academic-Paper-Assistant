import { useEffect, useState } from 'react';
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
  Sparkles,
} from 'lucide-react';
import { paperApi } from '../services/api';
import { Paper } from '../types';
import { useLanguage } from '../i18n';

export default function PaperList() {
  const { t } = useLanguage();
  const [papers, setPapers] = useState<Paper[]>([]);
  const [loading, setLoading] = useState(true);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadPapers();
  }, []);

  const loadPapers = async () => {
    try {
      const data = await paperApi.getPapers();
      setPapers(data);
    } catch (error) {
      console.error('Failed to load papers:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm(t('paperList.confirmDelete'))) return;

    setDeleting(id);
    try {
      await paperApi.deletePaper(id);
      setPapers(papers.filter((p) => p.id !== id));
    } catch (error) {
      console.error('Failed to delete paper:', error);
    } finally {
      setDeleting(null);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'failed':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'generating':
      case 'writing':
      case 'reviewing':
        return <Clock className="w-5 h-5 text-blue-500" />;
      default:
        return <Sparkles className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'generating':
      case 'writing':
      case 'reviewing':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
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
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t('paperList.title')}</h1>
          <p className="text-gray-500 dark:text-gray-400 mt-1">
            {papers.length} {t('paperList.paperCount')}
          </p>
        </div>
        <Link to="/create" className="btn-primary flex items-center gap-2">
          <Plus className="w-4 h-4" />
          {t('nav.newPaper')}
        </Link>
      </div>

      {/* Papers List */}
      {papers.length === 0 ? (
        <div className="card text-center py-16">
          <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {t('paperList.noPapers')}
          </h3>
          <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md mx-auto">
            {t('paperList.noPapersDesc')}
          </p>
          <Link to="/create" className="btn-primary inline-flex items-center gap-2">
            <Plus className="w-4 h-4" />
            {t('paperList.createPaper')}
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {papers.map((paper) => (
            <div
              key={paper.id}
              className="card hover:shadow-md transition-shadow dark:bg-gray-800"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    {getStatusIcon(paper.status)}
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                      {paper.title}
                    </h3>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium capitalize ${getStatusColor(
                        paper.status
                      )}`}
                    >
                      {t(`status.${paper.status}`)}
                    </span>
                    {paper.request?.language && (
                      <span className="px-2 py-1 rounded-full text-xs font-medium bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
                        {paper.request.language === 'chinese' ? '中文' : 'EN'}
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-sm text-gray-500 dark:text-gray-400 mb-4">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-4 h-4" />
                      {new Date(paper.created_at).toLocaleDateString()}
                    </span>
                    {paper.request?.citation_style && (
                      <span className="uppercase text-gray-600 dark:text-gray-400">{paper.request.citation_style}</span>
                    )}
                    {paper.review?.overall_score && (
                      <span className="flex items-center gap-1">
                        <span className="font-medium text-gray-700 dark:text-gray-300">
                          {t('paperList.qualityScore')}:
                        </span>
                        {paper.review.overall_score}/100
                      </span>
                    )}
                  </div>
                </div>

                {/* Action Buttons - Right Side */}
                <div className="flex items-center gap-3 ml-4"
                >
                  {/* View Details Button */}
                  <Link
                    to={`/papers/${paper.id}`}
                    className="inline-flex items-center gap-2 px-6 py-3 bg-primary-600 hover:bg-primary-700 text-white rounded-lg font-medium transition-all shadow-sm hover:shadow-md"
                  >
                    <FileText className="w-5 h-5" />
                    {t('paperList.viewDetails')}
                  </Link>

                  {/* Delete Button */}
                  <button
                    onClick={() => handleDelete(paper.id)}
                    disabled={deleting === paper.id}
                    className="inline-flex items-center gap-2 px-4 py-3 bg-white dark:bg-gray-700 hover:bg-red-50 dark:hover:bg-red-900/30 text-gray-700 dark:text-gray-200 hover:text-red-600 dark:hover:text-red-400 border border-gray-300 dark:border-gray-600 hover:border-red-300 dark:hover:border-red-500 rounded-lg font-medium transition-all shadow-sm"
                    title={t('delete') as string}
                  >
                    {deleting === paper.id ? (
                      <Loader2 className="w-5 h-5 animate-spin" />
                    ) : (
                      <Trash2 className="w-5 h-5" />
                    )}
                    <span className="hidden sm:inline">{t('delete')}</span>
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

import { useEffect, useState, useRef } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  Loader2,
  AlertCircle,
  FileText,
  CheckCircle,
  Download,
  RefreshCw,
  ChevronLeft,
  FileCode,
  X,
  EyeOff,
  BookOpen,
  FileSearch,
  ImageIcon,
  ExternalLink,
  User,
  BarChart3,
  Sparkles,
  Globe,
  BookOpenCheck,
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { paperApi } from '../services/api';
import { Paper, Reference, PaperImage } from '../types';
import { useLanguage } from '../i18n';

// Download state type
type DownloadType = 'pdf' | 'docx' | 'md' | null;

interface DownloadState {
  type: DownloadType;
  status: 'idle' | 'preparing' | 'downloading' | 'success' | 'error';
  progress: number;
  message: string;
}

// Helper to safely get string from translation
const getString = (value: string | Record<string, string>): string => {
  return typeof value === 'string' ? value : JSON.stringify(value);
};

export default function PaperViewer() {
  const { t } = useLanguage();
  const { id } = useParams<{ id: string }>();
  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [polling, setPolling] = useState(false);

  // Download states
  const [downloadState, setDownloadState] = useState<DownloadState>({
    type: null,
    status: 'idle',
    progress: 0,
    message: '',
  });
  const [showDownloadToast, setShowDownloadToast] = useState(false);
  const downloadToastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Preview mode state
  const [formattedPreview, setFormattedPreview] = useState(false);

  // Tab state for switching between preview and sources
  const [activeTab, setActiveTab] = useState<'preview' | 'sources'>('preview');

  useEffect(() => {
    if (id) {
      loadPaper();
    }
  }, [id]);

  const loadPaper = async () => {
    try {
      const data = await paperApi.getPaper(id!);
      setPaper(data);

      // Continue polling if paper is still generating
      if (
        data.status === 'generating' ||
        data.status === 'writing'
      ) {
        setPolling(true);
        setTimeout(loadPaper, 3000);
      } else {
        setPolling(false);
      }
    } catch (err: any) {
      setError(getString(err.response?.data?.detail || t('error')));
    } finally {
      setLoading(false);
    }
  };

  // Simulate progress for downloads
  const simulateProgress = (type: DownloadType) => {
    setDownloadState({
      type,
      status: 'preparing',
      progress: 0,
      message: getString(t('paperViewer.downloadProgress.preparing') || 'Preparing...'),
    });
    setShowDownloadToast(true);

    const steps = [
      { progress: 15, message: getString(t('paperViewer.downloadProgress.generating') || 'Generating document...'), delay: 300 },
      { progress: 35, message: getString(t('paperViewer.downloadProgress.formatting') || 'Formatting content...'), delay: 600 },
      { progress: 55, message: getString(t('paperViewer.downloadProgress.addingImages') || 'Adding images...'), delay: 900 },
      { progress: 75, message: getString(t('paperViewer.downloadProgress.finalizing') || 'Finalizing...'), delay: 1200 },
      { progress: 90, message: getString(t('paperViewer.downloadProgress.downloading') || 'Downloading...'), delay: 1500 },
    ];

    steps.forEach((step) => {
      setTimeout(() => {
        setDownloadState((prev) => ({
          ...prev,
          progress: step.progress,
          message: step.message,
        }));
      }, step.delay);
    });
  };

  const completeDownload = (type: DownloadType, success: boolean, errorMsg?: string) => {
    setDownloadState({
      type,
      status: success ? 'success' : 'error',
      progress: success ? 100 : 0,
      message: success
        ? getString(t('paperViewer.downloadProgress.success') || 'Download complete!')
        : errorMsg || getString(t('paperViewer.downloadProgress.failed') || 'Download failed'),
    });

    // Auto hide toast after 3 seconds on success
    if (success) {
      if (downloadToastTimer.current) {
        clearTimeout(downloadToastTimer.current);
      }
      downloadToastTimer.current = setTimeout(() => {
        setShowDownloadToast(false);
        setDownloadState({ type: null, status: 'idle', progress: 0, message: '' });
      }, 3000);
    }
  };

  const handleDownload = async (type: 'pdf' | 'docx' | 'md') => {
    if (!paper?.id || downloadState.status === 'preparing' || downloadState.status === 'downloading') return;

    simulateProgress(type);

    try {
      let response;
      let filename: string;
      let mimeType: string;

      const safeTitle = paper.title.replace(/[^\w\s]/gi, '_').substring(0, 50);

      switch (type) {
        case 'pdf':
          setDownloadState((prev) => ({ ...prev, status: 'downloading' }));
          response = await paperApi.downloadPdf(paper.id);
          mimeType = 'application/pdf';
          filename = `${safeTitle}.pdf`;
          break;
        case 'docx':
          setDownloadState((prev) => ({ ...prev, status: 'downloading' }));
          response = await paperApi.downloadDocx(paper.id);
          mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document';
          filename = `${safeTitle}.docx`;
          break;
        case 'md':
          setDownloadState((prev) => ({ ...prev, status: 'downloading' }));
          response = await paperApi.downloadMarkdown(paper.id);
          mimeType = 'text/markdown';
          filename = `${safeTitle}.md`;
          break;
        default:
          return;
      }

      // Create and trigger download
      const blob = new Blob([response.data], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      completeDownload(type, true);
    } catch (err: any) {
      console.error(`Failed to download ${type.toUpperCase()}:`, err);
      let errorMsg = getString(t('paperViewer.downloadProgress.failed') || 'Download failed');
      if (type === 'pdf') {
        errorMsg = getString(t('paperViewer.downloadProgress.pdfFailed') || 'PDF conversion failed. Please ensure Microsoft Word or LibreOffice is installed.');
      }
      completeDownload(type, false, errorMsg);
    }
  };

  const downloadDocx = () => handleDownload('docx');
  const downloadMarkdown = () => handleDownload('md');
  const downloadPdf = () => handleDownload('pdf');

  const closeDownloadToast = () => {
    setShowDownloadToast(false);
    setDownloadState({ type: null, status: 'idle', progress: 0, message: '' });
    if (downloadToastTimer.current) {
      clearTimeout(downloadToastTimer.current);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="card text-center py-12">
          <AlertCircle className="w-16 h-16 text-red-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">{getString(t('error'))}</h2>
          <p className="text-gray-500 dark:text-gray-400 mb-6">{error}</p>
          <Link to="/papers" className="btn-primary">
            {getString(t('paperViewer.backToPapers'))}
          </Link>
        </div>
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="max-w-2xl mx-auto">
        <div className="card text-center py-12">
          <FileText className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-gray-100 mb-2">
            {getString(t('paperViewer.paperNotFound'))}
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-6">
            {getString(t('paperViewer.paperNotFoundDesc'))}
          </p>
          <Link to="/papers" className="btn-primary">
            {getString(t('paperViewer.backToPapers'))}
          </Link>
        </div>
      </div>
    );
  }

  const isGenerating =
    paper.status === 'generating' ||
    paper.status === 'writing';

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            to="/papers"
            className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
          >
            <ChevronLeft className="w-5 h-5 text-gray-500 dark:text-gray-400" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{paper.title}</h1>
            <div className="flex items-center gap-3 mt-1">
              <span
                className={`px-2 py-0.5 rounded-full text-xs font-medium capitalize ${
                  paper.status === 'completed'
                    ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    : paper.status === 'failed'
                    ? 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200'
                    : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                }`}
              >
                {getString(t(`status.${paper.status}`))}
              </span>
              {paper.request?.language && (
                <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300">
                  {paper.request.language === 'chinese' ? '中文' : 'English'}
                </span>
              )}
              {polling && (
                <span className="flex items-center gap-1 text-sm text-blue-600 dark:text-blue-400">
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  {getString(t('paperViewer.processing'))}
                </span>
              )}
            </div>
          </div>
        </div>

        {paper.status === 'completed' && (
          <div className="flex items-center gap-2">
            <DownloadButton
              type="pdf"
              onClick={downloadPdf}
              isLoading={downloadState.type === 'pdf' && downloadState.status !== 'idle' && downloadState.status !== 'success' && downloadState.status !== 'error'}
              isSuccess={downloadState.type === 'pdf' && downloadState.status === 'success'}
              label="PDF"
              title={getString(t('paperViewer.downloadPdf'))}
            />
            <DownloadButton
              type="docx"
              onClick={downloadDocx}
              isLoading={downloadState.type === 'docx' && downloadState.status !== 'idle' && downloadState.status !== 'success' && downloadState.status !== 'error'}
              isSuccess={downloadState.type === 'docx' && downloadState.status === 'success'}
              label="DOCX"
              title={getString(t('paperViewer.downloadDocx'))}
            />
            <DownloadButton
              type="md"
              onClick={downloadMarkdown}
              isLoading={downloadState.type === 'md' && downloadState.status !== 'idle' && downloadState.status !== 'success' && downloadState.status !== 'error'}
              isSuccess={downloadState.type === 'md' && downloadState.status === 'success'}
              label="MD"
              title={getString(t('paperViewer.downloadMarkdown'))}
            />
          </div>
        )}
      </div>

      {/* Progress Steps */}
      {isGenerating && (
        <div className="card">
          <div className="flex items-center justify-between">
            {[getString(t('paperViewer.progressSteps.research')), getString(t('paperViewer.progressSteps.writing')), getString(t('paperViewer.progressSteps.complete'))].map((step, index) => {
              const isActive =
                (paper.status === 'generating' && index === 0) ||
                (paper.status === 'writing' && index === 1) ||
                (paper.status === 'completed' && index === 2);

              const isDone =
                (paper.status === 'writing' && index < 1) ||
                (paper.status === 'completed' && index < 2);

              return (
                <div key={index} className="flex items-center gap-2">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      isDone
                        ? 'bg-green-500 text-white'
                        : isActive
                        ? 'bg-blue-500 text-white animate-pulse'
                        : 'bg-gray-200 dark:bg-gray-700 text-gray-400 dark:text-gray-500'
                    }`}
                  >
                    {isDone ? (
                      <CheckCircle className="w-5 h-5" />
                    ) : (
                      <span className="text-sm font-medium">{index + 1}</span>
                    )}
                  </div>
                  <span
                    className={`text-sm font-medium ${
                      isActive || isDone ? 'text-gray-900 dark:text-gray-100' : 'text-gray-400 dark:text-gray-500'
                    }`}
                  >
                    {step}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="mt-4 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
            <div
              className="h-full bg-primary-600 dark:bg-primary-500 transition-all duration-500"
              style={{
                width:
                  paper.status === 'generating'
                    ? '33%'
                    : paper.status === 'writing'
                    ? '66%'
                    : '100%',
              }}
            />
          </div>
        </div>
      )}

      {/* Tab Navigation */}
      {paper.status === 'completed' && (
        <div className="card py-2 px-2">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setActiveTab('preview')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                activeTab === 'preview'
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <BookOpen className="w-4 h-4" />
              {paper.request?.language === 'chinese' ? '论文预览' : 'Paper Preview'}
            </button>
            <button
              onClick={() => setActiveTab('sources')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all ${
                activeTab === 'sources'
                  ? 'bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700'
              }`}
            >
              <FileSearch className="w-4 h-4" />
              {paper.request?.language === 'chinese' ? '引用与来源' : 'References & Sources'}
            </button>
          </div>
        </div>
      )}

      {/* Content */}
      {paper.status === 'completed' && paper.sections && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar - only show in preview tab */}
          {activeTab === 'preview' && (
            <div className="lg:col-span-1">
              <div className="card sticky top-24">
                {/* Preview Mode Toggle */}
                <div className="mb-4 pb-4 border-b border-gray-200 dark:border-gray-600">
                  <button
                    onClick={() => setFormattedPreview(!formattedPreview)}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-lg bg-primary-50 dark:bg-primary-900/30 hover:bg-primary-100 dark:hover:bg-primary-900/50 text-primary-700 dark:text-primary-300 transition-colors"
                  >
                    {formattedPreview ? (
                      <>
                        <EyeOff className="w-4 h-4" />
                        <span>{getString(t('paperViewer.plainPreview') || 'Plain Preview')}</span>
                      </>
                    ) : (
                      <>
                        <BookOpen className="w-4 h-4" />
                        <span>{getString(t('paperViewer.formattedPreview') || 'Formatted Preview')}</span>
                      </>
                    )}
                  </button>
                </div>
                <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-4">{getString(t('paperViewer.sections'))}</h3>
                <nav className="space-y-1">
                  {[
                    { key: 'abstract', label: getString(t('paperViewer.abstract')) },
                    { key: 'introduction', label: getString(t('paperViewer.introduction')) },
                    { key: 'literature_review', label: getString(t('paperViewer.literatureReview')) },
                    { key: 'methodology', label: getString(t('paperViewer.methodology')) },
                    { key: 'results', label: getString(t('paperViewer.results')) },
                    { key: 'discussion', label: getString(t('paperViewer.discussion')) },
                    { key: 'conclusion', label: getString(t('paperViewer.conclusion')) },
                    { key: 'references', label: getString(t('paperViewer.references')) },
                  ].map((section) => (
                    <a
                      key={section.key}
                      href={`#${section.key}`}
                      className="block px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-lg transition-colors"
                    >
                      {section.label}
                    </a>
                  ))}
                </nav>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className={activeTab === 'preview' ? 'lg:col-span-3' : 'lg:col-span-4'}>
            {activeTab === 'preview' ? (
              formattedPreview ? (
                <FormattedPaperPreview paper={paper} />
              ) : (
                <div className="card">
                  <article className="prose prose-lg max-w-none">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                      {`# ${paper.sections.title}

## Abstract

${paper.sections.abstract}

## Introduction

${paper.sections.introduction}

## Literature Review

${paper.sections.literature_review}

## Methodology

${paper.sections.methodology}

## Results

${paper.sections.results}

## Discussion

${paper.sections.discussion}

## Conclusion

${paper.sections.conclusion}

## References

${paper.sections.references}`}
                    </ReactMarkdown>
                  </article>
                </div>
              )
            ) : (
              <SourcesAndReferencesTab paper={paper} />
            )}
          </div>
        </div>
      )}

      {/* Download Progress Toast */}
      {showDownloadToast && (
        <DownloadToast
          state={downloadState}
          onClose={closeDownloadToast}
        />
      )}

    </div>
  );
}

// Download Button Component
interface DownloadButtonProps {
  type: 'pdf' | 'docx' | 'md';
  onClick: () => void;
  isLoading: boolean;
  isSuccess: boolean;
  label: string;
  title: string;
}

function DownloadButton({ type, onClick, isLoading, isSuccess, label, title }: DownloadButtonProps) {
  const getIcon = () => {
    if (isLoading) return <Loader2 className="w-4 h-4 animate-spin" />;
    if (isSuccess) return <CheckCircle className="w-4 h-4 text-green-500" />;
    if (type === 'md') return <FileCode className="w-4 h-4" />;
    return <FileText className="w-4 h-4" />;
  };

  const getClassName = () => {
    const baseClass = "flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all duration-200";
    if (isLoading) {
      return `${baseClass} bg-blue-50 text-blue-600 border border-blue-200 cursor-wait`;
    }
    if (isSuccess) {
      return `${baseClass} bg-green-50 text-green-600 border border-green-200 hover:bg-green-100`;
    }
    return `${baseClass} bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600 hover:border-gray-400 dark:hover:border-gray-500`;
  };

  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className={getClassName()}
      title={title}
    >
      {getIcon()}
      <span>{label}</span>
    </button>
  );
}

// Download Toast Component
interface DownloadToastProps {
  state: DownloadState;
  onClose: () => void;
}

function DownloadToast({ state, onClose }: DownloadToastProps) {
  const getStatusColor = () => {
    switch (state.status) {
      case 'success':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'preparing':
      case 'downloading':
        return 'bg-blue-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusIcon = () => {
    switch (state.status) {
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      case 'preparing':
      case 'downloading':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      default:
        return <Download className="w-5 h-5 text-gray-500 dark:text-gray-400" />;
    }
  };

  const getFileTypeLabel = () => {
    switch (state.type) {
      case 'pdf': return 'PDF';
      case 'docx': return 'DOCX';
      case 'md': return 'Markdown';
      default: return 'File';
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-4 fade-in duration-300">
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl border border-gray-200 dark:border-gray-600 overflow-hidden min-w-[320px]">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-700 border-b border-gray-100 dark:border-gray-600">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <span className="font-medium text-gray-700 dark:text-gray-200">
              {state.status === 'success' ? 'Download Complete' :
               state.status === 'error' ? 'Download Failed' :
               `Downloading ${getFileTypeLabel()}`}
            </span>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-full transition-colors"
          >
            <X className="w-4 h-4 text-gray-400 dark:text-gray-500" />
          </button>
        </div>

        {/* Progress Bar */}
        {(state.status === 'preparing' || state.status === 'downloading') && (
          <div className="px-4 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600 dark:text-gray-400">{state.message}</span>
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{state.progress}%</span>
            </div>
            <div className="h-2 bg-gray-100 dark:bg-gray-600 rounded-full overflow-hidden">
              <div
                className={`h-full ${getStatusColor()} transition-all duration-300 ease-out`}
                style={{ width: `${state.progress}%` }}
              />
            </div>
          </div>
        )}

        {/* Success/Error Message */}
        {(state.status === 'success' || state.status === 'error') && (
          <div className="px-4 py-3">
            <p className={`text-sm ${state.status === 'success' ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
              {state.message}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

// Formatted Paper Preview Component
interface FormattedPaperPreviewProps {
  paper: Paper;
}

function FormattedPaperPreview({ paper }: FormattedPaperPreviewProps) {
  const isChinese = paper.request?.language === 'chinese';

  if (!paper.sections) return null;

  const sections = [
    { key: 'abstract', title: isChinese ? '摘要' : 'Abstract', content: paper.sections.abstract },
    { key: 'introduction', title: isChinese ? '1 引言' : '1. Introduction', content: paper.sections.introduction },
    { key: 'literature_review', title: isChinese ? '2 文献综述' : '2. Literature Review', content: paper.sections.literature_review },
    { key: 'methodology', title: isChinese ? '3 研究方法' : '3. Methodology', content: paper.sections.methodology },
    { key: 'results', title: isChinese ? '4 研究结果' : '4. Results', content: paper.sections.results },
    { key: 'discussion', title: isChinese ? '5 讨论' : '5. Discussion', content: paper.sections.discussion },
    { key: 'conclusion', title: isChinese ? '6 结论' : '6. Conclusion', content: paper.sections.conclusion },
    { key: 'references', title: isChinese ? '参考文献' : 'References', content: paper.sections.references },
  ];

  return (
    <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-600 p-8 md:p-12">
      {/* Title */}
      <div className="text-center mb-8 pb-8 border-b-2 border-gray-200 dark:border-gray-600">
        <h1 className="text-2xl md:text-3xl font-bold text-gray-900 dark:text-gray-100 leading-tight">
          {paper.sections.title}
        </h1>
        <div className="mt-4 flex flex-wrap items-center justify-center gap-4 text-sm text-gray-600 dark:text-gray-400">
          {paper.request?.keywords && (
            <span>
              <strong>{isChinese ? '关键词：' : 'Keywords: '}</strong>
              {paper.request.keywords.join(isChinese ? '；' : '; ')}
            </span>
          )}
          {paper.request?.field && (
            <span>
              <strong>{isChinese ? '领域：' : 'Field: '}</strong>
              {paper.request.field}
            </span>
          )}
        </div>
      </div>

      {/* Sections */}
      <div className="space-y-6">
        {sections.map((section) => (
          section.content && (
            <section key={section.key} id={section.key} className="paper-section">
              {section.key === 'abstract' ? (
                // Special formatting for abstract
                <div className="bg-gray-50 dark:bg-gray-700 p-6 rounded-lg">
                  <h2 className="text-center text-lg font-bold mb-4 text-gray-900 dark:text-gray-100">
                    {section.title}
                  </h2>
                  <p className="text-justify leading-relaxed text-gray-700 dark:text-gray-300 indent-8">
                    {section.content}
                  </p>
                </div>
              ) : section.key === 'references' ? (
                // Special formatting for references
                <div className="pt-4 border-t border-gray-200 dark:border-gray-600">
                  <h2 className="text-center text-lg font-bold mb-4 text-gray-900 dark:text-gray-100">
                    {section.title}
                  </h2>
                  <div className="text-sm text-gray-700 dark:text-gray-300 space-y-2">
                    {section.content.split('\n\n').map((ref, idx) => (
                      <p key={idx} className="pl-4 -indent-4">
                        {ref}
                      </p>
                    ))}
                  </div>
                </div>
              ) : (
                // Standard section formatting
                <div className="pt-2">
                  <h2 className="text-lg font-bold mb-3 text-gray-900 dark:text-gray-100">
                    {section.title}
                  </h2>
                  <div className="prose prose-gray dark:prose-invert max-w-none">
                    {section.content.split('\n\n').map((paragraph, idx) => (
                      <p key={idx} className="text-justify leading-relaxed text-gray-700 dark:text-gray-300 mb-4 indent-8 first:indent-0">
                        {paragraph}
                      </p>
                    ))}
                  </div>
                </div>
              )}
            </section>
          )
        ))}
      </div>

      {/* Footer */}
      <div className="mt-12 pt-6 border-t border-gray-200 dark:border-gray-600 text-center text-sm text-gray-500 dark:text-gray-400">
        <p>
          {isChinese
            ? `生成日期：${new Date(paper.created_at).toLocaleDateString('zh-CN')}`
            : `Generated on: ${new Date(paper.created_at).toLocaleDateString('en-US')}`}
        </p>
      </div>
    </div>
  );
}

// Sources and References Tab Component
interface SourcesAndReferencesTabProps {
  paper: Paper;
}

function SourcesAndReferencesTab({ paper }: SourcesAndReferencesTabProps) {
  const isChinese = paper.request?.language === 'chinese';

  // Parse references from paper sections
  const parseReferences = (): Reference[] => {
    if (!paper.sections?.references) return [];

    const refs: Reference[] = [];
    const lines = paper.sections.references.split('\n\n');

    lines.forEach((line, index) => {
      if (!line.trim()) return;

      // Try to extract year (4 digits)
      const yearMatch = line.match(/\((\d{4})\)/) || line.match(/(\d{4})/);
      const year = yearMatch ? parseInt(yearMatch[1]) : new Date().getFullYear();

      // Try to extract authors (text before year, or first part)
      let authors: string[] = [];
      const authorMatch = line.match(/^([^(]+)/);
      if (authorMatch) {
        const authorStr = authorMatch[1].trim();
        // Split by & or and
        authors = authorStr.split(/\s*&\s*|\s+and\s+/i).map(a => a.trim()).filter(Boolean);
      }
      if (authors.length === 0) {
        authors = ['Unknown Author'];
      }

      // Extract title (between year and period, or just use remaining)
      let title = line;
      const titleMatch = line.match(/[."]([^."]+)[."]/);
      if (titleMatch) {
        title = titleMatch[1].trim();
      }

      refs.push({
        id: `ref-${index}`,
        title: title.substring(0, 100),
        authors,
        year,
        source: line,
      });
    });

    return refs;
  };

  const references = parseReferences();

  // Get images from paper (if available) or create sample for demo
  const images: PaperImage[] = paper.images || [];

  return (
    <div className="space-y-8">
      {/* References Section */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <BookOpenCheck className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {isChinese ? '参考文献' : 'References'}
          </h2>
          <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm">
            {references.length}
          </span>
        </div>

        {references.length > 0 ? (
          <div className="space-y-4">
            {references.map((ref, index) => (
              <div
                key={ref.id}
                className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border-l-4 border-primary-500 hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-3">
                  <span className="flex-shrink-0 w-8 h-8 flex items-center justify-center bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 rounded-full text-sm font-medium">
                    {index + 1}
                  </span>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                      {ref.title}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {ref.authors.join(', ')}
                      </span>
                      <span className="text-gray-400">|</span>
                      <span>{ref.year}</span>
                    </div>
                    <p className="mt-2 text-xs text-gray-500 dark:text-gray-500 break-all">
                      {ref.source}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <BookOpen className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>{isChinese ? '暂无参考文献信息' : 'No reference information available'}</p>
          </div>
        )}
      </div>

      {/* Images Section */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <ImageIcon className="w-6 h-6 text-primary-600 dark:text-primary-400" />
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
            {isChinese ? '图片与图表来源' : 'Images & Charts Sources'}
          </h2>
          <span className="px-2 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm">
            {images.length}
          </span>
        </div>

        {images.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {images.map((img) => (
              <div
                key={img.id}
                className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg hover:shadow-md transition-shadow"
              >
                <div className="flex items-start gap-3">
                  <div className="flex-shrink-0">
                    {img.source === 'ai_generated' ? (
                      <Sparkles className="w-8 h-8 text-purple-500" />
                    ) : img.source === 'chart' ? (
                      <BarChart3 className="w-8 h-8 text-blue-500" />
                    ) : img.source === 'web_search' ? (
                      <Globe className="w-8 h-8 text-green-500" />
                    ) : (
                      <FileText className="w-8 h-8 text-orange-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-gray-900 dark:text-gray-100 mb-1">
                      {img.caption || (isChinese ? '图片' : 'Image')}
                    </h3>
                    <div className="flex flex-wrap items-center gap-2">
                      <SourceBadge source={img.source} isChinese={isChinese} />
                      {img.width && img.height && (
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          {img.width} x {img.height}px
                        </span>
                      )}
                    </div>
                    {img.source_url && (
                      <a
                        href={img.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-2 inline-flex items-center gap-1 text-sm text-primary-600 dark:text-primary-400 hover:underline"
                      >
                        <ExternalLink className="w-3 h-3" />
                        {isChinese ? '查看来源' : 'View Source'}
                      </a>
                    )}
                    {img.source_title && (
                      <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                        {isChinese ? '来源: ' : 'Source: '}{img.source_title}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="space-y-4">
            {/* Sample image sources for demo */}
            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border-l-4 border-purple-500">
              <div className="flex items-start gap-3">
                <Sparkles className="w-8 h-8 text-purple-500" />
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {isChinese ? '图表 1: 研究流程图' : 'Figure 1: Research Flowchart'}
                  </h3>
                  <SourceBadge source="ai_generated" isChinese={isChinese} />
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {isChinese
                      ? '使用 AI 生成的 Mermaid 流程图，展示研究方法的整体流程'
                      : 'AI-generated Mermaid flowchart showing the research methodology workflow'}
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border-l-4 border-blue-500">
              <div className="flex items-start gap-3">
                <BarChart3 className="w-8 h-8 text-blue-500" />
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {isChinese ? '图表 2: 实验结果对比' : 'Figure 2: Experimental Results Comparison'}
                  </h3>
                  <SourceBadge source="chart" isChinese={isChinese} />
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {isChinese
                      ? '使用 Matplotlib 生成的数据可视化图表，基于论文中的实验数据'
                      : 'Data visualization chart generated using Matplotlib based on experimental data in the paper'}
                  </p>
                </div>
              </div>
            </div>

            <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg border-l-4 border-green-500">
              <div className="flex items-start gap-3">
                <Globe className="w-8 h-8 text-green-500" />
                <div>
                  <h3 className="font-medium text-gray-900 dark:text-gray-100">
                    {isChinese ? '图片 3: 概念示意图' : 'Figure 3: Conceptual Diagram'}
                  </h3>
                  <SourceBadge source="web_search" isChinese={isChinese} />
                  <p className="mt-1 text-sm text-gray-600 dark:text-gray-400">
                    {isChinese
                      ? '通过 DuckDuckGo/Unsplash 搜索获取的相关学术图片'
                      : 'Academic image sourced via DuckDuckGo/Unsplash search'}
                  </p>
                </div>
              </div>
            </div>

            <div className="text-center py-4 text-xs text-gray-500 dark:text-gray-500">
              {isChinese
                ? '注：以上仅为示例。实际论文中的图片来源将在生成后显示在此'
                : 'Note: Above are examples only. Actual image sources will appear here after paper generation'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Source Badge Component
function SourceBadge({ source, isChinese }: { source: string; isChinese: boolean }) {
  const configs: Record<string, { label: string; className: string }> = {
    ai_generated: {
      label: isChinese ? 'AI 生成' : 'AI Generated',
      className: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
    },
    web_search: {
      label: isChinese ? '网络搜索' : 'Web Search',
      className: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
    },
    pdf_extract: {
      label: isChinese ? 'PDF 提取' : 'PDF Extract',
      className: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
    },
    chart: {
      label: isChinese ? '数据图表' : 'Data Chart',
      className: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
    },
  };

  const config = configs[source] || configs.web_search;

  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${config.className}`}>
      {config.label}
    </span>
  );
}

import { useCallback, useEffect, useRef, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  Clock,
  Download,
  Edit3,
  ExternalLink,
  FileText,
  Loader2,
  RefreshCw,
  RotateCcw,
  Save,
  Sparkles,
  Square,
  X,
  XCircle,
  AlertCircle,
} from 'lucide-react';
import { errorMessage, paperApi, saveBlob, streamPaper } from '../services/api';
import type { Paper, ProgressEvent } from '../types';
import { SECTION_KEYS, SECTION_LABELS } from '../types';
import { useLanguage } from '../i18n';

type Tab = 'preview' | 'sources' | 'log';

const STAGE_LABEL: Record<string, [string, string]> = {
  queued: ['排队中', 'Queued'],
  researching: ['检索文献', 'Researching'],
  outlining: ['拟定提纲', 'Outlining'],
  writing: ['分节写作', 'Writing'],
  abstract: ['撰写摘要', 'Abstract'],
  references: ['整理参考文献', 'References'],
  completed: ['已完成', 'Completed'],
  failed: ['失败', 'Failed'],
  cancelled: ['已取消', 'Cancelled'],
  edit: ['编辑', 'Edit'],
};

export default function PaperViewer() {
  const { id } = useParams<{ id: string }>();
  const { language } = useLanguage();
  const zh = language === 'chinese';

  const [paper, setPaper] = useState<Paper | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [tab, setTab] = useState<Tab>('preview');
  const [events, setEvents] = useState<ProgressEvent[]>([]);
  const [downloading, setDownloading] = useState<string | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState('');
  const [regen, setRegen] = useState<{ key: string; instructions: string } | null>(null);
  const streamRef = useRef<(() => void) | null>(null);

  const load = useCallback(async () => {
    if (!id) return;
    try {
      const data = await paperApi.get(id);
      setPaper(data);
      if ((data.status === 'running' || data.status === 'queued') && !streamRef.current) {
        connectStream();
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }, [id]);

  const connectStream = useCallback(() => {
    if (!id) return;
    streamRef.current?.();
    streamRef.current = streamPaper(id, {
      onEvent: (event) => setEvents((prev) => [...prev.slice(-199), event]),
      onDone: () => {
        streamRef.current?.();
        streamRef.current = null;
        setTimeout(() => load(), 300);
      },
      onError: (message) => {
        streamRef.current = null;
        setEvents((prev) => [
          ...prev,
          { id: Date.now(), ts: new Date().toISOString(), stage: 'stream', level: 'warning', message },
        ]);
      },
    });
  }, [id, load]);

  useEffect(() => {
    load();
    return () => {
      streamRef.current?.();
      streamRef.current = null;
    };
  }, [load]);

  // While running, poll for stage/progress updates as a safety net in case the
  // event stream is blocked by a proxy.
  useEffect(() => {
    if (!paper || (paper.status !== 'running' && paper.status !== 'queued')) return;
    const timer = setInterval(() => {
      paperApi.get(paper.id).then(setPaper).catch(() => undefined);
    }, 4000);
    return () => clearInterval(timer);
  }, [paper]);

  const download = async (format: 'docx' | 'pdf' | 'md' | 'bib') => {
    if (!paper) return;
    setDownloading(format);
    try {
      const blob = await paperApi.download(paper.id, format);
      const base = (paper.title || 'paper').replace(/[\\/:*?"<>|]/g, '_').slice(0, 60);
      await saveBlob(blob, `${base}.${format}`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setDownloading(null);
    }
  };

  const doAction = async (kind: 'cancel' | 'retry') => {
    if (!paper) return;
    setBusy(kind);
    try {
      const updated = kind === 'cancel' ? await paperApi.cancel(paper.id) : await paperApi.retry(paper.id);
      setPaper(updated);
      if (kind === 'retry') {
        setEvents([]);
        setTab('log');
        connectStream();
      }
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  };

  const saveSection = async (key: string) => {
    if (!paper) return;
    setBusy(`save-${key}`);
    try {
      setPaper(await paperApi.updateSection(paper.id, key, draft));
      setEditing(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  };

  const regenerate = async () => {
    if (!paper || !regen) return;
    setBusy(`regen-${regen.key}`);
    try {
      const result = await paperApi.regenerateSection(paper.id, regen.key, regen.instructions);
      setPaper(result.paper);
      setRegen(null);
      setEditing(null);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!paper) {
    return (
      <div className="card text-center py-16">
        <FileText className="w-14 h-14 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">{zh ? '未找到论文' : 'Paper not found'}</h2>
        <p className="text-gray-500 mb-6">{error || (zh ? '这篇论文不存在或已被删除。' : 'It does not exist or was deleted.')}</p>
        <Link to="/papers" className="btn-primary inline-flex items-center gap-2">
          <ArrowLeft className="w-4 h-4" />{zh ? '返回列表' : 'Back to papers'}
        </Link>
      </div>
    );
  }

  const running = paper.status === 'running' || paper.status === 'queued';
  const sections = paper.sections || {};
  const sectionOrder = ['abstract', ...SECTION_KEYS] as string[];
  const stage = STAGE_LABEL[paper.stage] || [paper.stage, paper.stage];
  const stageText = zh ? stage[0] : stage[1];

  const statusBadge = () => {
    if (paper.status === 'completed') return { cls: 'bg-green-100 text-green-800 dark:bg-green-900/40 dark:text-green-300', icon: CheckCircle2, label: zh ? '已完成' : 'Completed' };
    if (paper.status === 'failed') return { cls: 'bg-red-100 text-red-800 dark:bg-red-900/40 dark:text-red-300', icon: XCircle, label: zh ? '失败' : 'Failed' };
    if (paper.status === 'cancelled') return { cls: 'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300', icon: XCircle, label: zh ? '已取消' : 'Cancelled' };
    return { cls: 'bg-blue-100 text-blue-800 dark:bg-blue-900/40 dark:text-blue-300', icon: Clock, label: zh ? '生成中' : 'Generating' };
  };
  const badge = statusBadge();
  const BadgeIcon = badge.icon;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <Link to="/papers" className="text-sm text-gray-500 hover:text-primary-600 flex items-center gap-1 mb-2">
            <ArrowLeft className="w-4 h-4" />{zh ? '返回论文列表' : 'Back to papers'}
          </Link>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 leading-snug">{paper.title}</h1>
          <div className="flex flex-wrap items-center gap-2 mt-3 text-sm">
            <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${badge.cls}`}>
              <BadgeIcon className="w-3.5 h-3.5" />{badge.label}
            </span>
            <span className="px-2.5 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">
              {paper.request?.language === 'chinese' ? '中文' : 'English'}
            </span>
            <span className="px-2.5 py-1 rounded-full text-xs bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 uppercase">
              {paper.request?.citation_style}
            </span>
            <span className="text-gray-500 dark:text-gray-400">
              {paper.word_count || 0} {zh ? '字' : 'words'} · {paper.references?.length || 0} {zh ? '篇参考文献' : 'references'}
            </span>
            {paper.meta?.model && <span className="text-gray-400 dark:text-gray-500">· {String(paper.meta.model)}</span>}
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          {running ? (
            <button onClick={() => doAction('cancel')} disabled={busy === 'cancel'} className="btn-secondary flex items-center gap-2">
              {busy === 'cancel' ? <Loader2 className="w-4 h-4 animate-spin" /> : <Square className="w-4 h-4" />}
              {zh ? '取消' : 'Cancel'}
            </button>
          ) : (
            <>
              <button onClick={() => doAction('retry')} disabled={busy === 'retry'} className="btn-secondary flex items-center gap-2">
                <RotateCcw className="w-4 h-4" />{zh ? '重新生成' : 'Regenerate'}
              </button>
              {paper.status === 'completed' && (
                <>
                  {(['docx', 'pdf', 'md', 'bib'] as const).map((fmt) => (
                    <button key={fmt} onClick={() => download(fmt)} disabled={downloading === fmt} className="btn-secondary flex items-center gap-2">
                      {downloading === fmt ? <Loader2 className="w-4 h-4 animate-spin" /> : <Download className="w-4 h-4" />}
                      {fmt === 'docx' ? 'Word' : fmt === 'pdf' ? 'PDF' : fmt === 'md' ? 'MD' : 'BibTeX'}
                    </button>
                  ))}
                </>
              )}
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 shrink-0" />{error}
          <button className="ml-auto" onClick={() => setError('')}><X className="w-4 h-4" /></button>
        </div>
      )}

      {running && (
        <div className="card border-primary-200 dark:border-primary-800 bg-primary-50/60 dark:bg-primary-900/20">
          <div className="flex items-center justify-between mb-2">
            <p className="font-medium text-primary-800 dark:text-primary-200 flex items-center gap-2">
              <Loader2 className="w-4 h-4 animate-spin" />{stageText}…
            </p>
            <span className="text-sm font-semibold text-primary-700 dark:text-primary-300">{paper.progress}%</span>
          </div>
          <div className="h-2 bg-white dark:bg-gray-700 rounded-full overflow-hidden">
            <div className="h-full bg-primary-500 transition-all duration-500" style={{ width: `${paper.progress}%` }} />
          </div>
          <p className="text-xs text-primary-700/80 dark:text-primary-300/80 mt-2">
            {zh
              ? '生成过程会实时显示在「过程日志」中；每写完一节会自动保存草稿。'
              : 'Live progress appears in the Log tab; each finished section is saved automatically.'}
          </p>
        </div>
      )}

      {paper.status === 'failed' && paper.error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300">
          <p className="font-medium mb-1">{zh ? '生成失败' : 'Generation failed'}</p>
          <p>{paper.error}</p>
        </div>
      )}

      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {([
          ['preview', zh ? '正文' : 'Manuscript'],
          ['sources', zh ? '参考文献' : 'References'],
          ['log', zh ? '过程日志' : 'Log'],
        ] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 -mb-px transition-colors ${
              tab === key
                ? 'border-primary-600 text-primary-700 dark:text-primary-400 dark:border-primary-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700'
            }`}
          >
            {label}
            {key === 'log' && events.length > 0 && <span className="ml-1.5 text-xs text-gray-400">{events.length}</span>}
          </button>
        ))}
      </div>

      {tab === 'preview' && (
        <div className="space-y-4">
          {sectionOrder.map((key) => {
            const content = sections[key];
            const isEditing = editing === key;
            const label = SECTION_LABELS[key]?.[zh ? 'zh' : 'en'] || key;
            const isBusy = busy === `regen-${key}` || busy === `save-${key}`;
            return (
              <section key={key} className="card">
                <div className="flex items-center justify-between mb-3 gap-2">
                  <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">{label}</h2>
                  {!running && (
                    <div className="flex items-center gap-3">
                      <button
                        onClick={() => { setEditing(isEditing ? null : key); setDraft(content || ''); }}
                        className="text-sm text-gray-500 hover:text-primary-600 flex items-center gap-1"
                      >
                        <Edit3 className="w-3.5 h-3.5" />{isEditing ? (zh ? '收起' : 'Close') : (zh ? '编辑' : 'Edit')}
                      </button>
                      <button
                        onClick={() => setRegen({ key, instructions: '' })}
                        disabled={isBusy}
                        className="text-sm text-gray-500 hover:text-primary-600 flex items-center gap-1 disabled:opacity-50"
                      >
                        {busy === `regen-${key}` ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <RefreshCw className="w-3.5 h-3.5" />}
                        {zh ? '重写' : 'Rewrite'}
                      </button>
                    </div>
                  )}
                </div>

                {isEditing ? (
                  <div className="space-y-3">
                    <textarea
                      value={draft}
                      onChange={(e) => setDraft(e.target.value)}
                      className="input min-h-[220px] font-normal leading-relaxed"
                    />
                    <div className="flex justify-end gap-2">
                      <button onClick={() => setEditing(null)} className="btn-secondary">{zh ? '取消' : 'Cancel'}</button>
                      <button onClick={() => saveSection(key)} disabled={isBusy} className="btn-primary flex items-center gap-2">
                        {isBusy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Save className="w-4 h-4" />}
                        {zh ? '保存' : 'Save'}
                      </button>
                    </div>
                  </div>
                ) : content ? (
                  <div className="markdown-content text-[15px]">
                    <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                  </div>
                ) : (
                  <p className="text-sm text-gray-400 dark:text-gray-500 italic">
                    {running ? (zh ? '正在生成…' : 'Generating…') : (zh ? '（本节暂无内容）' : '(empty)')}
                  </p>
                )}

                {key === 'abstract' && (paper.request?.keywords?.length || 0) > 0 && (
                  <p className="mt-3 text-sm text-gray-500 dark:text-gray-400">
                    <span className="font-medium">{zh ? '关键词' : 'Keywords'}:</span> {paper.request.keywords?.join('; ')}
                  </p>
                )}
              </section>
            );
          })}

          {paper.outline?.research_questions && paper.outline.research_questions.length > 0 && (
            <section className="card bg-gray-50 dark:bg-gray-800/60">
              <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
                <Sparkles className="w-4 h-4" />{zh ? '研究问题（由提纲阶段确定）' : 'Research questions (from outlining)'}
              </h2>
              <ul className="list-disc pl-5 text-sm text-gray-600 dark:text-gray-400 space-y-1">
                {paper.outline.research_questions.map((q: string, i: number) => <li key={i}>{q}</li>)}
              </ul>
            </section>
          )}
        </div>
      )}

      {tab === 'sources' && (
        <div className="card">
          {paper.references && paper.references.length > 0 ? (
            <ol className="space-y-4">
              {paper.references.map((ref, index) => (
                <li key={index} className="flex gap-3">
                  <span className="shrink-0 w-6 h-6 rounded-full bg-primary-50 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 text-xs font-semibold flex items-center justify-center">
                    {index + 1}
                  </span>
                  <div className="min-w-0">
                    <p className="font-medium text-gray-900 dark:text-gray-100">{ref.title}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-0.5">
                      {(ref.authors || []).slice(0, 5).join(', ')}{ref.authors && ref.authors.length > 5 ? ' et al.' : ''}
                      {ref.year ? ` · ${ref.year}` : ''}{ref.venue ? ` · ${ref.venue}` : ''}
                    </p>
                    <div className="flex items-center gap-3 mt-1 text-xs">
                      {ref.source && <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">{ref.source}</span>}
                      {typeof ref.citations === 'number' && <span className="text-gray-400">↗ {ref.citations}</span>}
                      {(ref.doi || ref.url) && (
                        <a href={ref.doi ? `https://doi.org/${ref.doi}` : ref.url} target="_blank" rel="noreferrer" className="text-primary-600 dark:text-primary-400 inline-flex items-center gap-1">
                          <ExternalLink className="w-3 h-3" />{zh ? '原文' : 'Open'}
                        </a>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ol>
          ) : (
            <div className="text-center text-gray-500 dark:text-gray-400 py-8">
              <BookOpen className="w-10 h-10 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
              {zh ? '本篇没有检索到外部文献，正文未做引用标注。' : 'No external references were retrieved for this paper.'}
            </div>
          )}
        </div>
      )}

      {tab === 'log' && (
        <div className="card">
          {events.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400 py-8">
              {running ? (zh ? '等待第一条日志…' : 'Waiting for the first event…') : (zh ? '本次会话暂无日志。' : 'No log in this session.')}
            </p>
          ) : (
            <ul className="space-y-2 font-mono text-xs">
              {events.map((event) => (
                <li key={`${event.id}-${event.ts}`} className="flex gap-3">
                  <span className="text-gray-400 shrink-0">{new Date(event.ts).toLocaleTimeString()}</span>
                  <span className={`shrink-0 uppercase ${event.level === 'error' ? 'text-red-500' : event.level === 'warning' ? 'text-amber-500' : 'text-primary-500'}`}>
                    {event.stage}
                  </span>
                  <span className={event.level === 'error' ? 'text-red-600 dark:text-red-400' : 'text-gray-700 dark:text-gray-300'}>{event.message}</span>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}

      {regen && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center p-4 z-50" onClick={() => setRegen(null)}>
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-xl max-w-lg w-full p-6" onClick={(e) => e.stopPropagation()}>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              {zh ? '重写本节' : 'Rewrite section'} · {SECTION_LABELS[regen.key]?.[zh ? 'zh' : 'en'] || regen.key}
            </h3>
            <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">
              {zh ? '可以补充写作要求；模型会参考其他章节保持前后一致。' : 'Add optional guidance; the model keeps consistency with the other sections.'}
            </p>
            <textarea
              className="input min-h-[100px]"
              value={regen.instructions}
              onChange={(e) => setRegen({ ...regen, instructions: e.target.value })}
              placeholder={zh ? '例如：更突出方法局限，减少描述性内容' : 'e.g. emphasise limitations, less descriptive'}
            />
            <div className="flex justify-end gap-2 mt-4">
              <button onClick={() => setRegen(null)} className="btn-secondary">{zh ? '取消' : 'Cancel'}</button>
              <button onClick={regenerate} disabled={busy === `regen-${regen.key}`} className="btn-primary flex items-center gap-2">
                {busy === `regen-${regen.key}` ? <Loader2 className="w-4 h-4 animate-spin" /> : <RefreshCw className="w-4 h-4" />}
                {zh ? '开始重写' : 'Rewrite'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

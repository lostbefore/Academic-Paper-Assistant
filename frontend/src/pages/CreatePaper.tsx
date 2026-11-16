import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Loader2,
  AlertCircle,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  FileText,
  Search,
} from 'lucide-react';
import { errorMessage, metaApi, paperApi } from '../services/api';
import type { CitationStyle, PaperRequest } from '../types';
import { useLanguage } from '../i18n';

export default function CreatePaper() {
  const { t, language } = useLanguage();
  const zh = language === 'chinese';
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [styles, setStyles] = useState<Record<string, CitationStyle>>({});
  const [form, setForm] = useState<PaperRequest>({
    title: '',
    field: '',
    keywords: [],
    length: 'medium',
    citation_style: 'gbt7714',
    language: 'chinese',
    target_words: 6000,
    reference_count: 12,
    instructions: '',
  });
  const [keywordInput, setKeywordInput] = useState('');

  useEffect(() => {
    metaApi.styles().then(setStyles).catch(() => undefined);
  }, []);

  useEffect(() => {
    setForm((f) => ({ ...f, language }));
  }, [language]);

  const lengthPresets = useMemo(
    () => [
      { value: 'short' as const, label: zh ? '短篇' : 'Short', words: 3000 },
      { value: 'medium' as const, label: zh ? '中篇' : 'Medium', words: 6000 },
      { value: 'long' as const, label: zh ? '长篇' : 'Long', words: 9000 },
    ],
    [zh],
  );

  const addKeyword = () => {
    const value = keywordInput.trim();
    if (value && !form.keywords.includes(value) && form.keywords.length < 12) {
      setForm({ ...form, keywords: [...form.keywords, value] });
      setKeywordInput('');
    }
  };

  const submit = async () => {
    if (!form.title.trim() || !form.field.trim()) {
      setError(t('createPaper.requiredFields') as string);
      return;
    }
    setLoading(true);
    setError('');
    try {
      const paper = await paperApi.create(form);
      navigate(`/papers/${paper.id}`);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    { n: 1, title: zh ? '选题' : 'Topic' },
    { n: 2, title: zh ? '关键词' : 'Keywords' },
    { n: 3, title: zh ? '成稿设置' : 'Settings' },
  ];

  return (
    <div className="max-w-3xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{t('createPaper.title') as string}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2">{t('createPaper.subtitle') as string}</p>
      </div>

      <div className="flex items-center mb-8">
        {steps.map((s, index) => (
          <div key={s.n} className="flex items-center">
            <div
              className={`w-9 h-9 rounded-full flex items-center justify-center text-sm font-semibold ${
                step >= s.n ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
              }`}
            >
              {s.n}
            </div>
            <span className="ml-2 text-sm font-medium text-gray-700 dark:text-gray-300 hidden sm:inline">{s.title}</span>
            {index < steps.length - 1 && <ChevronRight className="w-4 h-4 text-gray-400 mx-3" />}
          </div>
        ))}
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3 text-red-700 dark:text-red-300">
          <AlertCircle className="w-5 h-5 shrink-0" />{error}
        </div>
      )}

      <div className="card">
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <label className="label">{t('createPaper.paperTitle') as string} <span className="text-red-500">*</span></label>
              <input
                className="input"
                value={form.title}
                onChange={(e) => setForm({ ...form, title: e.target.value })}
                placeholder={t('createPaper.paperTitlePlaceholder') as string}
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t('createPaper.paperTitleHelp') as string}</p>
            </div>
            <div>
              <label className="label">{t('createPaper.researchField') as string} <span className="text-red-500">*</span></label>
              <input
                className="input"
                value={form.field}
                onChange={(e) => setForm({ ...form, field: e.target.value })}
                placeholder={t('createPaper.researchFieldPlaceholder') as string}
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t('createPaper.researchFieldHelp') as string}</p>
            </div>
            <div>
              <label className="label">{zh ? '写作要求（可选）' : 'Extra requirements (optional)'}</label>
              <textarea
                className="input min-h-[90px]"
                value={form.instructions}
                onChange={(e) => setForm({ ...form, instructions: e.target.value })}
                placeholder={zh ? '例如：采用混合研究方法；重点讨论政策含义；面向教育技术学期刊' : 'e.g. use a mixed-methods design; emphasise policy implications'}
              />
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div>
              <label className="label">{t('createPaper.researchKeywords') as string}</label>
              <div className="flex gap-2">
                <input
                  className="input"
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      e.preventDefault();
                      addKeyword();
                    }
                  }}
                  placeholder={t('createPaper.keywordPlaceholder') as string}
                />
                <button type="button" onClick={addKeyword} className="btn-secondary whitespace-nowrap">
                  {t('create') as string}
                </button>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t('createPaper.keywordHelp') as string}</p>
            </div>

            {form.keywords.length > 0 ? (
              <div className="flex flex-wrap gap-2">
                {form.keywords.map((keyword) => (
                  <span key={keyword} className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 rounded-full text-sm">
                    {keyword}
                    <button
                      type="button"
                      onClick={() => setForm({ ...form, keywords: form.keywords.filter((k) => k !== keyword) })}
                      className="hover:text-primary-900 dark:hover:text-primary-100"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            ) : (
              <div className="p-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center text-gray-500 dark:text-gray-400">
                <Sparkles className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>{t('createPaper.noKeywords') as string}</p>
              </div>
            )}

            <p className="text-xs text-gray-500 dark:text-gray-400 flex items-center gap-2">
              <Search className="w-4 h-4" />
              {zh
                ? '生成时系统会用标题与关键词到 OpenAlex / Crossref / arXiv 检索真实文献，并据此标注引用。'
                : 'The title and keywords are used to retrieve real papers from OpenAlex / Crossref / arXiv for citations.'}
            </p>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div>
              <label className="label">{t('createPaper.language') as string}</label>
              <div className="grid grid-cols-2 gap-3">
                {(['chinese', 'english'] as const).map((value) => (
                  <button
                    key={value}
                    type="button"
                    onClick={() => setForm({ ...form, language: value })}
                    className={`p-4 rounded-lg border-2 text-center ${
                      form.language === value
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                    }`}
                  >
                    <p className="font-semibold text-gray-900 dark:text-gray-100">{value === 'chinese' ? '中文' : 'English'}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{value === 'chinese' ? '生成中文论文' : 'Generate in English'}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">{t('createPaper.paperLength') as string}</label>
              <div className="grid grid-cols-3 gap-3">
                {lengthPresets.map((preset) => (
                  <button
                    key={preset.value}
                    type="button"
                    onClick={() => setForm({ ...form, length: preset.value, target_words: preset.words })}
                    className={`p-3 rounded-lg border-2 text-center ${
                      form.length === preset.value
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                    }`}
                  >
                    <p className="font-semibold text-gray-900 dark:text-gray-100">{preset.label}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">~{preset.words}</p>
                  </button>
                ))}
              </div>
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-300">
                  <span>{zh ? '目标字数' : 'Target length'}</span>
                  <span className="font-semibold text-primary-600 dark:text-primary-400">
                    {form.target_words} {zh ? '字' : 'words'}
                  </span>
                </div>
                <input
                  type="range"
                  min={1500}
                  max={12000}
                  step={500}
                  value={form.target_words}
                  onChange={(e) => setForm({ ...form, target_words: Number(e.target.value) })}
                  className="w-full mt-2 accent-primary-600"
                />
              </div>
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm text-gray-600 dark:text-gray-300">
                  <span>{zh ? '引用文献数' : 'References'}</span>
                  <span className="font-semibold text-primary-600 dark:text-primary-400">{form.reference_count}</span>
                </div>
                <input
                  type="range"
                  min={4}
                  max={30}
                  step={1}
                  value={form.reference_count}
                  onChange={(e) => setForm({ ...form, reference_count: Number(e.target.value) })}
                  className="w-full mt-2 accent-primary-600"
                />
              </div>
            </div>

            <div>
              <label className="label">{t('createPaper.citationStyle') as string}</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {Object.entries(styles).map(([key, style]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setForm({ ...form, citation_style: key as PaperRequest['citation_style'] })}
                    className={`p-4 rounded-lg border-2 text-left ${
                      form.citation_style === key
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-4 h-4 text-primary-600 dark:text-primary-400" />
                      <p className="font-semibold text-gray-900 dark:text-gray-100">{style.name}</p>
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 line-clamp-2">{style.example}</p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-700">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1 || loading}
            className="btn-secondary flex items-center gap-2 disabled:opacity-50"
          >
            <ChevronLeft className="w-4 h-4" />{t('previous') as string}
          </button>
          {step < 3 ? (
            <button onClick={() => setStep(step + 1)} className="btn-primary flex items-center gap-2">
              {t('next') as string}<ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button onClick={submit} disabled={loading} className="btn-primary flex items-center gap-2 disabled:opacity-60">
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileText className="w-4 h-4" />}
              {loading ? (t('createPaper.generating') as string) : (t('createPaper.generatePaper') as string)}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

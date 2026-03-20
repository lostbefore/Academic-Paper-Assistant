import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  BookOpen,
  Loader2,
  AlertCircle,
  Sparkles,
  ChevronRight,
  ChevronLeft,
  FileText,
} from 'lucide-react';
import { paperApi } from '../services/api';
import { PaperRequest, CitationStyle } from '../types';
import { useLanguage } from '../i18n';

export default function CreatePaper() {
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [styles, setStyles] = useState<Record<string, CitationStyle>>({});
  const [formData, setFormData] = useState<PaperRequest>({
    title: '',
    keywords: [],
    field: '',
    length: 'medium',
    citation_style: 'gbt7714',
    language: 'english',
  });
  const [keywordInput, setKeywordInput] = useState('');

  useEffect(() => {
    loadStyles();
  }, []);

  const loadStyles = async () => {
    try {
      const data = await paperApi.getCitationStyles();
      setStyles(data);
    } catch (err) {
      console.error('Failed to load styles:', err);
    }
  };

  const handleSubmit = async () => {
    if (!formData.title || !formData.field) {
      setError(t('createPaper.requiredFields'));
      return;
    }

    setLoading(true);
    setError('');

    try {
      const paper = await paperApi.createPaper(formData);
      navigate(`/papers/${paper.id}`);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create paper');
    } finally {
      setLoading(false);
    }
  };

  const addKeyword = () => {
    if (keywordInput.trim() && !formData.keywords.includes(keywordInput.trim())) {
      setFormData({
        ...formData,
        keywords: [...formData.keywords, keywordInput.trim()],
      });
      setKeywordInput('');
    }
  };

  const removeKeyword = (keyword: string) => {
    setFormData({
      ...formData,
      keywords: formData.keywords.filter((k) => k !== keyword),
    });
  };

  const steps = [
    { number: 1, title: t('createPaper.steps.basicInfo.title'), description: t('createPaper.steps.basicInfo.desc') },
    { number: 2, title: t('createPaper.steps.keywords.title'), description: t('createPaper.steps.keywords.desc') },
    { number: 3, title: t('createPaper.steps.settings.title'), description: t('createPaper.steps.settings.desc') },
  ];

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">{t('createPaper.title')}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-2">
          {t('createPaper.subtitle')}
        </p>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center mb-8">
        {steps.map((s, index) => (
          <div key={s.number} className="flex items-center">
            <div
              className={`w-10 h-10 rounded-full flex items-center justify-center font-semibold transition-colors ${
                step >= s.number
                  ? 'bg-primary-600 text-white'
                  : 'bg-gray-200 dark:bg-gray-700 text-gray-500 dark:text-gray-400'
              }`}
            >
              {s.number}
            </div>
            <div className="ml-3 hidden sm:block">
              <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{s.title}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">{s.description}</p>
            </div>
            {index < steps.length - 1 && (
              <ChevronRight className="w-5 h-5 text-gray-400 dark:text-gray-500 mx-4" />
            )}
          </div>
        ))}
      </div>

      {/* Error */}
      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3 text-red-700 dark:text-red-400">
          <AlertCircle className="w-5 h-5" />
          {error}
        </div>
      )}

      {/* Form */}
      <div className="card">
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <label className="label">
                {t('createPaper.paperTitle')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                className="input"
                placeholder={t('createPaper.paperTitlePlaceholder') as string}
                value={formData.title}
                onChange={(e) =>
                  setFormData({ ...formData, title: e.target.value })
                }
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {t('createPaper.paperTitleHelp')}
              </p>
            </div>

            <div>
              <label className="label">
                {t('createPaper.researchField')} <span className="text-red-500">*</span>
              </label>
              <input
                type="text"
                className="input"
                placeholder={t('createPaper.researchFieldPlaceholder') as string}
                value={formData.field}
                onChange={(e) =>
                  setFormData({ ...formData, field: e.target.value })
                }
              />
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {t('createPaper.researchFieldHelp')}
              </p>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-6">
            <div>
              <label className="label">{t('createPaper.researchKeywords')}</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  className="input"
                  placeholder={t('createPaper.keywordPlaceholder') as string}
                  value={keywordInput}
                  onChange={(e) => setKeywordInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && addKeyword()}
                />
                <button
                  type="button"
                  onClick={addKeyword}
                  className="btn-primary whitespace-nowrap"
                >
                  {t('create')}
                </button>
              </div>
              <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                {t('createPaper.keywordHelp')}
              </p>
            </div>

            {formData.keywords.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {formData.keywords.map((keyword) => (
                  <span
                    key={keyword}
                    className="inline-flex items-center gap-1 px-3 py-1 bg-primary-100 dark:bg-primary-900/50 text-primary-700 dark:text-primary-300 rounded-full text-sm"
                  >
                    {keyword}
                    <button
                      onClick={() => removeKeyword(keyword)}
                      className="hover:text-primary-900 dark:hover:text-primary-200"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            )}

            {formData.keywords.length === 0 && (
              <div className="p-4 bg-gray-50 dark:bg-gray-700 rounded-lg text-center text-gray-500 dark:text-gray-400">
                <Sparkles className="w-8 h-8 mx-auto mb-2 text-gray-400 dark:text-gray-500" />
                <p>{t('createPaper.noKeywords')}</p>
              </div>
            )}
          </div>
        )}

        {step === 3 && (
          <div className="space-y-6">
            <div>
              <label className="label">{t('createPaper.language')}</label>
              <div className="grid grid-cols-2 gap-4">
                {[
                  { value: 'english', label: t('createPaper.languages.english.label'), desc: t('createPaper.languages.english.desc') },
                  { value: 'chinese', label: t('createPaper.languages.chinese.label'), desc: t('createPaper.languages.chinese.desc') },
                ].map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        language: option.value as PaperRequest['language'],
                      })
                    }
                    className={`p-4 rounded-lg border-2 text-center transition-all ${
                      formData.language === option.value
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    <p className="font-semibold text-gray-900 dark:text-gray-100">
                      {option.label}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{option.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">{t('createPaper.paperLength')}</label>
              <div className="grid grid-cols-3 gap-4">
                {[
                  { value: 'short', label: t('createPaper.lengths.short.label'), desc: t('createPaper.lengths.short.desc') },
                  { value: 'medium', label: t('createPaper.lengths.medium.label'), desc: t('createPaper.lengths.medium.desc') },
                  { value: 'long', label: t('createPaper.lengths.long.label'), desc: t('createPaper.lengths.long.desc') },
                ].map((option) => (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        length: option.value as PaperRequest['length'],
                      })
                    }
                    className={`p-4 rounded-lg border-2 text-center transition-all ${
                      formData.length === option.value
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    <p className="font-semibold text-gray-900 dark:text-gray-100">
                      {option.label}
                    </p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{option.desc}</p>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">{t('createPaper.citationStyle')}</label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {Object.entries(styles).map(([key, style]) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() =>
                      setFormData({
                        ...formData,
                        citation_style: key as PaperRequest['citation_style'],
                      })
                    }
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      formData.citation_style === key
                        ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/30'
                        : 'border-gray-200 dark:border-gray-600 hover:border-gray-300 dark:hover:border-gray-500'
                    }`}
                  >
                    <div className="flex items-center gap-2">
                      <BookOpen className="w-5 h-5 text-primary-600 dark:text-primary-400" />
                      <p className="font-semibold text-gray-900 dark:text-gray-100">
                        {style.name}
                      </p>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                      {style.description}
                    </p>
                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-2 truncate">
                      Example: {style.example}
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200 dark:border-gray-600">
          <button
            onClick={() => setStep(Math.max(1, step - 1))}
            disabled={step === 1 || loading}
            className="btn-secondary flex items-center gap-2 disabled:opacity-50"
          >
            <ChevronLeft className="w-4 h-4" />
            {t('previous')}
          </button>

          {step < 3 ? (
            <button
              onClick={() => setStep(step + 1)}
              className="btn-primary flex items-center gap-2"
            >
              {t('next')}
              <ChevronRight className="w-4 h-4" />
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="btn-primary flex items-center gap-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  {t('createPaper.generating')}
                </>
              ) : (
                <>
                  <FileText className="w-4 h-4" />
                  {t('createPaper.generatePaper')}
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

import { useState } from 'react';
import { Search, Loader2, ExternalLink, AlertCircle, BookOpen } from 'lucide-react';
import { errorMessage, literatureApi } from '../services/api';
import type { Reference } from '../types';
import { useLanguage } from '../i18n';

const EXAMPLES = [
  { zh: '大语言模型 学术写作', en: 'large language model academic writing' },
  { zh: '生成式人工智能 高等教育', en: 'generative AI higher education' },
  { zh: '学术诚信 科研伦理', en: 'academic integrity research ethics' },
];

export default function Literature() {
  const { language } = useLanguage();
  const zh = language === 'chinese';
  const [query, setQuery] = useState('');
  const [yearFrom, setYearFrom] = useState<number | ''>('');
  const [results, setResults] = useState<Reference[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searched, setSearched] = useState(false);

  const search = async (q = query) => {
    const text = q.trim();
    if (text.length < 2) return;
    setLoading(true);
    setError('');
    setSearched(true);
    try {
      setResults(await literatureApi.search(text, 15, yearFrom === '' ? undefined : Number(yearFrom)));
    } catch (err) {
      setError(errorMessage(err));
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{zh ? '文献检索' : 'Literature Search'}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          {zh
            ? '同时检索 OpenAlex、Crossref 与 arXiv，结果按相关度合并去重，可直接用于选题调研。'
            : 'Searches OpenAlex, Crossref and arXiv in parallel, merges and de-duplicates results by relevance.'}
        </p>
      </div>

      <div className="card">
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <Search className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
            <input
              className="input pl-9"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && search()}
              placeholder={zh ? '输入主题、关键词或论文标题…' : 'Topic, keywords or a paper title…'}
            />
          </div>
          <input
            className="input sm:w-32"
            type="number"
            min={1900}
            max={2100}
            value={yearFrom}
            onChange={(e) => setYearFrom(e.target.value === '' ? '' : Number(e.target.value))}
            placeholder={zh ? '起始年份' : 'Year from'}
          />
          <button onClick={() => search()} disabled={loading} className="btn-primary flex items-center justify-center gap-2 sm:w-32">
            {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            {zh ? '检索' : 'Search'}
          </button>
        </div>
        <div className="flex flex-wrap gap-2 mt-3">
          {EXAMPLES.map((example) => (
            <button
              key={example.en}
              onClick={() => { const q = zh ? example.zh : example.en; setQuery(q); search(q); }}
              className="text-xs px-2.5 py-1 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 hover:bg-primary-50 dark:hover:bg-primary-900/30"
            >
              {zh ? example.zh : example.en}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />{error}
        </div>
      )}

      {loading && (
        <div className="card text-center py-12 text-gray-500">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-3 text-primary-500" />
          {zh ? '正在检索多个数据源…' : 'Querying sources…'}
        </div>
      )}

      {!loading && searched && results.length === 0 && (
        <div className="card text-center py-12 text-gray-500">
          <BookOpen className="w-10 h-10 mx-auto mb-3 text-gray-300" />
          {zh ? '没有找到匹配的文献，试试更换关键词或放宽年份。' : 'No matches. Try different keywords or a wider year range.'}
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {zh ? `共 ${results.length} 条结果` : `${results.length} results`}
          </p>
          {results.map((ref, index) => (
            <div key={`${ref.title}-${index}`} className="card">
              <div className="flex items-start gap-3">
                <span className="shrink-0 w-7 h-7 rounded-full bg-primary-50 dark:bg-primary-900/40 text-primary-700 dark:text-primary-300 text-xs font-semibold flex items-center justify-center">
                  {index + 1}
                </span>
                <div className="min-w-0 flex-1">
                  <p className="font-semibold text-gray-900 dark:text-gray-100">{ref.title}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    {(ref.authors || []).slice(0, 4).join(', ')}{ref.authors && ref.authors.length > 4 ? ' et al.' : ''}
                    {ref.year ? ` · ${ref.year}` : ''}{ref.venue ? ` · ${ref.venue}` : ''}
                  </p>
                  {ref.abstract && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 line-clamp-3">{ref.abstract}</p>
                  )}
                  <div className="flex flex-wrap items-center gap-3 mt-2 text-xs">
                    <span className="px-2 py-0.5 rounded bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300">{ref.source}</span>
                    {typeof ref.citations === 'number' && <span className="text-gray-400">↗ {ref.citations}</span>}
                    {(ref.doi || ref.url) && (
                      <a href={ref.doi ? `https://doi.org/${ref.doi}` : ref.url} target="_blank" rel="noreferrer" className="text-primary-600 dark:text-primary-400 inline-flex items-center gap-1">
                        <ExternalLink className="w-3 h-3" />{zh ? '查看原文' : 'Open'}
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

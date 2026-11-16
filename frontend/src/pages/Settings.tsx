import { useEffect, useState } from 'react';
import { CheckCircle2, XCircle, Loader2, Cpu, Database, Globe, User as UserIcon, Plug } from 'lucide-react';
import { errorMessage, metaApi } from '../services/api';
import type { ApiStatus } from '../types';
import { useLanguage } from '../i18n';
import { useAuth } from '../contexts/AuthContext';

export default function SettingsPage() {
  const { language } = useLanguage();
  const { user } = useAuth();
  const zh = language === 'chinese';
  const [status, setStatus] = useState<ApiStatus | null>(null);
  const [health, setHealth] = useState<Record<string, unknown> | null>(null);
  const [testing, setTesting] = useState(false);
  const [testResult, setTestResult] = useState<{ ok: boolean; message: string } | null>(null);
  const [error, setError] = useState('');

  useEffect(() => {
    Promise.all([metaApi.status(), metaApi.health()])
      .then(([s, h]) => { setStatus(s); setHealth(h as Record<string, unknown>); })
      .catch((err) => setError(errorMessage(err)));
  }, []);

  const testLLM = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      setTestResult(await metaApi.testLLM());
    } catch (err) {
      setTestResult({ ok: false, message: errorMessage(err) });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{zh ? '设置' : 'Settings'}</h1>
        <p className="text-gray-500 dark:text-gray-400 mt-1">
          {zh ? '查看运行环境与模型连通性。' : 'Runtime configuration and model connectivity.'}
        </p>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300">{error}</div>
      )}

      <section className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
          <UserIcon className="w-5 h-5 text-primary-600" />{zh ? '账户' : 'Account'}
        </h2>
        <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
          <div>
            <dt className="text-gray-500 dark:text-gray-400">{zh ? '姓名' : 'Name'}</dt>
            <dd className="font-medium text-gray-900 dark:text-gray-100 mt-0.5">{user?.name}</dd>
          </div>
          <div>
            <dt className="text-gray-500 dark:text-gray-400">{zh ? '邮箱' : 'Email'}</dt>
            <dd className="font-medium text-gray-900 dark:text-gray-100 mt-0.5">{user?.email}</dd>
          </div>
          <div>
            <dt className="text-gray-500 dark:text-gray-400">{zh ? '角色' : 'Role'}</dt>
            <dd className="font-medium text-gray-900 dark:text-gray-100 mt-0.5">{user?.role}</dd>
          </div>
          <div>
            <dt className="text-gray-500 dark:text-gray-400">{zh ? '注册时间' : 'Joined'}</dt>
            <dd className="font-medium text-gray-900 dark:text-gray-100 mt-0.5">
              {user?.created_at ? new Date(user.created_at).toLocaleString() : '-'}
            </dd>
          </div>
        </dl>
      </section>

      {status && (
        <section className="card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
            <Cpu className="w-5 h-5 text-primary-600" />{zh ? '模型服务' : 'Model service'}
          </h2>
          <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
            <div>
              <dt className="text-gray-500 dark:text-gray-400">{zh ? '服务商' : 'Provider'}</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100 mt-0.5">{status.provider}</dd>
            </div>
            <div>
              <dt className="text-gray-500 dark:text-gray-400">{zh ? '模型' : 'Model'}</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100 mt-0.5">{status.model}</dd>
            </div>
            <div>
              <dt className="text-gray-500 dark:text-gray-400">{zh ? 'API 状态' : 'API status'}</dt>
              <dd className="mt-0.5">
                <span className={`inline-flex items-center gap-1 font-medium ${status.llm_configured ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                  {status.llm_configured ? <CheckCircle2 className="w-4 h-4" /> : <XCircle className="w-4 h-4" />}
                  {status.llm_configured ? (zh ? '已配置' : 'configured') : (zh ? '未配置' : 'missing')}
                </span>
              </dd>
            </div>
            <div>
              <dt className="text-gray-500 dark:text-gray-400">{zh ? '最大并发任务' : 'Concurrent jobs'}</dt>
              <dd className="font-medium text-gray-900 dark:text-gray-100 mt-0.5">{status.max_concurrent_jobs}</dd>
            </div>
          </dl>
          <div className="mt-4 flex items-center gap-3">
            <button onClick={testLLM} disabled={testing} className="btn-secondary flex items-center gap-2">
              {testing ? <Loader2 className="w-4 h-4 animate-spin" /> : <Plug className="w-4 h-4" />}
              {zh ? '测试模型连通性' : 'Test connection'}
            </button>
            {testResult && (
              <span className={`text-sm ${testResult.ok ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'}`}>
                {testResult.ok ? `✓ ${testResult.message}` : `✗ ${testResult.message}`}
              </span>
            )}
          </div>
        </section>
      )}

      {status && (
        <section className="card">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4 flex items-center gap-2">
            <Database className="w-5 h-5 text-primary-600" />{zh ? '文献数据源' : 'Literature sources'}
          </h2>
          <div className="flex flex-wrap gap-2">
            {status.literature_sources.map((source) => (
              <span key={source} className="px-3 py-1.5 rounded-lg bg-gray-100 dark:bg-gray-700 text-sm text-gray-700 dark:text-gray-300 flex items-center gap-2">
                <Globe className="w-4 h-4" />{source}
              </span>
            ))}
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-3">
            {zh
              ? 'OpenAlex、Crossref、arXiv 无需密钥；Semantic Scholar 配置密钥后自动启用。'
              : 'OpenAlex, Crossref and arXiv need no key; Semantic Scholar activates when a key is configured.'}
          </p>
        </section>
      )}

      {health && (
        <section className="card bg-gray-50 dark:bg-gray-800/60">
          <h2 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">{zh ? '健康检查' : 'Health'}</h2>
          <pre className="text-xs text-gray-600 dark:text-gray-400 overflow-x-auto">{JSON.stringify(health, null, 2)}</pre>
        </section>
      )}
    </div>
  );
}

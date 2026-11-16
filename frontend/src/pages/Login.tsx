import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BookOpen, Loader2, Lock, Mail, ShieldCheck, User as UserIcon } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { useLanguage } from '../i18n';

export default function Login() {
  const { t, language } = useLanguage();
  const { login, register } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const zh = language === 'chinese';

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setBusy(true);
    try {
      if (mode === 'login') await login(email.trim(), password);
      else await register(email.trim(), password, name.trim());
      navigate('/', { replace: true });
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-2 bg-gray-50 dark:bg-gray-900">
      <div className="hidden lg:flex flex-col justify-between bg-gradient-to-br from-primary-700 via-primary-600 to-indigo-700 text-white p-12">
        <div className="flex items-center gap-3">
          <div className="bg-white/15 p-2 rounded-xl">
            <BookOpen className="w-7 h-7" />
          </div>
          <span className="text-xl font-semibold">Academic Paper Assistant</span>
        </div>
        <div className="space-y-6 max-w-md">
          <h1 className="text-3xl font-bold leading-snug">
            {zh ? '从选题到成稿，一套可核查的学术写作工作流' : 'A verifiable workflow from research question to manuscript'}
          </h1>
          <ul className="space-y-3 text-primary-50">
            <li className="flex gap-3"><ShieldCheck className="w-5 h-5 mt-0.5 shrink-0" />{zh ? '真实文献检索：OpenAlex / Crossref / arXiv' : 'Real literature retrieval: OpenAlex / Crossref / arXiv'}</li>
            <li className="flex gap-3"><ShieldCheck className="w-5 h-5 mt-0.5 shrink-0" />{zh ? '逐节生成，过程可追踪、可编辑' : 'Section-by-section generation, traceable and editable'}</li>
            <li className="flex gap-3"><ShieldCheck className="w-5 h-5 mt-0.5 shrink-0" />{zh ? '导出 Word / PDF / Markdown / BibTeX' : 'Export Word / PDF / Markdown / BibTeX'}</li>
          </ul>
        </div>
        <p className="text-sm text-primary-200">
          {zh ? '本工具用于辅助写作与研究，不替代作者本人的判断与责任。' : 'A writing aid — it does not replace the author’s judgement or responsibility.'}
        </p>
      </div>

      <div className="flex items-center justify-center p-6">
        <div className="w-full max-w-md">
          <div className="lg:hidden flex items-center gap-3 mb-8">
            <div className="bg-primary-600 p-2 rounded-xl">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <span className="text-lg font-semibold text-gray-900 dark:text-gray-100">Academic Paper Assistant</span>
          </div>

          <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            {mode === 'login' ? (zh ? '登录' : 'Sign in') : (zh ? '创建账户' : 'Create account')}
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mt-1 mb-6">
            {mode === 'login'
              ? (zh ? '使用你的邮箱和密码继续' : 'Continue with your email and password')
              : (zh ? '注册后即可生成并管理论文' : 'Sign up to generate and manage papers')}
          </p>

          {error && (
            <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-300">
              {error}
            </div>
          )}

          <form onSubmit={submit} className="space-y-4">
            {mode === 'register' && (
              <div>
                <label className="label">{zh ? '姓名' : 'Name'}</label>
                <div className="relative">
                  <UserIcon className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                  <input
                    className="input pl-9"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder={zh ? '用于论文署名' : 'Used as the paper author'}
                  />
                </div>
              </div>
            )}
            <div>
              <label className="label">{zh ? '邮箱' : 'Email'}</label>
              <div className="relative">
                <Mail className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <input
                  className="input pl-9"
                  type="email"
                  required
                  autoComplete="username"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                />
              </div>
            </div>
            <div>
              <label className="label">{zh ? '密码' : 'Password'}</label>
              <div className="relative">
                <Lock className="w-4 h-4 absolute left-3 top-3 text-gray-400" />
                <input
                  className="input pl-9"
                  type="password"
                  required
                  minLength={8}
                  autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={zh ? '至少 8 位' : 'At least 8 characters'}
                />
              </div>
            </div>

            <button type="submit" disabled={busy} className="btn-primary w-full flex items-center justify-center gap-2 py-2.5 disabled:opacity-60">
              {busy && <Loader2 className="w-4 h-4 animate-spin" />}
              {mode === 'login' ? (zh ? '登录' : 'Sign in') : (zh ? '注册并登录' : 'Create account')}
            </button>
          </form>

          <p className="text-sm text-gray-500 dark:text-gray-400 mt-6 text-center">
            {mode === 'login' ? (zh ? '还没有账户？' : 'No account yet?') : (zh ? '已有账户？' : 'Already registered?')}{' '}
            <button
              className="text-primary-600 dark:text-primary-400 font-medium hover:underline"
              onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(''); }}
            >
              {mode === 'login' ? (zh ? '注册' : 'Sign up') : (zh ? '去登录' : 'Sign in')}
            </button>
          </p>
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-8 text-center">
            {t('footer.description') as string}
          </p>
        </div>
      </div>
    </div>
  );
}

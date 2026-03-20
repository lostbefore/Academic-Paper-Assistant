import { Globe } from 'lucide-react';
import { useLanguage } from '../i18n';

export default function LanguageSwitcher() {
  const { language, toggleLanguage } = useLanguage();

  return (
    <button
      onClick={toggleLanguage}
      className="flex items-center gap-2 px-3 py-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors"
      title={language === 'english' ? 'Switch to Chinese' : '切换到英文'}
    >
      <Globe className="w-4 h-4" />
      <span className="text-sm font-medium">
        {language === 'english' ? 'EN' : '中文'}
      </span>
    </button>
  );
}

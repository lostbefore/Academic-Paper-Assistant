import { createContext, useContext, useState, useCallback, ReactNode } from 'react';
import { translations, Language } from './translations';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string | Record<string, string>;
  toggleLanguage: () => void;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// Get nested value from object using dot notation
function getNestedValue(obj: Record<string, any>, path: string): any {
  return path.split('.').reduce((current, key) => {
    if (current === undefined || current === null) return undefined;
    return current[key];
  }, obj);
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  // Try to get saved language from localStorage, default to browser language or 'english'
  const getInitialLanguage = (): Language => {
    const saved = localStorage.getItem('app-language') as Language;
    if (saved && (saved === 'english' || saved === 'chinese')) {
      return saved;
    }
    // Check browser language
    const browserLang = navigator.language.toLowerCase();
    if (browserLang.startsWith('zh')) {
      return 'chinese';
    }
    return 'english';
  };

  const [language, setLanguageState] = useState<Language>(getInitialLanguage);

  const setLanguage = useCallback((lang: Language) => {
    setLanguageState(lang);
    localStorage.setItem('app-language', lang);
    // Update document title based on language
    document.title = lang === 'chinese' ? '学术论文助手' : 'Academic Paper Assistant';
  }, []);

  const toggleLanguage = useCallback(() => {
    const newLang = language === 'english' ? 'chinese' : 'english';
    setLanguage(newLang);
  }, [language, setLanguage]);

  // Translation function
  const t = useCallback(
    (key: string): string | Record<string, string> => {
      const value = getNestedValue(translations[language], key);
      if (value === undefined) {
        console.warn(`Translation key not found: ${key}`);
        return key;
      }
      return value;
    },
    [language]
  );

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t, toggleLanguage }}>
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (context === undefined) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
}

// Hook for typed translations
export function useTypedTranslation() {
  const { t, language } = useLanguage();

  const translate = <T extends string | Record<string, string>>(key: string): T => {
    return t(key) as T;
  };

  return { t: translate, language };
}

export type Language = 'english' | 'chinese';
export type ApiLanguage = 'en' | 'zh';
export type Length = 'short' | 'medium' | 'long';
export type CitationStyleKey = 'apa' | 'mla' | 'ieee' | 'gbt7714';
export type PaperStatus = 'queued' | 'running' | 'completed' | 'failed' | 'cancelled';

export interface User {
  id: string;
  email: string;
  name: string;
  role: string;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface PaperRequest {
  title: string;
  field: string;
  keywords: string[];
  length: Length;
  citation_style: CitationStyleKey;
  language: Language;
  target_words?: number;
  reference_count?: number;
  instructions?: string;
}

export interface PaperSections {
  title?: string;
  abstract?: string;
  introduction?: string;
  literature_review?: string;
  methodology?: string;
  results?: string;
  discussion?: string;
  conclusion?: string;
  references?: string;
  [key: string]: string | undefined;
}

export interface Reference {
  title: string;
  authors: string[];
  year?: number | null;
  venue?: string;
  doi?: string;
  url?: string;
  abstract?: string;
  citations?: number;
  source?: string;
}

export interface OutlineSection {
  key: string;
  title: string;
  goal: string;
  words: number;
}

export interface Paper {
  id: string;
  title: string;
  status: PaperStatus;
  stage: string;
  progress: number;
  created_at: string;
  updated_at: string;
  finished_at?: string | null;
  error?: string;
  request: Partial<PaperRequest>;
  outline?: { sections?: OutlineSection[]; research_questions?: string[]; [key: string]: unknown };
  sections?: PaperSections;
  references?: Reference[];
  meta?: Record<string, unknown> & {
    word_count?: number;
    tokens_in?: number;
    tokens_out?: number;
    reference_count?: number;
    model?: string;
  };
  word_count?: number;
  images?: unknown[];
}

export interface CitationStyle {
  name: string;
  description: string;
  example: string;
}

export interface ApiStatus {
  version: string;
  environment: string;
  llm_configured: boolean;
  provider: string;
  model: string;
  model_fast: string;
  literature_sources: string[];
  citation_styles: string[];
  length_options: string[];
  language_options: Record<string, string>;
  max_concurrent_jobs: number;
  allow_registration: boolean;
}

export interface Stats {
  total: number;
  completed: number;
  running: number;
  failed: number;
  words: number;
  by_style: Record<string, number>;
}

export interface ProgressEvent {
  id: number;
  ts: string;
  stage: string;
  level: 'info' | 'warning' | 'error' | string;
  message: string;
  data?: Record<string, unknown>;
}

export const SECTION_KEYS = [
  'introduction',
  'literature_review',
  'methodology',
  'results',
  'discussion',
  'conclusion',
] as const;

export const SECTION_LABELS: Record<string, { en: string; zh: string }> = {
  abstract: { en: 'Abstract', zh: '摘要' },
  introduction: { en: 'Introduction', zh: '引言' },
  literature_review: { en: 'Literature Review', zh: '文献综述' },
  methodology: { en: 'Methodology', zh: '研究方法' },
  results: { en: 'Results', zh: '研究结果' },
  discussion: { en: 'Discussion', zh: '讨论' },
  conclusion: { en: 'Conclusion', zh: '结论' },
  references: { en: 'References', zh: '参考文献' },
};

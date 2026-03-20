export interface PaperRequest {
  title: string;
  keywords: string[];
  field: string;
  length: 'short' | 'medium' | 'long';
  citation_style: 'apa' | 'mla' | 'ieee' | 'gbt7714';
  language: 'english' | 'chinese';
}

export interface PaperSections {
  title: string;
  abstract: string;
  introduction: string;
  literature_review: string;
  methodology: string;
  results: string;
  discussion: string;
  conclusion: string;
  references: string;
}

export interface Reference {
  id: string;
  title: string;
  authors: string[];
  year: number;
  source: string;
  url?: string;
  citation_count?: number;
}

export interface PaperImage {
  id: string;
  caption: string;
  source: 'ai_generated' | 'web_search' | 'pdf_extract' | 'chart';
  source_url?: string;
  source_title?: string;
  filepath: string;
  width?: number;
  height?: number;
}

export interface Paper {
  id: string;
  title: string;
  status: 'generating' | 'writing' | 'completed' | 'failed';
  sections?: PaperSections;
  created_at: string;
  error?: string;
  filepath?: string;
  request?: PaperRequest;
  references?: Reference[];
  images?: PaperImage[];
}

export interface CitationStyle {
  name: string;
  description: string;
  example: string;
}

export interface ApiStatus {
  api_key_configured: boolean;
  model: string;
  api_base: string;
  citation_styles: string[];
  length_options: string[];
  language_options: Record<string, string>;
}
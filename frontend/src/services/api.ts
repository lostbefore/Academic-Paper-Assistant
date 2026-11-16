import axios, { AxiosError } from 'axios';
import type {
  ApiStatus,
  AuthResponse,
  CitationStyle,
  Language,
  Paper,
  PaperRequest,
  ProgressEvent,
  Reference,
  Stats,
  User,
} from '../types';

const TOKEN_KEY = 'apa_token';
const API_BASE = import.meta.env.VITE_API_URL || '';

export const api = axios.create({
  baseURL: `${API_BASE}/api`,
  headers: { 'Content-Type': 'application/json' },
});

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      setToken(null);
      if (!window.location.pathname.startsWith('/login')) {
        window.dispatchEvent(new CustomEvent('apa:unauthorized'));
      }
    }
    return Promise.reject(error);
  },
);

export function errorMessage(error: unknown): string {
  const axiosError = error as AxiosError<{ detail?: string | { msg?: string }[] }>;
  const detail = axiosError?.response?.data?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length > 0) {
    return detail.map((d) => d.msg || JSON.stringify(d)).join('; ');
  }
  return axiosError?.message || 'Request failed';
}

const toApiLanguage = (language?: Language) => (language === 'chinese' ? 'zh' : 'en');
const fromApiLanguage = (language?: string): Language => (language === 'zh' ? 'chinese' : 'english');

function normalizePaper(raw: any): Paper {
  const paper = raw as Paper;
  if (paper.request) {
    paper.request = { ...paper.request, language: fromApiLanguage(paper.request.language as string) };
  }
  return paper;
}

export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthResponse>('/auth/login', { email, password }).then((r) => r.data),
  register: (email: string, password: string, name: string) =>
    api.post<AuthResponse>('/auth/register', { email, password, name }).then((r) => r.data),
  me: () => api.get<User>('/auth/me').then((r) => r.data),
};

export const paperApi = {
  list: (params?: { status?: string; q?: string }) =>
    api.get<Paper[]>('/papers', { params }).then((r) => r.data.map(normalizePaper)),

  get: (id: string) => api.get<Paper>(`/papers/${id}`).then((r) => normalizePaper(r.data)),

  create: (payload: PaperRequest) =>
    api
      .post<Paper>('/papers', { ...payload, language: toApiLanguage(payload.language) })
      .then((r) => normalizePaper(r.data)),

  remove: (id: string) => api.delete(`/papers/${id}`),

  cancel: (id: string) => api.post<Paper>(`/papers/${id}/cancel`).then((r) => normalizePaper(r.data)),

  retry: (id: string) => api.post<Paper>(`/papers/${id}/retry`).then((r) => normalizePaper(r.data)),

  updateSection: (id: string, key: string, content: string) =>
    api.put<Paper>(`/papers/${id}/sections/${key}`, { content }).then((r) => normalizePaper(r.data)),

  regenerateSection: (id: string, key: string, instructions = '') =>
    api
      .post<{ section: string; content: string; paper: Paper }>(
        `/papers/${id}/sections/${key}/regenerate`,
        { instructions },
      )
      .then((r) => ({ ...r.data, paper: normalizePaper(r.data.paper as unknown as Record<string, unknown>) })),

  log: (id: string) =>
    api.get<ProgressEvent[]>(`/papers/${id}/log`).then((r) => r.data),

  stats: () => api.get<Stats>('/stats').then((r) => r.data),

  download: (id: string, format: 'docx' | 'pdf' | 'md' | 'bib') =>
    api.get(`/papers/${id}/export/${format}`, { responseType: 'blob' }).then((r) => r.data as Blob),
};

export const metaApi = {
  status: () => api.get<ApiStatus>('/status').then((r) => r.data),
  styles: () => api.get<Record<string, CitationStyle>>('/styles').then((r) => r.data),
  health: () => api.get('/health').then((r) => r.data),
  testLLM: () => api.post<{ ok: boolean; message: string; model?: string }>('/llm/test').then((r) => r.data),
};

export const literatureApi = {
  search: (query: string, limit = 12, yearFrom?: number) =>
    api
      .get<Reference[]>('/literature/search', { params: { q: query, limit, year_from: yearFrom } })
      .then((r) => r.data),
};

/**
 * Subscribe to a paper's progress stream. Uses fetch (not EventSource) so the
 * bearer token can be sent in a header.
 */
export function streamPaper(
  id: string,
  handlers: {
    onEvent: (event: ProgressEvent) => void;
    onDone: (status: string) => void;
    onError: (error: string) => void;
  },
): () => void {
  const controller = new AbortController();
  const token = getToken();

  (async () => {
    try {
      const response = await fetch(`/api/papers/${id}/events`, {
        headers: token ? { Authorization: `Bearer ${token}` } : {},
        signal: controller.signal,
      });
      if (!response.ok || !response.body) {
        throw new Error(`stream failed (${response.status})`);
      }
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const blocks = buffer.split('\n\n');
        buffer = blocks.pop() || '';
        for (const block of blocks) {
          let eventName = 'message';
          const dataLines: string[] = [];
          for (const line of block.split('\n')) {
            if (line.startsWith('event:')) eventName = line.slice(6).trim();
            else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
          }
          if (!dataLines.length) continue;
          const payload = dataLines.join('\n');
          if (eventName === 'done') {
            try {
              handlers.onDone(JSON.parse(payload).status);
            } catch {
              handlers.onDone('completed');
            }
            return;
          }
          if (eventName === 'progress') {
            try {
              handlers.onEvent(JSON.parse(payload) as ProgressEvent);
            } catch {
              /* ignore malformed frames */
            }
          }
        }
      }
    } catch (error) {
      if ((error as Error).name !== 'AbortError') {
        handlers.onError(errorMessage(error));
      }
    }
  })();

  return () => controller.abort();
}

export async function saveBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default api;

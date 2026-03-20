import axios from 'axios';
import { PaperRequest, Paper, ApiStatus, CitationStyle } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_BASE_URL}/api`,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const paperApi = {
  // Status
  getStatus: () => api.get<ApiStatus>('/status').then(res => res.data),

  // Papers
  createPaper: (data: PaperRequest) =>
    api.post<Paper>('/papers', data).then(res => res.data),

  getPapers: () =>
    api.get<Paper[]>('/papers').then(res => res.data),

  getPaper: (id: string) =>
    api.get<Paper>(`/papers/${id}`).then(res => res.data),

  deletePaper: (id: string) =>
    api.delete(`/papers/${id}`).then(res => res.data),

  // Format
  formatPaper: (id: string, style: string) =>
    api.post(`/papers/${id}/format`, { style }).then(res => res.data),

  // Styles
  getCitationStyles: () =>
    api.get<Record<string, CitationStyle>>('/styles').then(res => res.data),

  // Download
  downloadDocx: (id: string) =>
    api.get(`/papers/${id}/download/docx`, { responseType: 'blob' }),

  downloadMarkdown: (id: string) =>
    api.get(`/papers/${id}/download/markdown`, { responseType: 'blob' }),

  downloadPdf: (id: string) =>
    api.get(`/papers/${id}/download/pdf`, { responseType: 'blob' }),
};

export default api;

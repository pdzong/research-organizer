import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface Paper {
  id: string;
  title: string;
  authors: string[];
  arxiv_url: string | null;
  arxiv_id: string | null;
}

export interface ParseResponse {
  success: boolean;
  markdown: string | null;
  size_bytes: number | null;
  error: string | null;
  from_cache?: boolean;
}

export interface Benchmark {
  name: string;
  score: string;
  metric: string;
}

export interface Summary {
  main_contribution: string;
  methodology: string;
  key_results: string;
  significance: string;
  limitations: string;
}

export interface Analysis {
  paper_title: string;
  summary: Summary;
  benchmarks: Benchmark[];
}

export interface AnalyzeResponse {
  success: boolean;
  summary: Analysis | null;
  model: string | null;
  tokens_used: number | null;
  error: string | null;
  from_cache?: boolean;
}

export interface AddPaperResponse {
  success: boolean;
  paper: Paper | null;
  message: string | null;
  error: string | null;
}

export const fetchPapers = async (): Promise<Paper[]> => {
  const response = await apiClient.get<Paper[]>('/papers');
  return response.data;
};

export const parsePaper = async (
  paperId: string, 
  arxivUrl?: string, 
  forceReload?: boolean
): Promise<ParseResponse> => {
  const params: any = {};
  if (arxivUrl) params.arxiv_url = arxivUrl;
  if (forceReload) params.force_reload = true;
  const response = await apiClient.get<ParseResponse>(`/papers/${paperId}/parse`, { params });
  return response.data;
};

export const analyzePaper = async (markdown: string): Promise<AnalyzeResponse> => {
  const response = await apiClient.post<AnalyzeResponse>('/papers/analyze', { markdown });
  return response.data;
};

export const addPaper = async (arxivUrl: string): Promise<AddPaperResponse> => {
  const response = await apiClient.post<AddPaperResponse>('/papers/add', { arxiv_url: arxivUrl });
  return response.data;
};

export interface RelatedPaper {
  paperId: string | null;
  title: string | null;
  year: number | null;
  authors: Array<{ authorId: string | null; name: string | null }>;
  citationCount: number;
  url: string | null;
  arxivId: string | null;
  externalIds: Record<string, any>;
}

export interface PaperMetadata {
  success: boolean;
  paperId: string | null;
  title: string | null;
  abstract: string | null;
  year: number | null;
  publicationDate: string | null;
  citationCount: number;
  referenceCount: number;
  influentialCitationCount: number;
  isOpenAccess: boolean;
  fieldsOfStudy: string[];
  s2FieldsOfStudy: Array<{ category: string; source: string }>;
  publicationTypes: string[];
  publicationVenue: { name: string | null; type: string | null; url: string | null } | null;
  journal: { name: string | null; volume: string | null; pages: string | null } | null;
  authors: Array<{ authorId: string; name: string; url: string }>;
  venue: string | null;
  openAccessPdf: any;
  externalIds: Record<string, any>;
  url: string | null;
  tldr: string | null;
  corpusId: string | null;
  citations?: RelatedPaper[];
  recommendations?: RelatedPaper[];
}

export interface MetadataResponse {
  success: boolean;
  metadata: PaperMetadata | null;
  error: string | null;
  from_cache?: boolean;
}

export interface CacheStatus {
  metadata: boolean;
  markdown: boolean;
  analysis: boolean;
}

export const getPaperMetadata = async (
  arxivId: string, 
  forceReload?: boolean
): Promise<MetadataResponse> => {
  const params = forceReload ? { force_reload: true } : {};
  const response = await apiClient.get<MetadataResponse>(`/papers/${arxivId}/metadata`, { params });
  return response.data;
};

export const getCachedAnalysis = async (
  arxivId: string,
  forceReload?: boolean
): Promise<AnalyzeResponse> => {
  const params = forceReload ? { force_reload: true } : {};
  const response = await apiClient.get<AnalyzeResponse>(`/papers/${arxivId}/analyze`, { params });
  return response.data;
};

export const getCacheStatus = async (arxivId: string): Promise<CacheStatus> => {
  const response = await apiClient.get<CacheStatus>(`/papers/${arxivId}/cache-status`);
  return response.data;
};

export const addRelatedPaper = async (
  paperId: string,
  arxivId: string | null,
  title: string,
  authors: string[]
): Promise<AddPaperResponse> => {
  const response = await apiClient.post<AddPaperResponse>('/papers/add-related', {
    paper_id: paperId,
    arxiv_id: arxivId,
    title,
    authors
  });
  return response.data;
};

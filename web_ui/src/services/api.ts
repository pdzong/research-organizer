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
  source?: string | null;
  pdf_url?: string | null;
  landing_url?: string | null;
  published_date?: string | null;
  is_open_access?: boolean | null;
  oa_status?: string | null;
  doi?: string | null;
}

export interface ParseResponse {
  success: boolean;
  markdown: string | null;
  size_bytes: number | null;
  error: string | null;
  from_cache?: boolean;
}

export interface BenchmarkResult {
  name: string;
  score: string;
  metric: string;
  setting: string | null;
  is_this_paper_result: boolean;
  source_quote: string;
}

export interface NoveltyAnalysis {
  status_quo: string;
  proposed_delta: string;
  novelty_summary: string;
  real_world_analogy: string;
}

export interface ApplicationIdea {
  domain: string;
  specific_utility: string;
}

export interface Summary {
  main_contribution: string;
  methodology: string;
  applications: (ApplicationIdea | string)[]; // Support both old (string) and new (ApplicationIdea) formats
  limitations: string;
}

export interface Analysis {
  paper_title: string;
  novelty: NoveltyAnalysis;
  summary: Summary;
  github_repo: string;
  benchmarks: BenchmarkResult[];
}

export interface AnalyzeResponse {
  success: boolean;
  data?: Analysis;
  usage?: {
    model: string;
    input_tokens: number;
    output_tokens: number;
  };
  error?: string;
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

export const addPaper = async (reference: string): Promise<AddPaperResponse> => {
  // Backend accepts an arXiv URL, DOI, OpenAlex id/URL, or direct .pdf link (P1-005)
  const payload = /^10\./.test(reference.trim())
    ? { doi: reference.trim() }
    : { url: reference.trim() };
  const response = await apiClient.post<AddPaperResponse>('/papers/add', payload);
  return response.data;
};

export const addPaperFromSource = async (
  source: string,
  sourceRecordId: string
): Promise<AddPaperResponse> => {
  const response = await apiClient.post<AddPaperResponse>('/papers/add', {
    source,
    source_record_id: sourceRecordId,
  });
  return response.data;
};

export interface RelatedPaper {
  paperId: string | null;
  title: string | null;
  year: number | null;
  authors: Array<{ authorId: string | null; name: string | null }>;
  citationCount: number;
  influentialCitationCount?: number;
  referenceCount?: number;
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
  sections: boolean;
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

export interface SimplePaperInfo {
  title: string;
  authors: string[];
  arxiv_id?: string;
}

export interface AddApplicationRequest {
  application: ApplicationIdea;
  current_paper: SimplePaperInfo;
  related_papers: SimplePaperInfo[];
}

export interface AddApplicationResponse {
  success: boolean;
  message?: string;
  error?: string;
}

export const addApplication = async (
  application: ApplicationIdea,
  currentPaper: SimplePaperInfo,
  relatedPapers: SimplePaperInfo[]
): Promise<AddApplicationResponse> => {
  const response = await apiClient.post<AddApplicationResponse>('/applications/add', {
    application,
    current_paper: currentPaper,
    related_papers: relatedPapers
  });
  return response.data;
};

export interface ApplicationEntry {
  id: string;
  application: ApplicationIdea;
  current_paper: SimplePaperInfo;
  related_papers: SimplePaperInfo[];
  added_at: string;
}

export interface FetchApplicationsResponse {
  success: boolean;
  applications: ApplicationEntry[];
  error?: string;
}

export const fetchApplications = async (): Promise<ApplicationEntry[]> => {
  const response = await apiClient.get<FetchApplicationsResponse>('/applications');
  return response.data.applications;
};

// ─── Solution plans (codegen-ready system descriptions) ────────────────────

export interface SolutionModule {
  name: string;
  responsibility: string;
  inputs: string[];
  outputs: string[];
  technologies: string[];
  paper_grounding: string[];
}

export interface SolutionDataModel {
  name: string;
  fields: string[];
  notes?: string | null;
}

export interface SolutionAPISpec {
  method: string;
  path: string;
  purpose: string;
  request?: string | null;
  response?: string | null;
}

export interface SolutionMilestone {
  title: string;
  deliverables: string[];
  estimated_effort?: string | null;
}

export interface SolutionRisk {
  description: string;
  mitigation: string;
}

export interface SolutionPlan {
  name: string;
  tagline: string;
  problem_statement: string;
  target_users: string[];
  scientific_grounding: string;
  key_enabling_papers: string[];
  system_overview: string;
  architecture_diagram: string;
  modules: SolutionModule[];
  data_models: SolutionDataModel[];
  apis: SolutionAPISpec[];
  integration_points: string[];
  tech_stack: string[];
  milestones: SolutionMilestone[];
  risks: SolutionRisk[];
  success_metrics: string[];
  open_questions: string[];
  code_generation_prompt: string;
}

export interface SolutionPlanRecord {
  application_id?: string;
  generated_at?: string;
  plan?: SolutionPlan;
  markdown?: string;
  brief?: string;
}

export interface GeneratePlanResponse {
  success: boolean;
  application_id?: string;
  plan?: SolutionPlan;
  markdown?: string;
  brief?: string;
  generated_at?: string;
  from_cache?: boolean;
  error?: string;
}

export const generateSolutionPlan = async (
  applicationId: string,
  forceReload: boolean = false
): Promise<GeneratePlanResponse> => {
  const params = forceReload ? { force_reload: true } : {};
  const response = await apiClient.post<GeneratePlanResponse>(
    `/applications/${encodeURIComponent(applicationId)}/plan`,
    null,
    { params }
  );
  return response.data;
};

export const getSolutionPlan = async (
  applicationId: string
): Promise<GeneratePlanResponse> => {
  const response = await apiClient.get<GeneratePlanResponse>(
    `/applications/${encodeURIComponent(applicationId)}/plan`
  );
  return response.data;
};

export const fetchSolutions = async (): Promise<SolutionPlanRecord[]> => {
  const response = await apiClient.get<{ success: boolean; plans: SolutionPlanRecord[] }>(
    '/solutions'
  );
  return response.data.plans || [];
};

// ─── Source discovery (OpenAlex, …) ───────────────────────────────────────

export interface SourcePaperResult {
  id: string;
  source: string;
  source_record_id: string;
  title: string;
  authors: string[];
  abstract?: string | null;
  published_date?: string | null;
  landing_url?: string | null;
  pdf_url?: string | null;
  is_open_access?: boolean | null;
  oa_status?: string | null;
  arxiv_id?: string | null;
  doi?: string | null;
  external_ids?: Record<string, string>;
  source_metadata?: Record<string, any>;
  matched_topic?: string;
  strategic_fit?: StrategicFitAssessment;
  strategic_fit_error?: string;
}

export interface SourceSearchResponse {
  success: boolean;
  source: string;
  papers: SourcePaperResult[];
  count: number;
  error?: string | null;
}

export const searchSource = async (params: {
  source?: string;
  query: string;
  limit?: number;
  since?: string;
  openAccessOnly?: boolean;
}): Promise<SourceSearchResponse> => {
  const response = await apiClient.get<SourceSearchResponse>('/sources/search', {
    params: {
      source: params.source || 'openalex',
      query: params.query,
      limit: params.limit ?? 20,
      since: params.since,
      open_access_only: params.openAccessOnly ?? true,
    },
  });
  return response.data;
};

// ─── Company research profiles ────────────────────────────────────────────

export interface CompanyProfile {
  id: string;
  name: string;
  industry?: string | null;
  description?: string | null;
  tech_stack: string[];
  strategic_questions: string[];
  watch_topics: string[];
  assumptions: string[];
  created_at: string;
  updated_at: string;
}

export interface CompanyProfileInput {
  name: string;
  industry?: string | null;
  description?: string | null;
  tech_stack: string[];
  strategic_questions: string[];
  watch_topics: string[];
  assumptions: string[];
}

export interface StrategicFitAssessment {
  fit_score: number;
  relevance_summary: string;
  opportunities: string[];
  threats: string[];
  challenged_assumptions: string[];
  recommended_action: 'ignore' | 'watch' | 'analyze' | 'prototype';
  reasoning: string;
  profile_id?: string;
  paper_id?: string;
  scored_at?: string;
}

export interface ProfileListResponse {
  success: boolean;
  profiles: CompanyProfile[];
  active_profile_id: string | null;
}

export const fetchProfiles = async (): Promise<ProfileListResponse> => {
  const response = await apiClient.get<ProfileListResponse>('/profiles');
  return response.data;
};

export const createProfile = async (data: CompanyProfileInput): Promise<CompanyProfile> => {
  const response = await apiClient.post<{ success: boolean; profile: CompanyProfile }>(
    '/profiles',
    data
  );
  return response.data.profile;
};

export const updateProfile = async (
  profileId: string,
  data: CompanyProfileInput
): Promise<CompanyProfile> => {
  const response = await apiClient.put<{ success: boolean; profile: CompanyProfile }>(
    `/profiles/${encodeURIComponent(profileId)}`,
    data
  );
  return response.data.profile;
};

export const deleteProfile = async (profileId: string): Promise<void> => {
  await apiClient.delete(`/profiles/${encodeURIComponent(profileId)}`);
};

export const activateProfile = async (profileId: string): Promise<void> => {
  await apiClient.post(`/profiles/${encodeURIComponent(profileId)}/activate`);
};

export interface StrategicFitResponse {
  success: boolean;
  assessment: StrategicFitAssessment | null;
  from_cache: boolean;
  error?: string | null;
}

export const scorePaperForProfile = async (
  profileId: string,
  paperId: string,
  forceReload: boolean = false
): Promise<StrategicFitResponse> => {
  const params = forceReload ? { force_reload: true } : {};
  const response = await apiClient.post<StrategicFitResponse>(
    `/profiles/${encodeURIComponent(profileId)}/score/${encodeURIComponent(paperId)}`,
    null,
    { params }
  );
  return response.data;
};

export interface ProfileDiscoverResponse {
  success: boolean;
  profile_id: string;
  topics_searched: string[];
  papers: SourcePaperResult[];
  count: number;
  error?: string | null;
}

export const discoverForProfile = async (params: {
  profileId: string;
  limitPerTopic?: number;
  since?: string;
  scoreTop?: number;
}): Promise<ProfileDiscoverResponse> => {
  const response = await apiClient.get<ProfileDiscoverResponse>(
    `/profiles/${encodeURIComponent(params.profileId)}/discover`,
    {
      params: {
        limit_per_topic: params.limitPerTopic ?? 5,
        since: params.since,
        score_top: params.scoreTop ?? 0,
      },
    }
  );
  return response.data;
};

export interface AppImproveDiscoverResponse {
  success: boolean;
  run_id?: string | null;
  created_at?: string | null;
  topics_searched: string[];
  topics_rationale?: string | null;
  papers: SourcePaperResult[];
  count: number;
  error?: string | null;
}

export interface AppImproveRunSummary {
  id: string;
  created_at: string;
  app_description: string;
  improvement_direction: string;
  count: number;
  topics_searched: string[];
  top_fit_score?: number | null;
}

export interface AppImproveRun extends AppImproveRunSummary {
  since?: string | null;
  limit_per_topic: number;
  score_top: number;
  topics_rationale?: string | null;
  papers: SourcePaperResult[];
  error?: string | null;
}

export const discoverForApp = async (params: {
  appDescription: string;
  improvementDirection: string;
  limitPerTopic?: number;
  since?: string;
  scoreTop?: number;
}): Promise<AppImproveDiscoverResponse> => {
  const response = await apiClient.post<AppImproveDiscoverResponse>('/app-improve/discover', {
    app_description: params.appDescription,
    improvement_direction: params.improvementDirection,
    limit_per_topic: params.limitPerTopic ?? 5,
    since: params.since || undefined,
    score_top: params.scoreTop ?? 5,
  });
  return response.data;
};

export const fetchAppImproveRuns = async (): Promise<AppImproveRunSummary[]> => {
  const response = await apiClient.get<{ success: boolean; runs: AppImproveRunSummary[] }>(
    '/app-improve/runs'
  );
  return response.data.runs || [];
};

export const getAppImproveRun = async (runId: string): Promise<AppImproveRun> => {
  const response = await apiClient.get<{ success: boolean; run: AppImproveRun }>(
    `/app-improve/runs/${encodeURIComponent(runId)}`
  );
  return response.data.run;
};

export const deleteAppImproveRun = async (runId: string): Promise<void> => {
  await apiClient.delete(`/app-improve/runs/${encodeURIComponent(runId)}`);
};

export const appImproveRunMarkdownUrl = (runId: string): string =>
  `${API_BASE_URL}/app-improve/runs/${encodeURIComponent(runId)}/markdown`;

// ─── Auto-research control plane ──────────────────────────────────────────

export interface AutoResearchLogEntry {
  ts: string;
  level: string;
  message: string;
}

export interface AutoResearchStatus {
  state: 'idle' | 'running' | 'stopping' | 'stopped' | 'error';
  source: string;
  limit: number;
  continuous: boolean;
  interval_seconds: number;
  generate_plans?: boolean;
  plan_min_confidence?: number;
  started_at?: string | null;
  finished_at?: string | null;
  current_arxiv_id?: string | null;
  current_step?: string | null;
  processed_count: number;
  skipped_count: number;
  error_count: number;
  application_count: number;
  plan_count?: number;
  plan_skipped_count?: number;
  log: AutoResearchLogEntry[];
  last_error?: string | null;
}

export interface AutoResearchStatusResponse {
  success: boolean;
  status: AutoResearchStatus;
  error?: string;
}

export interface AutoResearchSource {
  id: string;
  label: string;
}

export const fetchAutoResearchSources = async (): Promise<AutoResearchSource[]> => {
  const response = await apiClient.get<{ success: boolean; sources: AutoResearchSource[] }>(
    '/auto-research/sources'
  );
  return response.data.sources || [];
};

export const startAutoResearch = async (params: {
  source: string;
  limit: number;
  continuous: boolean;
  interval_seconds: number;
  generate_plans?: boolean;
  plan_min_confidence?: number;
}): Promise<AutoResearchStatusResponse> => {
  const response = await apiClient.post<AutoResearchStatusResponse>(
    '/auto-research/start',
    params
  );
  return response.data;
};

export const stopAutoResearch = async (): Promise<AutoResearchStatusResponse> => {
  const response = await apiClient.post<AutoResearchStatusResponse>(
    '/auto-research/stop'
  );
  return response.data;
};

export const getAutoResearchStatus = async (): Promise<AutoResearchStatusResponse> => {
  const response = await apiClient.get<AutoResearchStatusResponse>(
    '/auto-research/status'
  );
  return response.data;
};

// ─── LLM provider / model config ──────────────────────────────────────────

export interface LlmRoleBinding {
  provider: string;
  model: string;
}

export interface LlmProviderInfo {
  label: string;
  suggested_models: string[];
  env_keys: string[];
  key_present: boolean;
  active_env?: string | null;
}

export interface LlmRoleDescription {
  id: string;
  description: string;
}

export interface LlmConfigResponse {
  success: boolean;
  roles: Record<string, LlmRoleBinding>;
  defaults: Record<string, LlmRoleBinding>;
  role_descriptions: LlmRoleDescription[];
  providers: Record<string, LlmProviderInfo>;
}

export const getLlmConfig = async (): Promise<LlmConfigResponse> => {
  const response = await apiClient.get<LlmConfigResponse>('/config/llm');
  return response.data;
};

export const updateLlmConfig = async (
  roles: Record<string, Partial<LlmRoleBinding>>
): Promise<{ success: boolean; roles: Record<string, LlmRoleBinding> }> => {
  const response = await apiClient.put<{ success: boolean; roles: Record<string, LlmRoleBinding> }>(
    '/config/llm',
    { roles }
  );
  return response.data;
};

export const resetLlmConfig = async (): Promise<{ success: boolean; roles: Record<string, LlmRoleBinding> }> => {
  const response = await apiClient.post<{ success: boolean; roles: Record<string, LlmRoleBinding> }>(
    '/config/llm/reset'
  );
  return response.data;
};

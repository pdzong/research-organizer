import { IconAlertCircle, IconSparkles, IconFileText, IconArrowLeft, IconChartBar, IconBook, IconUsers, IconCalendar, IconWorld, IconFileDescription, IconPlus, IconLink, IconTrendingUp, IconFlame, IconReload } from '@tabler/icons-react';
import ReactMarkdown from 'react-markdown';
import { Paper as PaperType, Analysis, PaperMetadata, CacheStatus, RelatedPaper } from '../services/api';
import { useState } from 'react';

interface PaperDetailProps {
  paper: PaperType;
  markdown: string | null;
  summary: Analysis | null;
  metadata: PaperMetadata | null;
  cacheStatus: CacheStatus;
  loading: boolean;
  analyzing: boolean;
  loadingMetadata: boolean;
  error: string | null;
  onParse: (forceReload?: boolean) => void;
  onAnalyze: (forceReload?: boolean) => void;
  onReloadMetadata: () => void;
  onAddRelatedPaper: (paperId: string, arxivId: string | null, title: string, authors: string[]) => void;
  onBack: () => void;
}

/**
 * Calculate relevance score based on Semantic Scholar metrics
 * Returns a score between 0-100
 */
function calculateRelevanceScore(paper: RelatedPaper, index: number, isRecommendation: boolean = false): number {
  const citationCount = paper.citationCount || 0;
  const influentialCount = paper.influentialCitationCount || 0;
  
  // Calculate influence ratio (0-1)
  const influenceRatio = citationCount > 0 ? influentialCount / citationCount : 0;
  
  // For recommendations, position matters (earlier = more relevant)
  const positionBonus = isRecommendation ? Math.max(0, (10 - index) * 2) : 0;
  
  // Combined score: citation count (log scale) + influence weight + position
  const citationScore = Math.min(50, Math.log10(citationCount + 1) * 15);
  const influenceScore = influenceRatio * 30;
  
  return Math.min(100, citationScore + influenceScore + positionBonus);
}

/**
 * Get color classes based on relevance score
 */
function getRelevanceClasses(score: number): string {
  if (score >= 60) {
    return 'border-amber-500/60 bg-amber-500/10 shadow-amber-500/20';
  } else if (score >= 40) {
    return 'border-yellow-500/60 bg-yellow-500/10 shadow-yellow-500/20';
  } else if (score >= 20) {
    return 'border-blue-500/60 bg-blue-500/10 shadow-blue-500/20';
  } else {
    return 'border-linear-dark-border bg-linear-dark-surface';
  }
}

/**
 * Get icon for relevance score
 */
function getRelevanceIcon(score: number) {
  if (score >= 60) {
    return { Icon: IconFlame, color: 'text-amber-400', label: 'Highly Relevant' };
  } else if (score >= 40) {
    return { Icon: IconTrendingUp, color: 'text-yellow-400', label: 'Very Relevant' };
  }
  return null;
}

export function PaperDetail({
  paper,
  markdown,
  summary,
  metadata,
  cacheStatus,
  loading,
  analyzing,
  loadingMetadata,
  error,
  onParse,
  onAnalyze,
  onReloadMetadata,
  onAddRelatedPaper,
  onBack,
}: PaperDetailProps) {
  const [activeSection, setActiveSection] = useState<string>('overview');
  const [expandedAccordion, setExpandedAccordion] = useState<string | null>('overview');

  const toggleAccordion = (section: string) => {
    setExpandedAccordion(expandedAccordion === section ? null : section);
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Back Button */}
      <button
        onClick={onBack}
        className="btn-secondary w-fit flex items-center gap-2"
      >
        <IconArrowLeft size={16} />
        Back to Papers
      </button>

      {/* Paper Header */}
      <div className="bento-card p-6">
        <h1 className="text-2xl font-bold text-white mb-3">{paper.title}</h1>
        <div className="flex items-center gap-2 text-sm text-linear-dark-muted mb-4">
          <IconUsers size={14} />
          <span>{paper.authors.join(', ')}</span>
        </div>
        {paper.arxiv_id && (
          <span className="inline-block px-3 py-1 rounded-linear text-sm bg-blue-500/10 text-blue-400 border border-blue-500/20">
            ArXiv: {paper.arxiv_id}
          </span>
        )}
      </div>

      {/* Action Buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          onClick={() => onParse(false)}
          disabled={loading}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loading ? (
            <>
              <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin"></div>
              {cacheStatus.has_markdown ? 'Reloading...' : 'Loading...'}
            </>
          ) : (
            <>
              <IconFileText size={16} />
              {cacheStatus.has_markdown ? 'Reload Markdown' : 'Load Markdown'}
            </>
          )}
        </button>

        <button
          onClick={() => onAnalyze(false)}
          disabled={analyzing || !markdown}
          className="btn-primary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {analyzing ? (
            <>
              <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin"></div>
              {cacheStatus.has_analysis ? 'Regenerating...' : 'Analyzing...'}
            </>
          ) : (
            <>
              <IconSparkles size={16} />
              {cacheStatus.has_analysis ? 'Regenerate Analysis' : 'Analyze Paper'}
            </>
          )}
        </button>

        <button
          onClick={onReloadMetadata}
          disabled={loadingMetadata}
          className="btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {loadingMetadata ? (
            <>
              <div className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
              Reloading Metadata...
            </>
          ) : (
            <>
              <IconReload size={16} />
              Reload Metadata
            </>
          )}
        </button>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bento-card p-4 border-red-500/50 bg-red-500/10">
          <div className="flex items-center gap-2 text-red-400">
            <IconAlertCircle size={18} />
            <span className="text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Main Content Grid */}
      {(markdown || summary || metadata) && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Sidebar - Metadata */}
          <div className="lg:col-span-1 space-y-4">
            {metadata && (
              <div className="bento-card p-5 space-y-4">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                  <IconBook size={20} />
                  Paper Metadata
                </h3>

                {/* Overview Section */}
                <div>
                  <button
                    onClick={() => toggleAccordion('overview')}
                    className="w-full flex justify-between items-center py-2 text-white hover:text-white/80 transition-colors"
                  >
                    <span className="font-medium">Overview</span>
                    <span className="text-linear-dark-muted">{expandedAccordion === 'overview' ? '−' : '+'}</span>
                  </button>
                  {expandedAccordion === 'overview' && (
                    <div className="mt-2 space-y-3 text-sm">
                      {metadata.abstract && (
                        <div>
                          <p className="text-linear-dark-muted mb-1">Abstract</p>
                          <p className="text-linear-dark-text leading-relaxed">{metadata.abstract}</p>
                        </div>
                      )}
                      {metadata.tldr && (
                        <div>
                          <p className="text-linear-dark-muted mb-1 flex items-center gap-1">
                            <IconQuote size={12} />
                            TL;DR
                          </p>
                          <p className="text-linear-dark-text leading-relaxed italic">"{metadata.tldr}"</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="border-t border-linear-dark-border"></div>

                {/* Publication Info */}
                <div>
                  <button
                    onClick={() => toggleAccordion('publication')}
                    className="w-full flex justify-between items-center py-2 text-white hover:text-white/80 transition-colors"
                  >
                    <span className="font-medium">Publication Info</span>
                    <span className="text-linear-dark-muted">{expandedAccordion === 'publication' ? '−' : '+'}</span>
                  </button>
                  {expandedAccordion === 'publication' && (
                    <div className="mt-2 space-y-2 text-sm">
                      <div className="flex items-center gap-2">
                        <IconCalendar size={14} className="text-linear-dark-muted" />
                        <span className="text-linear-dark-text">{metadata.year || 'N/A'}</span>
                      </div>
                      {metadata.venue && (
                        <div className="flex items-center gap-2">
                          <IconWorld size={14} className="text-linear-dark-muted" />
                          <span className="text-linear-dark-text">{metadata.venue}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-2">
                        <IconChartBar size={14} className="text-linear-dark-muted" />
                        <span className="text-linear-dark-text">{metadata.citationCount || 0} citations</span>
                      </div>
                      {metadata.influentialCitationCount !== undefined && (
                        <div className="flex items-center gap-2">
                          <IconTrendingUp size={14} className="text-linear-dark-muted" />
                          <span className="text-linear-dark-text">{metadata.influentialCitationCount} influential</span>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                <div className="border-t border-linear-dark-border"></div>

                {/* Authors */}
                {metadata.authors && metadata.authors.length > 0 && (
                  <>
                    <div>
                      <button
                        onClick={() => toggleAccordion('authors')}
                        className="w-full flex justify-between items-center py-2 text-white hover:text-white/80 transition-colors"
                      >
                        <span className="font-medium">Authors ({metadata.authors.length})</span>
                        <span className="text-linear-dark-muted">{expandedAccordion === 'authors' ? '−' : '+'}</span>
                      </button>
                      {expandedAccordion === 'authors' && (
                        <ul className="mt-2 space-y-1 text-sm">
                          {metadata.authors.map((author, idx) => (
                            <li key={idx} className="text-linear-dark-text">{author}</li>
                          ))}
                        </ul>
                      )}
                    </div>
                    <div className="border-t border-linear-dark-border"></div>
                  </>
                )}

                {/* Fields of Study */}
                {metadata.fieldsOfStudy && metadata.fieldsOfStudy.length > 0 && (
                  <>
                    <div>
                      <button
                        onClick={() => toggleAccordion('fields')}
                        className="w-full flex justify-between items-center py-2 text-white hover:text-white/80 transition-colors"
                      >
                        <span className="font-medium">Fields of Study</span>
                        <span className="text-linear-dark-muted">{expandedAccordion === 'fields' ? '−' : '+'}</span>
                      </button>
                      {expandedAccordion === 'fields' && (
                        <div className="mt-2 flex flex-wrap gap-2">
                          {metadata.fieldsOfStudy.map((field, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-1 rounded text-xs bg-purple-500/10 text-purple-400 border border-purple-500/20"
                            >
                              {field}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                    <div className="border-t border-linear-dark-border"></div>
                  </>
                )}

                {/* External Links */}
                <div>
                  <button
                    onClick={() => toggleAccordion('links')}
                    className="w-full flex justify-between items-center py-2 text-white hover:text-white/80 transition-colors"
                  >
                    <span className="font-medium">External Links</span>
                    <span className="text-linear-dark-muted">{expandedAccordion === 'links' ? '−' : '+'}</span>
                  </button>
                  {expandedAccordion === 'links' && (
                    <div className="mt-2 space-y-2 text-sm">
                      {metadata.url && (
                        <a
                          href={metadata.url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-blue-400 hover:text-blue-300 transition-colors"
                        >
                          <IconLink size={14} />
                          Semantic Scholar
                        </a>
                      )}
                      {metadata.openAccessPdf && (
                        <a
                          href={metadata.openAccessPdf}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="flex items-center gap-2 text-green-400 hover:text-green-300 transition-colors"
                        >
                          <IconFileDescription size={14} />
                          Open Access PDF
                        </a>
                      )}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Main Content Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* AI Analysis */}
            {summary && (
              <div className="bento-card p-6 border-amber-500/30 bg-gradient-to-br from-amber-500/5 to-transparent">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                  <IconSparkles size={20} className="text-amber-400" />
                  AI Analysis
                </h3>

                {/* Paper Title */}
                <div className="mb-4">
                  <p className="text-xs text-linear-dark-muted mb-1">Paper Title</p>
                  <p className="text-white font-medium">{summary.paper_title}</p>
                </div>

                {/* Analysis Thought Process */}
                {summary.analysis_thought_process && (
                  <div className="mb-4">
                    <p className="text-xs text-linear-dark-muted mb-1">Analysis Process</p>
                    <p className="text-sm text-linear-dark-text italic">"{summary.analysis_thought_process}"</p>
                  </div>
                )}

                {/* Novelty Analysis */}
                {summary.novelty && (
                  <div className="mb-4 p-4 rounded-linear bg-linear-dark-surface border border-linear-dark-border">
                    <p className="text-sm font-semibold text-white mb-2">Novelty Analysis</p>
                    <div className="space-y-2 text-sm">
                      <div>
                        <p className="text-linear-dark-muted">Status Quo:</p>
                        <p className="text-linear-dark-text">{summary.novelty.status_quo}</p>
                      </div>
                      <div>
                        <p className="text-linear-dark-muted">Proposed Change:</p>
                        <p className="text-linear-dark-text">{summary.novelty.proposed_delta}</p>
                      </div>
                      <div>
                        <p className="text-linear-dark-muted">Summary:</p>
                        <p className="text-linear-dark-text">{summary.novelty.novelty_summary}</p>
                      </div>
                      {summary.novelty.real_world_analogy && (
                        <div>
                          <p className="text-linear-dark-muted">Real-World Analogy:</p>
                          <p className="text-linear-dark-text italic">"{summary.novelty.real_world_analogy}"</p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Summary */}
                {summary.summary && (
                  <div className="mb-4 space-y-3">
                    <div>
                      <p className="text-xs font-semibold text-white mb-1">Main Contribution</p>
                      <p className="text-sm text-linear-dark-text">{summary.summary.main_contribution}</p>
                    </div>
                    <div>
                      <p className="text-xs font-semibold text-white mb-1">Methodology</p>
                      <p className="text-sm text-linear-dark-text">{summary.summary.methodology}</p>
                    </div>
                    {summary.summary.applications && (
                      <div>
                        <p className="text-xs font-semibold text-white mb-1">Applications</p>
                        <p className="text-sm text-linear-dark-text">{summary.summary.applications}</p>
                      </div>
                    )}
                    {summary.summary.limitations && (
                      <div>
                        <p className="text-xs font-semibold text-white mb-1">Limitations</p>
                        <p className="text-sm text-linear-dark-text">{summary.summary.limitations}</p>
                      </div>
                    )}
                  </div>
                )}

                {/* Benchmarks */}
                {summary.benchmarks && summary.benchmarks.length > 0 && (
                  <div>
                    <p className="text-sm font-semibold text-white mb-2">Benchmarks</p>
                    <div className="overflow-x-auto">
                      <table className="w-full text-sm">
                        <thead>
                          <tr className="border-b border-linear-dark-border">
                            <th className="text-left py-2 text-linear-dark-muted font-medium">Name</th>
                            <th className="text-left py-2 text-linear-dark-muted font-medium">Score</th>
                            <th className="text-left py-2 text-linear-dark-muted font-medium">Metric</th>
                          </tr>
                        </thead>
                        <tbody>
                          {summary.benchmarks.map((bench, idx) => (
                            <tr key={idx} className="border-b border-linear-dark-border/50">
                              <td className="py-2 text-linear-dark-text">{bench.name}</td>
                              <td className="py-2 text-white font-medium">{bench.score}</td>
                              <td className="py-2 text-linear-dark-text">{bench.metric}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Markdown Content */}
            {markdown && (
              <div className="bento-card p-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                  <IconFileText size={20} />
                  Paper Content
                </h3>
                <div className="prose prose-invert prose-sm max-w-none overflow-auto max-h-[600px]">
                  <ReactMarkdown
                    components={{
                      h1: ({ node, ...props }) => <h1 className="text-2xl font-bold text-white mt-6 mb-4" {...props} />,
                      h2: ({ node, ...props }) => <h2 className="text-xl font-semibold text-white mt-5 mb-3" {...props} />,
                      h3: ({ node, ...props }) => <h3 className="text-lg font-semibold text-white mt-4 mb-2" {...props} />,
                      p: ({ node, ...props }) => <p className="text-linear-dark-text leading-relaxed mb-3" {...props} />,
                      ul: ({ node, ...props }) => <ul className="list-disc list-inside text-linear-dark-text mb-3 space-y-1" {...props} />,
                      ol: ({ node, ...props }) => <ol className="list-decimal list-inside text-linear-dark-text mb-3 space-y-1" {...props} />,
                      li: ({ node, ...props }) => <li className="text-linear-dark-text" {...props} />,
                      code: ({ node, inline, ...props }: any) => 
                        inline ? (
                          <code className="bg-linear-dark-surface px-1 py-0.5 rounded text-amber-400 text-xs" {...props} />
                        ) : (
                          <code className="block bg-linear-dark-surface p-3 rounded-linear text-linear-dark-text text-xs overflow-x-auto" {...props} />
                        ),
                      a: ({ node, ...props }) => <a className="text-blue-400 hover:text-blue-300 underline" {...props} />,
                    }}
                  >
                    {markdown}
                  </ReactMarkdown>
                </div>
              </div>
            )}

            {/* Related Papers - Citations */}
            {metadata && Array.isArray(metadata.citations) && metadata.citations.length > 0 && (
              <div className="bento-card p-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                  <IconLink size={20} />
                  Papers Citing This Work ({metadata.citations.length})
                </h3>
                <div className="space-y-3">
                  {metadata.citations.map((citation, idx) => {
                    const relevanceScore = calculateRelevanceScore(citation, idx, false);
                    const classes = getRelevanceClasses(relevanceScore);
                    const iconData = getRelevanceIcon(relevanceScore);

                    return (
                      <div
                        key={idx}
                        className={`p-4 rounded-linear border-2 ${classes} transition-all duration-200`}
                      >
                        <div className="flex justify-between items-start gap-3">
                          <div className="flex-1">
                            <div className="flex items-start gap-2 mb-2">
                              {iconData && (
                                <iconData.Icon size={18} className={iconData.color} title={iconData.label} />
                              )}
                              <h4 className="text-sm font-semibold text-white">{citation.title || 'Untitled'}</h4>
                            </div>
                            
                            {citation.authors && citation.authors.length > 0 && (
                              <p className="text-xs text-linear-dark-muted mb-2">
                                {citation.authors.map((a: any) => a.name || 'Unknown').join(', ')}
                              </p>
                            )}

                            <div className="flex flex-wrap gap-2 items-center">
                              {citation.year && (
                                <span className="text-xs text-linear-dark-muted">{citation.year}</span>
                              )}
                              {citation.citationCount !== undefined && (
                                <span className="px-2 py-0.5 rounded text-xs bg-gray-500/10 text-gray-400 border border-gray-500/20">
                                  {citation.citationCount} citations
                                </span>
                              )}
                              {(citation.influentialCitationCount ?? 0) > 0 && (
                                <span className="px-2 py-0.5 rounded text-xs bg-orange-500/10 text-orange-400 border border-orange-500/20">
                                  {citation.influentialCitationCount} influential
                                </span>
                              )}
                              {citation.arxivId && (
                                <span className="px-2 py-0.5 rounded text-xs bg-green-500/10 text-green-400 border border-green-500/20">
                                  ArXiv: {citation.arxivId}
                                </span>
                              )}
                              {/* Debug score badge */}
                              <span className="px-2 py-0.5 rounded text-xs bg-purple-500/20 text-purple-300 border border-purple-500/40">
                                Score: {relevanceScore.toFixed(0)}
                              </span>
                            </div>

                            {citation.url && (
                              <a
                                href={citation.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 mt-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                              >
                                <IconLink size={12} />
                                View on Semantic Scholar
                              </a>
                            )}
                          </div>

                          <button
                            onClick={() => {
                              if (citation.paperId && citation.title) {
                                const authorNames = citation.authors.map((a: any) => a.name || 'Unknown');
                                onAddRelatedPaper(
                                  citation.paperId,
                                  citation.arxivId,
                                  citation.title,
                                  authorNames
                                );
                              }
                            }}
                            className="btn-secondary text-xs py-1 px-2 flex items-center gap-1 flex-shrink-0"
                            disabled={!citation.paperId || !citation.title}
                          >
                            <IconPlus size={12} />
                            Add
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Related Papers - Recommendations */}
            {metadata && Array.isArray(metadata.recommendations) && metadata.recommendations.length > 0 && (
              <div className="bento-card p-6">
                <h3 className="text-lg font-semibold text-white flex items-center gap-2 mb-4">
                  <IconTrendingUp size={20} />
                  Recommended Related Papers ({metadata.recommendations.length})
                </h3>
                <div className="space-y-3">
                  {metadata.recommendations.map((rec, idx) => {
                    const relevanceScore = calculateRelevanceScore(rec, idx, true);
                    const classes = getRelevanceClasses(relevanceScore);
                    const iconData = getRelevanceIcon(relevanceScore);

                    return (
                      <div
                        key={idx}
                        className={`p-4 rounded-linear border-2 ${classes} transition-all duration-200`}
                      >
                        <div className="flex justify-between items-start gap-3">
                          <div className="flex-1">
                            <div className="flex items-start gap-2 mb-2">
                              {iconData && (
                                <iconData.Icon size={18} className={iconData.color} title={iconData.label} />
                              )}
                              <h4 className="text-sm font-semibold text-white">{rec.title || 'Untitled'}</h4>
                            </div>
                            
                            {rec.authors && rec.authors.length > 0 && (
                              <p className="text-xs text-linear-dark-muted mb-2">
                                {rec.authors.map((a: any) => a.name || 'Unknown').join(', ')}
                              </p>
                            )}

                            <div className="flex flex-wrap gap-2 items-center">
                              {rec.year && (
                                <span className="text-xs text-linear-dark-muted">{rec.year}</span>
                              )}
                              {rec.citationCount !== undefined && (
                                <span className="px-2 py-0.5 rounded text-xs bg-gray-500/10 text-gray-400 border border-gray-500/20">
                                  {rec.citationCount} citations
                                </span>
                              )}
                              {(rec.influentialCitationCount ?? 0) > 0 && (
                                <span className="px-2 py-0.5 rounded text-xs bg-orange-500/10 text-orange-400 border border-orange-500/20">
                                  {rec.influentialCitationCount} influential
                                </span>
                              )}
                              {rec.arxivId && (
                                <span className="px-2 py-0.5 rounded text-xs bg-green-500/10 text-green-400 border border-green-500/20">
                                  ArXiv: {rec.arxivId}
                                </span>
                              )}
                              {/* Debug score badge */}
                              <span className="px-2 py-0.5 rounded text-xs bg-purple-500/20 text-purple-300 border border-purple-500/40">
                                Score: {relevanceScore.toFixed(0)}
                              </span>
                            </div>

                            {rec.url && (
                              <a
                                href={rec.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="inline-flex items-center gap-1 mt-2 text-xs text-blue-400 hover:text-blue-300 transition-colors"
                              >
                                <IconLink size={12} />
                                View on Semantic Scholar
                              </a>
                            )}
                          </div>

                          <button
                            onClick={() => {
                              if (rec.paperId && rec.title) {
                                const authorNames = rec.authors.map((a: any) => a.name || 'Unknown');
                                onAddRelatedPaper(
                                  rec.paperId,
                                  rec.arxivId,
                                  rec.title,
                                  authorNames
                                );
                              }
                            }}
                            className="btn-secondary text-xs py-1 px-2 flex items-center gap-1 flex-shrink-0"
                            disabled={!rec.paperId || !rec.title}
                          >
                            <IconPlus size={12} />
                            Add
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

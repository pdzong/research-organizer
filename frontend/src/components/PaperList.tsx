import { IconUsers, IconExternalLink, IconPlus, IconX } from '@tabler/icons-react';
import { useState } from 'react';
import { Paper } from '../services/api';

interface PaperListProps {
  papers: Paper[];
  loading: boolean;
  onSelectPaper: (paper: Paper) => void;
  onAddPaper: (arxivUrl: string) => Promise<void>;
  selectedPaperId: string | null;
}

export function PaperList({ papers, loading, onSelectPaper, onAddPaper, selectedPaperId }: PaperListProps) {
  const [modalOpened, setModalOpened] = useState(false);
  const [arxivUrl, setArxivUrl] = useState('');
  const [adding, setAdding] = useState(false);

  const handleAddPaper = async () => {
    if (!arxivUrl.trim()) return;
    
    try {
      setAdding(true);
      await onAddPaper(arxivUrl);
      setArxivUrl('');
      setModalOpened(false);
    } catch (error) {
      console.error('Error adding paper:', error);
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-white/20 border-t-white rounded-full animate-spin"></div>
          <p className="text-linear-dark-muted text-sm">Loading papers...</p>
        </div>
      </div>
    );
  }

  if (papers.length === 0) {
    return (
      <div className="flex items-center justify-center h-96">
        <p className="text-linear-dark-muted">No papers found</p>
      </div>
    );
  }

  return (
    <>
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-white">
          Research Papers <span className="text-linear-dark-muted">({papers.length})</span>
        </h2>
        <button
          onClick={() => setModalOpened(true)}
          className="btn-primary flex items-center gap-2"
        >
          <IconPlus size={16} />
          Add Paper
        </button>
      </div>

      {/* Bento Grid Layout */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 auto-rows-fr">
        {papers.map((paper, index) => {
          const isSelected = selectedPaperId === paper.id;
          // Make every 5th card span 2 columns for bento effect
          const spanTwo = (index + 1) % 5 === 0;
          
          return (
            <div
              key={paper.id}
              onClick={() => onSelectPaper(paper)}
              className={`
                bento-card bento-card-hover p-6 
                ${spanTwo ? 'md:col-span-2' : ''}
                ${isSelected ? 'ring-2 ring-white/20 bg-linear-dark-hover' : ''}
              `}
            >
              <div className="flex flex-col gap-3 h-full">
                {/* Title */}
                <h3 className="text-base font-semibold text-white line-clamp-2">
                  {paper.title}
                </h3>

                {/* Authors */}
                <div className="flex items-center gap-2 text-sm text-linear-dark-muted">
                  <IconUsers size={14} className="flex-shrink-0" />
                  <p className="line-clamp-1">{paper.authors.join(', ')}</p>
                </div>

                {/* ArXiv Badge & Link */}
                {paper.arxiv_id && (
                  <div className="flex items-center gap-2 mt-auto">
                    <span className="px-2 py-1 rounded text-xs bg-blue-500/10 text-blue-400 border border-blue-500/20">
                      ArXiv: {paper.arxiv_id}
                    </span>
                    {paper.arxiv_url && (
                      <a
                        href={paper.arxiv_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        onClick={(e) => e.stopPropagation()}
                        className="flex items-center gap-1 text-xs text-linear-dark-muted hover:text-white transition-colors"
                      >
                        <IconExternalLink size={12} />
                        View
                      </a>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Modal */}
      {modalOpened && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
          <div className="bento-card p-6 max-w-md w-full">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold text-white">Add New Paper</h3>
              <button
                onClick={() => setModalOpened(false)}
                className="p-1 hover:bg-white/5 rounded transition-colors"
              >
                <IconX size={20} className="text-linear-dark-muted" />
              </button>
            </div>
            
            <div className="flex flex-col gap-4">
              <div>
                <label className="block text-sm font-medium text-linear-dark-text mb-2">
                  ArXiv URL
                </label>
                <input
                  type="text"
                  placeholder="https://arxiv.org/abs/1706.03762"
                  value={arxivUrl}
                  onChange={(e) => setArxivUrl(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleAddPaper();
                    }
                  }}
                  className="w-full px-3 py-2 bg-linear-dark-bg border border-linear-dark-border rounded-linear text-linear-dark-text placeholder-linear-dark-muted focus:outline-none focus:border-white/30 transition-colors"
                />
              </div>
              
              <div className="flex justify-end gap-2">
                <button
                  onClick={() => setModalOpened(false)}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={handleAddPaper}
                  disabled={!arxivUrl.trim() || adding}
                  className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
                >
                  {adding ? (
                    <>
                      <div className="w-4 h-4 border-2 border-black/20 border-t-black rounded-full animate-spin"></div>
                      Adding...
                    </>
                  ) : (
                    'Add Paper'
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

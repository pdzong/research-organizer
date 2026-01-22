import { useState, useEffect } from 'react';
import { Layout } from './components/Layout';
import { PaperList } from './components/PaperList';
import { PaperDetail } from './components/PaperDetail';
import { 
  fetchPapers, 
  parsePaper, 
  analyzePaper, 
  addPaper, 
  getPaperMetadata, 
  getCachedAnalysis, 
  getCacheStatus, 
  addRelatedPaper,
  Paper, 
  Analysis, 
  PaperMetadata, 
  CacheStatus 
} from './services/api';

// Simple toast notification function
function showToast(message: string, type: 'success' | 'error' = 'success') {
  // Create toast element
  const toast = document.createElement('div');
  toast.className = `fixed top-4 right-4 z-50 px-4 py-3 rounded-linear shadow-linear transition-all duration-300 ${
    type === 'success' 
      ? 'bg-green-500/20 border border-green-500/40 text-green-200' 
      : 'bg-red-500/20 border border-red-500/40 text-red-200'
  }`;
  toast.textContent = message;
  
  document.body.appendChild(toast);
  
  // Fade in
  setTimeout(() => {
    toast.style.opacity = '1';
  }, 10);
  
  // Remove after 3 seconds
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => {
      document.body.removeChild(toast);
    }, 300);
  }, 3000);
}

function App() {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [summary, setSummary] = useState<Analysis | null>(null);
  const [metadata, setMetadata] = useState<PaperMetadata | null>(null);
  const [cacheStatus, setCacheStatus] = useState<CacheStatus>({ metadata: false, markdown: false, analysis: false });
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [loadingMetadata, setLoadingMetadata] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch papers on mount
  useEffect(() => {
    const loadPapers = async () => {
      try {
        setLoading(true);
        const data = await fetchPapers();
        setPapers(data);
      } catch (err) {
        console.error('Error fetching papers:', err);
        setError('Failed to load papers');
      } finally {
        setLoading(false);
      }
    };

    loadPapers();
  }, []);

  const handleSelectPaper = async (paper: Paper) => {
    setSelectedPaper(paper);
    setMarkdown(null);
    setSummary(null);
    setMetadata(null);
    setError(null);
    
    // Load cache status and auto-load data (cached or fresh)
    if (paper.arxiv_id) {
      try {
        const status = await getCacheStatus(paper.arxiv_id);
        setCacheStatus(status);
        
        // Always load metadata (from cache if available, otherwise fetch fresh)
        setLoadingMetadata(true);
        const metadataResponse = await getPaperMetadata(paper.arxiv_id, false);
        if (metadataResponse.success && metadataResponse.metadata) {
          setMetadata(metadataResponse.metadata);
        }
        setLoadingMetadata(false);
        
        // Auto-load cached markdown (only if cached - user must click to load if not)
        if (status.markdown) {
          setParsing(true);
          const response = await parsePaper(paper.id, paper.arxiv_url || undefined, false);
          if (response.success && response.markdown) {
            setMarkdown(response.markdown);
          }
          setParsing(false);
        }
        
        // Auto-load cached analysis (only if cached - user must click to analyze if not)
        if (status.analysis) {
          setAnalyzing(true);
          const response = await getCachedAnalysis(paper.arxiv_id, false);
          if (response.success && response.data) {
            setSummary(response.data);
          }
          setAnalyzing(false);
        }
      } catch (err) {
        console.error('Error loading data:', err);
      }
    }
  };

  const handleParsePaper = async (forceReload: boolean = false) => {
    if (!selectedPaper) return;

    try {
      setParsing(true);
      setError(null);
      const response = await parsePaper(selectedPaper.id, selectedPaper.arxiv_url || undefined, forceReload);

      if (response.success && response.markdown) {
        setMarkdown(response.markdown);
        // Update cache status
        if (selectedPaper.arxiv_id) {
          const status = await getCacheStatus(selectedPaper.arxiv_id);
          setCacheStatus(status);
        }
      } else {
        setError(response.error || 'Failed to parse paper');
      }
    } catch (err) {
      console.error('Error parsing paper:', err);
      setError('Failed to parse paper');
    } finally {
      setParsing(false);
    }
  };

  const handleAnalyzePaper = async (forceReload: boolean = false) => {
    if (!selectedPaper?.arxiv_id) return;

    try {
      setAnalyzing(true);
      setError(null);
      const response = await getCachedAnalysis(selectedPaper.arxiv_id, forceReload);

      if (response.success && response.data) {
        setSummary(response.data);
        // Update cache status
        const status = await getCacheStatus(selectedPaper.arxiv_id);
        setCacheStatus(status);
      } else {
        setError(response.error || 'Failed to analyze paper');
      }
    } catch (err) {
      console.error('Error analyzing paper:', err);
      setError('Failed to analyze paper');
    } finally {
      setAnalyzing(false);
    }
  };
  
  const handleReloadMetadata = async () => {
    if (!selectedPaper?.arxiv_id) return;

    try {
      setLoadingMetadata(true);
      setError(null);
      const response = await getPaperMetadata(selectedPaper.arxiv_id, true);

      if (response.success && response.metadata) {
        setMetadata(response.metadata);
        // Update cache status
        const status = await getCacheStatus(selectedPaper.arxiv_id);
        setCacheStatus(status);
      } else {
        setError(response.error || 'Failed to reload metadata');
      }
    } catch (err) {
      console.error('Error reloading metadata:', err);
      setError('Failed to reload metadata');
    } finally {
      setLoadingMetadata(false);
    }
  };

  const handleBack = () => {
    setSelectedPaper(null);
    setMarkdown(null);
    setSummary(null);
    setMetadata(null);
    setError(null);
  };

  const handleAddPaper = async (arxivUrl: string) => {
    try {
      const response = await addPaper(arxivUrl);
      
      if (response.success && response.paper) {
        // Refresh the papers list
        const data = await fetchPapers();
        setPapers(data);
        
        showToast(`Added paper: ${response.paper.title}`, 'success');
      } else {
        showToast(response.error || 'Failed to add paper', 'error');
      }
    } catch (err) {
      console.error('Error adding paper:', err);
      showToast('Failed to add paper. Please check the URL and try again.', 'error');
      throw err;
    }
  };

  const handleAddRelatedPaper = async (
    paperId: string,
    arxivId: string | null,
    title: string,
    authors: string[]
  ) => {
    try {
      const response = await addRelatedPaper(paperId, arxivId, title, authors);
      
      if (response.success && response.paper) {
        // Refresh the papers list
        const data = await fetchPapers();
        setPapers(data);
        
        showToast(`Added paper: ${response.paper.title}`, 'success');
      } else {
        showToast(response.error || 'Failed to add paper', 'error');
      }
    } catch (err) {
      console.error('Error adding related paper:', err);
      showToast('Failed to add related paper.', 'error');
    }
  };

  return (
    <Layout>
      {!selectedPaper ? (
        <PaperList
          papers={papers}
          loading={loading}
          onSelectPaper={handleSelectPaper}
          onAddPaper={handleAddPaper}
          selectedPaperId={selectedPaper?.id || null}
        />
      ) : (
        <PaperDetail
          paper={selectedPaper}
          markdown={markdown}
          summary={summary}
          metadata={metadata}
          cacheStatus={cacheStatus}
          loading={parsing}
          analyzing={analyzing}
          loadingMetadata={loadingMetadata}
          error={error}
          onParse={handleParsePaper}
          onAnalyze={handleAnalyzePaper}
          onReloadMetadata={handleReloadMetadata}
          onAddRelatedPaper={handleAddRelatedPaper}
          onBack={handleBack}
        />
      )}
    </Layout>
  );
}

export default App;

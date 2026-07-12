import { useState, useEffect } from 'react';
import { Container } from '@mantine/core';
import { Notifications, notifications } from '@mantine/notifications';
import { Layout, AppView } from './components/Layout';
import { PaperList } from './components/PaperList';
import { PaperDetail } from './components/PaperDetail';
import { ApplicationList } from './components/ApplicationList';
import { ApplicationDetail } from './components/ApplicationDetail';
import { SolutionList } from './components/SolutionList';
import { SolutionDetail } from './components/SolutionDetail';
import { AutoResearchView } from './components/AutoResearchView';
import { DiscoverView } from './components/DiscoverView';
import {
  fetchPapers,
  parsePaper,
  addPaper,
  getPaperMetadata,
  getCachedAnalysis,
  getCacheStatus,
  addRelatedPaper,
  addApplication,
  fetchApplications,
  fetchSolutions,
  generateSolutionPlan,
  Paper,
  Analysis,
  PaperMetadata,
  CacheStatus,
  ApplicationIdea,
  SimplePaperInfo,
  ApplicationEntry,
  SolutionPlanRecord,
} from './services/api';

function App() {
  // View state
  const [currentView, setCurrentView] = useState<AppView>('papers');

  // Papers state
  const [papers, setPapers] = useState<Paper[]>([]);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [markdown, setMarkdown] = useState<string | null>(null);
  const [summary, setSummary] = useState<Analysis | null>(null);
  const [metadata, setMetadata] = useState<PaperMetadata | null>(null);
  const [cacheStatus, setCacheStatus] = useState<CacheStatus>({
    metadata: false,
    markdown: false,
    sections: false,
    analysis: false,
  });
  const [loading, setLoading] = useState(true);
  const [parsing, setParsing] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [loadingMetadata, setLoadingMetadata] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Applications state
  const [applications, setApplications] = useState<ApplicationEntry[]>([]);
  const [selectedApplication, setSelectedApplication] = useState<ApplicationEntry | null>(null);
  const [loadingApplications, setLoadingApplications] = useState(true);
  const [generatingPlan, setGeneratingPlan] = useState(false);

  // Solutions state
  const [solutions, setSolutions] = useState<SolutionPlanRecord[]>([]);
  const [selectedSolution, setSelectedSolution] = useState<SolutionPlanRecord | null>(null);
  const [loadingSolutions, setLoadingSolutions] = useState(false);
  const [regeneratingSolution, setRegeneratingSolution] = useState(false);

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

  // Fetch applications on mount
  useEffect(() => {
    const loadApplications = async () => {
      try {
        setLoadingApplications(true);
        const data = await fetchApplications();
        setApplications(data);
      } catch (err) {
        console.error('Error fetching applications:', err);
      } finally {
        setLoadingApplications(false);
      }
    };

    loadApplications();
  }, []);

  // Lazy-load solutions when entering the view
  const loadSolutions = async () => {
    try {
      setLoadingSolutions(true);
      const data = await fetchSolutions();
      setSolutions(data);
    } catch (err) {
      console.error('Error fetching solutions:', err);
    } finally {
      setLoadingSolutions(false);
    }
  };

  useEffect(() => {
    if (currentView === 'solutions' && solutions.length === 0) {
      loadSolutions();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentView]);

  const handleSelectPaper = async (paper: Paper) => {
    setSelectedPaper(paper);
    setMarkdown(null);
    setSummary(null);
    setMetadata(null);
    setError(null);

    if (paper.arxiv_id) {
      try {
        const status = await getCacheStatus(paper.arxiv_id);
        setCacheStatus(status);

        try {
          setLoadingMetadata(true);
          const metadataResponse = await getPaperMetadata(paper.arxiv_id, false);
          if (metadataResponse.success && metadataResponse.metadata) {
            setMetadata(metadataResponse.metadata);
          } else {
            console.error('Metadata fetch failed:', metadataResponse.error);
            setError(metadataResponse.error || 'Failed to load metadata');
          }
        } catch (metadataErr) {
          console.error('Error fetching metadata:', metadataErr);
          setError('Failed to load metadata from Semantic Scholar');
        } finally {
          setLoadingMetadata(false);
        }

        if (status.markdown) {
          try {
            setParsing(true);
            const response = await parsePaper(paper.id, paper.arxiv_url || undefined, false);
            if (response.success && response.markdown) {
              setMarkdown(response.markdown);
            }
          } finally {
            setParsing(false);
          }
        }

        if (status.analysis) {
          try {
            setAnalyzing(true);
            const response = await getCachedAnalysis(paper.arxiv_id, false);
            if (response.success && response.data) {
              setSummary(response.data);
            }
          } finally {
            setAnalyzing(false);
          }
        }
      } catch (err) {
        console.error('Error loading data:', err);
        setError('Failed to load paper data');
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
        const data = await fetchPapers();
        setPapers(data);

        notifications.show({
          title: 'Success',
          message: `Added paper: ${response.paper.title}`,
          color: 'green',
        });
      } else {
        notifications.show({
          title: 'Error',
          message: response.error || 'Failed to add paper',
          color: 'red',
        });
      }
    } catch (err) {
      console.error('Error adding paper:', err);
      notifications.show({
        title: 'Error',
        message: 'Failed to add paper. Please check the URL and try again.',
        color: 'red',
      });
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
        const data = await fetchPapers();
        setPapers(data);

        notifications.show({
          title: 'Success',
          message: `Added paper: ${response.paper.title}`,
          color: 'green',
        });
      } else {
        notifications.show({
          title: 'Error',
          message: response.error || 'Failed to add paper',
          color: 'red',
        });
      }
    } catch (err) {
      console.error('Error adding related paper:', err);
      notifications.show({
        title: 'Error',
        message: 'Failed to add related paper.',
        color: 'red',
      });
    }
  };

  const handleAddApplication = async (
    application: ApplicationIdea,
    relatedPapers: SimplePaperInfo[]
  ) => {
    if (!selectedPaper) return;

    try {
      const currentPaper: SimplePaperInfo = {
        title: selectedPaper.title,
        authors: selectedPaper.authors,
        arxiv_id: selectedPaper.arxiv_id || undefined,
      };

      const response = await addApplication(application, currentPaper, relatedPapers);

      if (response.success) {
        const data = await fetchApplications();
        setApplications(data);

        notifications.show({
          title: 'Success',
          message: response.message || 'Application saved successfully',
          color: 'green',
        });
      } else {
        notifications.show({
          title: 'Error',
          message: response.error || 'Failed to save application',
          color: 'red',
        });
      }
    } catch (err) {
      console.error('Error adding application:', err);
      notifications.show({
        title: 'Error',
        message: 'Failed to save application.',
        color: 'red',
      });
    }
  };

  const handleViewChange = (view: AppView) => {
    setCurrentView(view);
    setSelectedPaper(null);
    setSelectedApplication(null);
    setSelectedSolution(null);
    setMarkdown(null);
    setSummary(null);
    setMetadata(null);
    setError(null);
  };

  const handleSelectApplication = (application: ApplicationEntry) => {
    setSelectedApplication(application);
  };

  const handleBackFromApplication = () => {
    setSelectedApplication(null);
  };

  const handleGeneratePlan = async (application: ApplicationEntry, forceReload: boolean = false) => {
    try {
      setGeneratingPlan(true);
      const response = await generateSolutionPlan(application.id, forceReload);
      if (response.success && response.plan) {
        const record: SolutionPlanRecord = {
          application_id: application.id,
          generated_at: response.generated_at,
          plan: response.plan,
          markdown: response.markdown,
          brief: response.brief,
        };
        setSolutions((prev) => {
          const filtered = prev.filter((s) => s.application_id !== application.id);
          return [record, ...filtered];
        });
        setSelectedSolution(record);
        setSelectedApplication(null);
        setCurrentView('solutions');
        notifications.show({
          title: response.from_cache ? 'Plan loaded from cache' : 'System plan generated',
          message: response.plan.name,
          color: 'green',
        });
      } else {
        notifications.show({
          title: 'Plan generation failed',
          message: response.error || 'Unknown error',
          color: 'red',
        });
      }
    } catch (err: any) {
      console.error('Error generating plan:', err);
      notifications.show({
        title: 'Plan generation failed',
        message: err?.message || 'Unknown error',
        color: 'red',
      });
    } finally {
      setGeneratingPlan(false);
    }
  };

  const handleRegenerateSolution = async () => {
    if (!selectedSolution?.application_id) return;
    const app = applications.find((a) => a.id === selectedSolution.application_id);
    if (!app) {
      notifications.show({
        title: 'Cannot regenerate',
        message: 'Source application is no longer available.',
        color: 'red',
      });
      return;
    }
    try {
      setRegeneratingSolution(true);
      await handleGeneratePlan(app, true);
    } finally {
      setRegeneratingSolution(false);
    }
  };

  const renderPapersView = () =>
    !selectedPaper ? (
      <PaperList
        papers={papers}
        loading={loading}
        onSelectPaper={handleSelectPaper}
        onAddPaper={handleAddPaper}
        selectedPaperId={null}
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
        onAddApplication={handleAddApplication}
        onBack={handleBack}
      />
    );

  const renderApplicationsView = () =>
    !selectedApplication ? (
      <ApplicationList
        applications={applications}
        loading={loadingApplications}
        onSelectApplication={handleSelectApplication}
        selectedApplicationId={null}
      />
    ) : (
      <ApplicationDetail
        application={selectedApplication}
        onBack={handleBackFromApplication}
        onGeneratePlan={(app) => handleGeneratePlan(app, false)}
        generatingPlan={generatingPlan}
      />
    );

  const renderSolutionsView = () =>
    !selectedSolution ? (
      <SolutionList
        solutions={solutions}
        loading={loadingSolutions}
        onSelectSolution={(rec) => setSelectedSolution(rec)}
        selectedApplicationId={null}
      />
    ) : (
      <SolutionDetail
        record={selectedSolution}
        onBack={() => setSelectedSolution(null)}
        onRegenerate={handleRegenerateSolution}
        regenerating={regeneratingSolution}
      />
    );

  return (
    <Layout currentView={currentView} onViewChange={handleViewChange}>
      <Notifications />
      <Container size="xl">
        {currentView === 'papers' && renderPapersView()}
        {currentView === 'discover' && <DiscoverView />}
        {currentView === 'applications' && renderApplicationsView()}
        {currentView === 'solutions' && renderSolutionsView()}
        {currentView === 'auto-research' && <AutoResearchView />}
      </Container>
    </Layout>
  );
}

export default App;

import {
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  SegmentedControl,
  Select,
  Stack,
  Text,
  TextInput,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconCalendar,
  IconExternalLink,
  IconPlus,
  IconQuote,
  IconSearch,
  IconUsers,
} from '@tabler/icons-react';
import { useEffect, useMemo, useState } from 'react';
import {
  addPaperFromSource,
  discoverPapers,
  DiscoverSort,
  fetchSources,
  Paper,
  SourceInfo,
  SourcePaper,
} from '../services/api';

interface DiscoverPapersProps {
  libraryPapers: Paper[];
  onLibraryRefresh: () => Promise<void>;
}

const DAYS_OPTIONS = [
  { value: '7', label: 'Last week' },
  { value: '30', label: 'Last month' },
  { value: '90', label: 'Last 3 months' },
  { value: '365', label: 'Last year' },
];

export function DiscoverPapers({ libraryPapers, onLibraryRefresh }: DiscoverPapersProps) {
  const [sources, setSources] = useState<SourceInfo[]>([]);
  const [sourceId, setSourceId] = useState<string | null>(null);
  const [field, setField] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [sort, setSort] = useState<DiscoverSort>('relevance');
  const [days, setDays] = useState('30');
  const [results, setResults] = useState<SourcePaper[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addingId, setAddingId] = useState<string | null>(null);

  // ids already in the library (primary id or arXiv id)
  const libraryIds = useMemo(() => {
    const ids = new Set<string>();
    libraryPapers.forEach((p) => {
      ids.add(p.id);
      if (p.arxiv_id) ids.add(p.arxiv_id);
    });
    return ids;
  }, [libraryPapers]);

  const isInLibrary = (paper: SourcePaper) =>
    libraryIds.has(paper.id) ||
    (paper.external_ids?.arxiv ? libraryIds.has(paper.external_ids.arxiv) : false);

  useEffect(() => {
    fetchSources()
      .then((data) => {
        setSources(data);
        if (data.length > 0) {
          const preferred = data.find((s) => s.id === 'openalex') ?? data[0];
          setSourceId(preferred.id);
        }
      })
      .catch(() => setError('Failed to load sources'));
  }, []);

  useEffect(() => {
    if (!sourceId) return;
    let cancelled = false;

    const load = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await discoverPapers(sourceId, {
          query: activeQuery || undefined,
          field: field || undefined,
          days: parseInt(days, 10),
          limit: 25,
          sort,
        });
        if (cancelled) return;
        if (response.success) {
          setResults(response.papers);
        } else {
          setError(response.error || 'Discovery failed');
          setResults([]);
        }
      } catch {
        if (!cancelled) {
          setError('Failed to fetch papers from source');
          setResults([]);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    load();
    return () => {
      cancelled = true;
    };
  }, [sourceId, field, activeQuery, sort, days]);

  const currentSource = sources.find((s) => s.id === sourceId);

  const handleSourceChange = (value: string | null) => {
    setSourceId(value);
    setField(null); // field ids are source-specific
  };

  const handleAdd = async (paper: SourcePaper) => {
    try {
      setAddingId(paper.id);
      const response = await addPaperFromSource(paper);
      if (response.success) {
        await onLibraryRefresh();
        notifications.show({
          title: 'Paper added',
          message: paper.title,
          color: 'green',
        });
      } else {
        notifications.show({
          title: 'Could not add paper',
          message: response.error || 'Unknown error',
          color: 'red',
        });
      }
    } catch (err) {
      notifications.show({
        title: 'Error',
        message: 'Failed to add paper',
        color: 'red',
      });
    } finally {
      setAddingId(null);
    }
  };

  return (
    <Stack gap="md">
      <Group align="flex-end" gap="sm" wrap="wrap">
        <Select
          label="Source"
          data={sources.map((s) => ({ value: s.id, label: s.label }))}
          value={sourceId}
          onChange={handleSourceChange}
          w={170}
          allowDeselect={false}
        />
        <Select
          label="Field"
          placeholder="All fields"
          data={(currentSource?.fields ?? []).map((f) => ({ value: f.id, label: f.label }))}
          value={field}
          onChange={setField}
          w={240}
          clearable
          searchable
        />
        <Select
          label="Period"
          data={DAYS_OPTIONS}
          value={days}
          onChange={(v) => setDays(v ?? '30')}
          w={140}
          allowDeselect={false}
        />
        <TextInput
          label="Search"
          placeholder="e.g. protein folding, agentic RAG..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') setActiveQuery(query.trim());
          }}
          leftSection={<IconSearch size={16} />}
          style={{ flexGrow: 1, minWidth: 220 }}
        />
        <Button onClick={() => setActiveQuery(query.trim())} variant="light">
          Search
        </Button>
      </Group>

      <Group justify="space-between">
        <SegmentedControl
          value={sort}
          onChange={(v) => setSort(v as DiscoverSort)}
          data={[
            { value: 'relevance', label: 'Relevance' },
            { value: 'recency', label: 'Newest' },
            { value: 'citations', label: 'Most cited' },
          ]}
          size="xs"
        />
        {!loading && (
          <Text size="sm" c="dimmed">
            {results.length} papers
          </Text>
        )}
      </Group>

      {loading ? (
        <Center h={200}>
          <Stack align="center">
            <Loader />
            <Text c="dimmed" size="sm">
              Discovering papers...
            </Text>
          </Stack>
        </Center>
      ) : error ? (
        <Center h={120}>
          <Text c="red">{error}</Text>
        </Center>
      ) : results.length === 0 ? (
        <Center h={120}>
          <Text c="dimmed">No papers found — try a broader period or another field.</Text>
        </Center>
      ) : (
        results.map((paper) => {
          const added = isInLibrary(paper);
          return (
            <Card key={paper.id} shadow="sm" padding="lg" radius="md" withBorder>
              <Stack gap="xs">
                <Group justify="space-between" wrap="nowrap" align="flex-start">
                  <Text fw={600} size="lg">
                    {paper.title}
                  </Text>
                  <Button
                    size="xs"
                    variant={added ? 'default' : 'filled'}
                    disabled={added}
                    loading={addingId === paper.id}
                    leftSection={<IconPlus size={14} />}
                    onClick={() => handleAdd(paper)}
                    style={{ flexShrink: 0 }}
                  >
                    {added ? 'In library' : 'Add'}
                  </Button>
                </Group>

                {paper.authors.length > 0 && (
                  <Group gap="xs">
                    <IconUsers size={16} />
                    <Text size="sm" c="dimmed">
                      {paper.authors.slice(0, 5).join(', ')}
                      {paper.authors.length > 5 ? ' et al.' : ''}
                    </Text>
                  </Group>
                )}

                <Group gap="xs">
                  <Badge color="gray" variant="light">
                    {paper.source}
                  </Badge>
                  {paper.published_date && (
                    <Badge color="blue" variant="light" leftSection={<IconCalendar size={12} />}>
                      {paper.published_date}
                    </Badge>
                  )}
                  {paper.citation_count !== null && paper.citation_count > 0 && (
                    <Badge color="grape" variant="light" leftSection={<IconQuote size={12} />}>
                      {paper.citation_count} citations
                    </Badge>
                  )}
                  {paper.relevance_score !== null && (
                    <Badge color="teal" variant="light">
                      relevance {paper.relevance_score.toFixed(1)}
                    </Badge>
                  )}
                  {paper.is_open_access && (
                    <Badge color="green" variant="light">
                      Open Access
                    </Badge>
                  )}
                  {paper.fields_of_study.slice(0, 2).map((f) => (
                    <Badge key={f} color="cyan" variant="outline">
                      {f}
                    </Badge>
                  ))}
                </Group>

                {paper.abstract && (
                  <Text size="sm" c="dimmed" lineClamp={3}>
                    {paper.abstract}
                  </Text>
                )}

                <Group gap="xs">
                  {paper.venue && (
                    <Text size="xs" c="dimmed">
                      {paper.venue}
                    </Text>
                  )}
                  {paper.landing_url && (
                    <Button
                      component="a"
                      href={paper.landing_url}
                      target="_blank"
                      variant="subtle"
                      size="xs"
                      rightSection={<IconExternalLink size={14} />}
                    >
                      View source
                    </Button>
                  )}
                </Group>
              </Stack>
            </Card>
          );
        })
      )}
    </Stack>
  );
}

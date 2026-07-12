import { useEffect, useState } from 'react';
import {
  Alert,
  Badge,
  Button,
  Card,
  Center,
  Group,
  Loader,
  Modal,
  NumberInput,
  Select,
  Stack,
  Switch,
  Text,
  TextInput,
  Textarea,
  Title,
  Tooltip,
} from '@mantine/core';
import {
  IconBuildingSkyscraper,
  IconExternalLink,
  IconPlus,
  IconSearch,
  IconTargetArrow,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import {
  CompanyProfile,
  CompanyProfileInput,
  SourcePaperResult,
  StrategicFitAssessment,
  activateProfile,
  addPaperFromSource,
  addPaper,
  createProfile,
  discoverForProfile,
  fetchProfiles,
  searchSource,
} from '../services/api';

const ACTION_COLORS: Record<string, string> = {
  ignore: 'gray',
  watch: 'yellow',
  analyze: 'orange',
  prototype: 'red',
};

function splitLines(value: string): string[] {
  return value
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean);
}

function FitBadge({ fit }: { fit: StrategicFitAssessment }) {
  return (
    <Tooltip label={fit.relevance_summary} withArrow multiline w={340}>
      <Group gap={6}>
        <Badge color={ACTION_COLORS[fit.recommended_action] || 'gray'} variant="filled">
          {fit.recommended_action} · {fit.fit_score}/100
        </Badge>
      </Group>
    </Tooltip>
  );
}

interface ProfileFormProps {
  opened: boolean;
  onClose: () => void;
  onCreated: (profile: CompanyProfile) => void;
}

function ProfileFormModal({ opened, onClose, onCreated }: ProfileFormProps) {
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState('');
  const [description, setDescription] = useState('');
  const [techStack, setTechStack] = useState('');
  const [watchTopics, setWatchTopics] = useState('');
  const [questions, setQuestions] = useState('');
  const [assumptions, setAssumptions] = useState('');
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!name.trim() || !watchTopics.trim()) return;
    const payload: CompanyProfileInput = {
      name: name.trim(),
      industry: industry.trim() || null,
      description: description.trim() || null,
      tech_stack: splitLines(techStack),
      strategic_questions: splitLines(questions),
      watch_topics: splitLines(watchTopics),
      assumptions: splitLines(assumptions),
    };
    try {
      setSaving(true);
      const profile = await createProfile(payload);
      notifications.show({ title: 'Profile created', message: profile.name, color: 'green' });
      onCreated(profile);
      onClose();
    } catch (err: any) {
      notifications.show({
        title: 'Failed to create profile',
        message: err?.message || 'Unknown error',
        color: 'red',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal opened={opened} onClose={onClose} title="New company research profile" size="lg">
      <Stack gap="sm">
        <TextInput
          label="Company name"
          placeholder="Acme Conversational AI"
          required
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <TextInput
          label="Industry"
          placeholder="Customer support software"
          value={industry}
          onChange={(e) => setIndustry(e.target.value)}
        />
        <Textarea
          label="What the company builds"
          placeholder="Chat-based customer support bots for e-commerce…"
          autosize
          minRows={2}
          value={description}
          onChange={(e) => setDescription(e.target.value)}
        />
        <Textarea
          label="Watch topics (one per line) — used for discovery searches"
          placeholder={'retrieval augmented generation\nsmall language models'}
          required
          autosize
          minRows={2}
          value={watchTopics}
          onChange={(e) => setWatchTopics(e.target.value)}
        />
        <Textarea
          label="Tech stack (one per line)"
          placeholder={'Python\nRAG pipelines'}
          autosize
          minRows={2}
          value={techStack}
          onChange={(e) => setTechStack(e.target.value)}
        />
        <Textarea
          label="Strategic questions (one per line)"
          placeholder="Will on-device LLMs make our cloud offering obsolete?"
          autosize
          minRows={2}
          value={questions}
          onChange={(e) => setQuestions(e.target.value)}
        />
        <Textarea
          label="Strategic assumptions (one per line) — papers challenging these are flagged"
          placeholder="Customers will keep paying for cloud-hosted inference"
          autosize
          minRows={2}
          value={assumptions}
          onChange={(e) => setAssumptions(e.target.value)}
        />
        <Group justify="flex-end">
          <Button variant="subtle" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleSave} loading={saving} disabled={!name.trim() || !watchTopics.trim()}>
            Create profile
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

function ResultCard({
  paper,
  onAdd,
  adding,
}: {
  paper: SourcePaperResult;
  onAdd: (paper: SourcePaperResult) => void;
  adding: boolean;
}) {
  const fit = paper.strategic_fit;
  return (
    <Card shadow="sm" padding="md" radius="md" withBorder>
      <Stack gap="xs">
        <Group justify="space-between" wrap="nowrap" align="flex-start">
          <Text fw={600}>{paper.title}</Text>
          <Button
            size="xs"
            variant="light"
            leftSection={<IconPlus size={14} />}
            loading={adding}
            onClick={() => onAdd(paper)}
          >
            Add
          </Button>
        </Group>

        {paper.authors.length > 0 && (
          <Text size="sm" c="dimmed">
            {paper.authors.slice(0, 6).join(', ')}
            {paper.authors.length > 6 ? ' et al.' : ''}
          </Text>
        )}

        <Group gap="xs">
          <Badge color="grape" variant="light">
            {paper.source}
          </Badge>
          {paper.is_open_access && (
            <Badge color="green" variant="light">
              open access
            </Badge>
          )}
          {paper.published_date && (
            <Badge color="gray" variant="light">
              {paper.published_date}
            </Badge>
          )}
          {paper.matched_topic && (
            <Badge color="blue" variant="light">
              topic: {paper.matched_topic}
            </Badge>
          )}
          {fit && <FitBadge fit={fit} />}
          {paper.landing_url && (
            <Button
              component="a"
              href={paper.landing_url}
              target="_blank"
              variant="subtle"
              size="compact-xs"
              rightSection={<IconExternalLink size={12} />}
              onClick={(e) => e.stopPropagation()}
            >
              Source
            </Button>
          )}
        </Group>

        {fit && (
          <Alert color={ACTION_COLORS[fit.recommended_action] || 'gray'} variant="light" p="xs">
            <Text size="sm">{fit.relevance_summary}</Text>
            {fit.challenged_assumptions.length > 0 && (
              <Text size="xs" c="red" mt={4}>
                Challenges assumptions: {fit.challenged_assumptions.join('; ')}
              </Text>
            )}
          </Alert>
        )}

        {paper.abstract && (
          <Text size="sm" c="dimmed" lineClamp={3}>
            {paper.abstract}
          </Text>
        )}
      </Stack>
    </Card>
  );
}

export function DiscoverView() {
  const [profiles, setProfiles] = useState<CompanyProfile[]>([]);
  const [activeProfileId, setActiveProfileId] = useState<string | null>(null);
  const [profileModalOpen, setProfileModalOpen] = useState(false);

  const [query, setQuery] = useState('');
  const [since, setSince] = useState('');
  const [scoreResults, setScoreResults] = useState(true);
  const [scoreTop, setScoreTop] = useState<number | string>(3);

  const [results, setResults] = useState<SourcePaperResult[]>([]);
  const [topicsSearched, setTopicsSearched] = useState<string[]>([]);
  const [searching, setSearching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [addingId, setAddingId] = useState<string | null>(null);

  const loadProfiles = async () => {
    try {
      const data = await fetchProfiles();
      setProfiles(data.profiles);
      setActiveProfileId(data.active_profile_id);
    } catch (err) {
      console.error('Error loading profiles:', err);
    }
  };

  useEffect(() => {
    loadProfiles();
  }, []);

  const handleProfileChange = async (id: string | null) => {
    setActiveProfileId(id);
    if (id) {
      try {
        await activateProfile(id);
      } catch (err) {
        console.error('Error activating profile:', err);
      }
    }
  };

  const handleKeywordSearch = async () => {
    if (!query.trim()) return;
    try {
      setSearching(true);
      setError(null);
      setTopicsSearched([]);
      const data = await searchSource({ query: query.trim(), since: since || undefined });
      setResults(data.papers);
      if (!data.success) setError(data.error || 'Search failed');
    } catch (err: any) {
      setError(err?.message || 'Search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleProfileDiscover = async () => {
    if (!activeProfileId) return;
    try {
      setSearching(true);
      setError(null);
      const data = await discoverForProfile({
        profileId: activeProfileId,
        since: since || undefined,
        scoreTop: scoreResults ? Number(scoreTop) || 0 : 0,
      });
      setResults(data.papers);
      setTopicsSearched(data.topics_searched);
      if (!data.success) setError(data.error || 'Discovery failed');
      else if (data.error) setError(`Partial results — ${data.error}`);
    } catch (err: any) {
      setError(err?.message || 'Discovery failed');
    } finally {
      setSearching(false);
    }
  };

  const handleAdd = async (paper: SourcePaperResult) => {
    try {
      setAddingId(paper.id);
      const response =
        paper.source === 'openalex'
          ? await addPaperFromSource('openalex', paper.source_record_id)
          : paper.pdf_url
            ? await addPaper(paper.pdf_url)
            : { success: false, paper: null, message: null, error: 'No addable reference' };
      if (response.success) {
        notifications.show({ title: 'Added to library', message: paper.title, color: 'green' });
      } else {
        notifications.show({
          title: 'Could not add paper',
          message: response.error || 'Unknown error',
          color: 'red',
        });
      }
    } catch (err: any) {
      notifications.show({
        title: 'Could not add paper',
        message: err?.message || 'Unknown error',
        color: 'red',
      });
    } finally {
      setAddingId(null);
    }
  };

  const activeProfile = profiles.find((p) => p.id === activeProfileId) || null;

  return (
    <Stack gap="lg">
      <Group justify="space-between" align="flex-end">
        <div>
          <Title order={3}>Discover research</Title>
          <Text size="sm" c="dimmed">
            Search OpenAlex directly, or run company-profiled discovery with strategic-fit scoring.
          </Text>
        </div>
      </Group>

      <Card withBorder radius="md" padding="md">
        <Stack gap="sm">
          <Group align="flex-end" gap="sm">
            <Select
              label="Company profile"
              placeholder={profiles.length ? 'Select profile' : 'No profiles yet'}
              data={profiles.map((p) => ({ value: p.id, label: p.name }))}
              value={activeProfileId}
              onChange={handleProfileChange}
              leftSection={<IconBuildingSkyscraper size={16} />}
              w={280}
              clearable
            />
            <Button variant="light" leftSection={<IconPlus size={16} />} onClick={() => setProfileModalOpen(true)}>
              New profile
            </Button>
            <TextInput
              label="Published since (optional)"
              placeholder="2026-01-01"
              value={since}
              onChange={(e) => setSince(e.target.value)}
              w={180}
            />
            <Switch
              label="Score results for strategic fit"
              checked={scoreResults}
              onChange={(e) => setScoreResults(e.currentTarget.checked)}
              mb={6}
            />
            {scoreResults && (
              <NumberInput label="Score top N" value={scoreTop} onChange={setScoreTop} min={1} max={10} w={110} />
            )}
          </Group>

          {activeProfile && (
            <Group gap={6}>
              <Text size="xs" c="dimmed">
                Watch topics:
              </Text>
              {activeProfile.watch_topics.map((t) => (
                <Badge key={t} size="sm" variant="dot" color="blue">
                  {t}
                </Badge>
              ))}
            </Group>
          )}

          <Group align="flex-end" gap="sm">
            <TextInput
              label="Keyword search"
              placeholder="e.g. retrieval augmented generation"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleKeywordSearch()}
              style={{ flex: 1 }}
              leftSection={<IconSearch size={16} />}
            />
            <Button onClick={handleKeywordSearch} loading={searching} disabled={!query.trim()}>
              Search OpenAlex
            </Button>
            <Button
              color="grape"
              leftSection={<IconTargetArrow size={16} />}
              onClick={handleProfileDiscover}
              loading={searching}
              disabled={!activeProfileId}
            >
              Discover for company
            </Button>
          </Group>
        </Stack>
      </Card>

      {error && (
        <Alert color="red" variant="light">
          {error}
        </Alert>
      )}

      {topicsSearched.length > 0 && !searching && (
        <Text size="sm" c="dimmed">
          Searched {topicsSearched.length} watch topic{topicsSearched.length > 1 ? 's' : ''}: {topicsSearched.join(', ')}
        </Text>
      )}

      {searching ? (
        <Center h={200}>
          <Stack align="center">
            <Loader />
            <Text c="dimmed" size="sm">
              Searching{scoreResults && activeProfileId ? ' and scoring strategic fit (LLM)…' : '…'}
            </Text>
          </Stack>
        </Center>
      ) : results.length > 0 ? (
        <Stack gap="sm">
          <Text fw={600}>{results.length} papers</Text>
          {results.map((paper) => (
            <ResultCard key={paper.id} paper={paper} onAdd={handleAdd} adding={addingId === paper.id} />
          ))}
        </Stack>
      ) : (
        <Center h={120}>
          <Text c="dimmed" size="sm">
            No results yet — run a keyword search or company discovery.
          </Text>
        </Center>
      )}

      <ProfileFormModal
        opened={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
        onCreated={async (profile) => {
          await loadProfiles();
          setActiveProfileId(profile.id);
        }}
      />
    </Stack>
  );
}

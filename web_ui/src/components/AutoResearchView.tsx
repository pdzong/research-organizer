import { useEffect, useRef, useState } from 'react';
import {
  Paper,
  Stack,
  Text,
  Button,
  Group,
  Badge,
  NumberInput,
  Select,
  Switch,
  Card,
  Code,
  ScrollArea,
  Divider,
  Alert,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconRobot,
  IconPlayerPlay,
  IconPlayerStop,
  IconRefresh,
  IconAlertCircle,
} from '@tabler/icons-react';
import {
  AutoResearchSource,
  AutoResearchStatus,
  fetchAutoResearchSources,
  getAutoResearchStatus,
  startAutoResearch,
  stopAutoResearch,
} from '../services/api';

const STATE_COLORS: Record<string, string> = {
  idle: 'gray',
  running: 'blue',
  stopping: 'orange',
  stopped: 'gray',
  error: 'red',
};

export function AutoResearchView() {
  const [sources, setSources] = useState<AutoResearchSource[]>([]);
  const [status, setStatus] = useState<AutoResearchStatus | null>(null);
  const [loading, setLoading] = useState(false);

  // Form state
  const [source, setSource] = useState<string>('huggingface');
  const [limit, setLimit] = useState<number>(5);
  const [continuous, setContinuous] = useState<boolean>(false);
  const [intervalSeconds, setIntervalSeconds] = useState<number>(300);

  const pollRef = useRef<number | null>(null);

  // Initial load: sources + status
  useEffect(() => {
    (async () => {
      try {
        const srcs = await fetchAutoResearchSources();
        setSources(srcs);
        if (srcs.length && !srcs.find((s) => s.id === source)) {
          setSource(srcs[0].id);
        }
      } catch (e) {
        console.error(e);
      }
      try {
        const r = await getAutoResearchStatus();
        setStatus(r.status);
        // Reflect persisted runner config on first load
        if (r.status) {
          setSource(r.status.source);
          setLimit(r.status.limit);
          setContinuous(r.status.continuous);
          setIntervalSeconds(r.status.interval_seconds);
        }
      } catch (e) {
        console.error(e);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Poll while running / stopping
  useEffect(() => {
    const isActive = status?.state === 'running' || status?.state === 'stopping';
    if (!isActive) {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
      return;
    }
    if (pollRef.current) return;
    pollRef.current = window.setInterval(async () => {
      try {
        const r = await getAutoResearchStatus();
        setStatus(r.status);
      } catch (e) {
        console.error(e);
      }
    }, 2000);
    return () => {
      if (pollRef.current) {
        window.clearInterval(pollRef.current);
        pollRef.current = null;
      }
    };
  }, [status?.state]);

  const handleStart = async () => {
    try {
      setLoading(true);
      const r = await startAutoResearch({
        source,
        limit,
        continuous,
        interval_seconds: intervalSeconds,
      });
      setStatus(r.status);
      if (!r.success) {
        notifications.show({
          title: 'Could not start',
          message: r.error || 'Unknown error',
          color: 'red',
        });
      } else {
        notifications.show({
          title: 'Auto-research started',
          message: `Source: ${source}, limit: ${limit}, continuous: ${continuous ? 'yes' : 'no'}`,
          color: 'green',
        });
      }
    } catch (e: any) {
      notifications.show({
        title: 'Could not start',
        message: e?.message || 'Unknown error',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleStop = async () => {
    try {
      setLoading(true);
      const r = await stopAutoResearch();
      setStatus(r.status);
      notifications.show({
        title: 'Stop requested',
        message: 'Runner will finish the current paper and stop.',
        color: 'blue',
      });
    } catch (e: any) {
      notifications.show({
        title: 'Could not stop',
        message: e?.message || 'Unknown error',
        color: 'red',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    try {
      const r = await getAutoResearchStatus();
      setStatus(r.status);
    } catch (e) {
      console.error(e);
    }
  };

  const isRunning = status?.state === 'running' || status?.state === 'stopping';

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Group>
          <IconRobot size={28} color="#228be6" />
          <div>
            <Text size="xl" fw={700}>Auto-Research</Text>
            <Text size="sm" c="dimmed">
              Continuously scan a paper source and run the full pipeline (parse → analyze → derive applications) on each one.
            </Text>
          </div>
        </Group>
      </Group>

      {/* Config */}
      <Paper shadow="sm" p="lg" withBorder>
        <Stack gap="md">
          <Text fw={600}>Configuration</Text>
          <Group grow align="flex-end">
            <Select
              label="Source"
              data={sources.length ? sources.map((s) => ({ value: s.id, label: s.label })) : [{ value: source, label: source }]}
              value={source}
              onChange={(v) => v && setSource(v)}
              disabled={isRunning}
            />
            <NumberInput
              label="Limit (papers per batch)"
              min={1}
              max={50}
              value={limit}
              onChange={(v) => setLimit(typeof v === 'number' ? v : parseInt(String(v) || '5', 10))}
              disabled={isRunning}
            />
          </Group>
          <Group grow align="flex-end">
            <Switch
              label="Continuous mode"
              description="Keep looping after each batch instead of stopping"
              checked={continuous}
              onChange={(e) => setContinuous(e.currentTarget.checked)}
              disabled={isRunning}
            />
            <NumberInput
              label="Interval between batches (seconds)"
              min={10}
              max={86400}
              value={intervalSeconds}
              onChange={(v) =>
                setIntervalSeconds(typeof v === 'number' ? v : parseInt(String(v) || '300', 10))
              }
              disabled={isRunning || !continuous}
            />
          </Group>

          <Group justify="flex-end" gap="xs">
            <Button
              variant="subtle"
              leftSection={<IconRefresh size={14} />}
              onClick={handleRefresh}
            >
              Refresh status
            </Button>
            {isRunning ? (
              <Button
                color="red"
                leftSection={<IconPlayerStop size={14} />}
                onClick={handleStop}
                loading={loading}
              >
                Stop
              </Button>
            ) : (
              <Button
                leftSection={<IconPlayerPlay size={14} />}
                onClick={handleStart}
                loading={loading}
              >
                Start
              </Button>
            )}
          </Group>
        </Stack>
      </Paper>

      {/* Status */}
      <Paper shadow="sm" p="lg" withBorder>
        <Group justify="space-between" mb="sm">
          <Text fw={600}>Status</Text>
          {status && (
            <Badge color={STATE_COLORS[status.state] || 'gray'} size="lg" variant="filled">
              {status.state.toUpperCase()}
            </Badge>
          )}
        </Group>

        {status?.last_error && (
          <Alert
            icon={<IconAlertCircle size={16} />}
            color="red"
            title="Last error"
            mb="sm"
          >
            {status.last_error}
          </Alert>
        )}

        {status && (
          <Group gap="xl">
            <Stat label="Processed" value={status.processed_count} color="teal" />
            <Stat label="Skipped (cached)" value={status.skipped_count} color="gray" />
            <Stat label="Errors" value={status.error_count} color="red" />
            <Stat label="Applications saved" value={status.application_count} color="grape" />
          </Group>
        )}

        <Divider my="sm" />

        <Group gap="xl">
          <div>
            <Text size="xs" c="dimmed" fw={600}>Current paper</Text>
            <Text size="sm">{status?.current_arxiv_id || '—'}</Text>
          </div>
          <div>
            <Text size="xs" c="dimmed" fw={600}>Current step</Text>
            <Text size="sm">{status?.current_step || '—'}</Text>
          </div>
          <div>
            <Text size="xs" c="dimmed" fw={600}>Started at</Text>
            <Text size="sm">{status?.started_at ? new Date(status.started_at).toLocaleString() : '—'}</Text>
          </div>
        </Group>
      </Paper>

      {/* Live log */}
      <Paper shadow="sm" p="lg" withBorder>
        <Text fw={600} mb="sm">Live log</Text>
        <ScrollArea h={300}>
          <Stack gap={2}>
            {status?.log?.length ? (
              status.log
                .slice()
                .reverse()
                .map((entry, i) => (
                  <Card
                    key={i}
                    padding={6}
                    withBorder={false}
                    bg={
                      entry.level === 'error'
                        ? 'red.0'
                        : entry.level === 'warn'
                        ? 'yellow.0'
                        : undefined
                    }
                  >
                    <Group gap="xs" wrap="nowrap" align="flex-start">
                      <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace', minWidth: 90 }}>
                        {new Date(entry.ts).toLocaleTimeString()}
                      </Text>
                      <Badge
                        size="xs"
                        variant="light"
                        color={
                          entry.level === 'error'
                            ? 'red'
                            : entry.level === 'warn'
                            ? 'yellow'
                            : 'blue'
                        }
                      >
                        {entry.level}
                      </Badge>
                      <Code style={{ background: 'transparent', fontSize: 12 }}>
                        {entry.message}
                      </Code>
                    </Group>
                  </Card>
                ))
            ) : (
              <Text size="sm" c="dimmed">No log entries yet.</Text>
            )}
          </Stack>
        </ScrollArea>
      </Paper>
    </Stack>
  );
}

function Stat({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div>
      <Text size="xs" c="dimmed" fw={600}>
        {label}
      </Text>
      <Badge size="xl" variant="light" color={color}>
        {value}
      </Badge>
    </div>
  );
}

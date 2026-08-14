import { useEffect, useState } from 'react';
import {
  Modal,
  Stack,
  Text,
  Group,
  Button,
  Select,
  Autocomplete,
  Badge,
  Divider,
  Alert,
  Loader,
  Paper,
  Title,
  Tooltip,
  Box,
  ThemeIcon,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import {
  IconAlertCircle,
  IconRefresh,
  IconRestore,
  IconSparkles,
  IconCheck,
  IconCoins,
  IconClock,
} from '@tabler/icons-react';
import {
  getLlmConfig,
  updateLlmConfig,
  resetLlmConfig,
  refreshLlmModels,
  LlmConfigResponse,
  LlmRoleBinding,
  LlmModelMetadata,
} from '../services/api';

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function LlmConfigModal({ opened, onClose }: Props) {
  const [config, setConfig] = useState<LlmConfigResponse | null>(null);
  const [draft, setDraft] = useState<Record<string, LlmRoleBinding>>({});
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (forceRefresh: boolean = false) => {
    setLoading(true);
    setError(null);
    try {
      const cfg = await getLlmConfig(forceRefresh);
      setConfig(cfg);
      setDraft({ ...cfg.roles });
    } catch (e: any) {
      setError(e?.message || 'Failed to load LLM config');
    } finally {
      setLoading(false);
    }
  };

  const handleSyncLive = async () => {
    setSyncing(true);
    try {
      const cfg = await refreshLlmModels();
      setConfig(cfg);
      notifications.show({
        title: 'Catalog Synced',
        message: 'Loaded latest live models from provider APIs.',
        color: 'teal',
        icon: <IconCheck size={16} />,
      });
    } catch (e: any) {
      notifications.show({
        title: 'Sync Notice',
        message: e?.message || 'Using curated model catalog.',
        color: 'yellow',
        icon: <IconAlertCircle size={16} />,
      });
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    if (opened) load();
  }, [opened]);

  const handleProviderChange = (role: string, provider: string) => {
    if (!config) return;
    const suggestions = config.providers[provider]?.suggested_models || [];
    const nextModel = suggestions[0] || draft[role]?.model || '';
    setDraft((prev) => ({
      ...prev,
      [role]: { provider, model: nextModel },
    }));
  };

  const handleModelChange = (role: string, model: string) => {
    setDraft((prev) => ({
      ...prev,
      [role]: { ...prev[role], model },
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const payload: Record<string, Partial<LlmRoleBinding>> = {};
      for (const [role, binding] of Object.entries(draft)) {
        payload[role] = { provider: binding.provider, model: binding.model };
      }
      const res = await updateLlmConfig(payload);
      if (res.success) {
        notifications.show({ title: 'Saved', message: 'LLM routing updated.', color: 'green' });
        setConfig((prev) => (prev ? { ...prev, roles: res.roles } : prev));
        onClose();
      }
    } catch (e: any) {
      const msg = e?.response?.data?.detail || e?.message || 'Failed to save';
      notifications.show({ title: 'Save failed', message: msg, color: 'red' });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    setSaving(true);
    try {
      const res = await resetLlmConfig();
      setDraft({ ...res.roles });
      setConfig((prev) => (prev ? { ...prev, roles: res.roles } : prev));
      notifications.show({ title: 'Reset', message: 'Reverted to defaults.', color: 'blue' });
    } catch (e: any) {
      notifications.show({ title: 'Reset failed', message: e?.message || 'Unknown error', color: 'red' });
    } finally {
      setSaving(false);
    }
  };

  const roleDescMap: Record<string, string> = {};
  (config?.role_descriptions || []).forEach((r) => {
    roleDescMap[r.id] = r.description;
  });

  const getModelMeta = (provider: string, modelId: string): LlmModelMetadata | undefined => {
    if (!config) return undefined;
    const provInfo = config.providers[provider];
    return provInfo?.models?.find((m) => m.id === modelId);
  };

  const formatPrice = (meta?: LlmModelMetadata) => {
    if (!meta) return null;
    if (meta.input_price_per_1m === 0 && meta.output_price_per_1m === 0) {
      return 'Free / Local';
    }
    if (meta.input_price_per_1m != null && meta.output_price_per_1m != null) {
      return `$${meta.input_price_per_1m.toFixed(2)} in / $${meta.output_price_per_1m.toFixed(2)} out per 1M tokens`;
    }
    return null;
  };

  const getTierBadgeColor = (tier?: string) => {
    switch (tier) {
      case 'flagship':
        return 'violet';
      case 'balanced':
        return 'blue';
      case 'fast':
        return 'teal';
      case 'reasoning':
        return 'indigo';
      case 'local':
        return 'grape';
      default:
        return 'gray';
    }
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={
        <Group gap="sm">
          <ThemeIcon size="md" radius="sm" color="blue" variant="light">
            <IconSparkles size={18} />
          </ThemeIcon>
          <Title order={4}>LLM Provider & Model Routing</Title>
        </Group>
      }
      size="xl"
      centered
    >
      {loading && !config ? (
        <Group justify="center" py="xl"><Loader /></Group>
      ) : error ? (
        <Alert icon={<IconAlertCircle size={16} />} color="red">{error}</Alert>
      ) : config ? (
        <Stack gap="md">
          <Text size="sm" c="dimmed">
            Configure which model powers each backend reasoning role. The catalog features current
            frontier models (including GPT-5.6, Claude 4.6, Gemini 3.7) with transparent token pricing,
            context lengths, and instant zero-latency loading.
          </Text>

          {/* Providers bar */}
          <Paper withBorder p="sm" radius="sm" bg="var(--mantine-color-body)">
            <Group justify="space-between" align="center" mb="xs">
              <Text size="sm" fw={600}>Provider Status & Catalogs</Text>
              <Button
                size="xs"
                variant="light"
                color="blue"
                leftSection={syncing ? <Loader size={12} color="blue" /> : <IconRefresh size={12} />}
                onClick={handleSyncLive}
                disabled={syncing}
              >
                {syncing ? 'Syncing APIs...' : 'Sync Live Models'}
              </Button>
            </Group>
            <Group gap="xs" wrap="wrap">
              {Object.entries(config.providers).map(([id, info]) => (
                <Tooltip
                  key={id}
                  label={
                    info.key_present
                      ? `${info.active_env} is configured · ${
                          info.models_source === 'live'
                            ? 'live API catalog active'
                            : info.models_source === 'cached'
                              ? 'cached catalog'
                              : info.models_error
                                ? `curated catalog (${info.models_error})`
                                : 'curated catalog with pricing'
                        }`
                      : `Missing API key. Set in .env: ${info.env_keys.join(' / ')}`
                  }
                  withArrow
                >
                  <Group gap={4} wrap="nowrap">
                    <Badge
                      color={info.key_present ? 'teal' : 'gray'}
                      variant={info.key_present ? 'filled' : 'light'}
                    >
                      {info.label} {info.key_present ? '✓' : '✗'}
                    </Badge>
                    <Badge
                      color={
                        info.models_source === 'live'
                          ? 'blue'
                          : info.models_source === 'curated'
                            ? 'teal'
                            : 'yellow'
                      }
                      variant="light"
                    >
                      {info.models_source === 'live' ? 'live' : 'catalog'}
                    </Badge>
                  </Group>
                </Tooltip>
              ))}
            </Group>
          </Paper>

          <Divider />

          {/* Roles Configuration */}
          <Stack gap="sm">
            {Object.entries(draft).map(([role, binding]) => {
              const providerOptions = Object.entries(config.providers).map(([pid, info]) => ({
                value: pid,
                label: `${info.label}${info.key_present ? '' : ' (no key)'}`,
              }));

              const currentProv = config.providers[binding.provider];
              const suggestions = Array.from(
                new Set(
                  [binding.model, ...(currentProv?.suggested_models || [])].filter(Boolean)
                )
              );

              const activeMeta = getModelMeta(binding.provider, binding.model);
              const priceText = formatPrice(activeMeta);
              const defaultBinding = config.defaults[role];
              const isDefault =
                binding.provider === defaultBinding?.provider &&
                binding.model === defaultBinding?.model;

              return (
                <Paper key={role} withBorder p="sm" radius="sm">
                  <Group justify="space-between" mb={6} wrap="nowrap">
                    <Box>
                      <Group gap="xs">
                        <Text fw={600} size="sm" tt="capitalize">
                          {role.replace(/_/g, ' ')}
                        </Text>
                        {!isDefault && (
                          <Badge size="xs" color="yellow" variant="light">
                            overridden
                          </Badge>
                        )}
                        {activeMeta?.tier && (
                          <Badge size="xs" color={getTierBadgeColor(activeMeta.tier)} variant="outline">
                            {activeMeta.tier}
                          </Badge>
                        )}
                      </Group>
                      <Text size="xs" c="dimmed">{roleDescMap[role] || ''}</Text>
                    </Box>
                    <Text size="xs" c="dimmed">
                      Default: <code>{defaultBinding?.provider}/{defaultBinding?.model}</code>
                    </Text>
                  </Group>

                  <Group grow align="flex-start">
                    <Select
                      label="Provider"
                      data={providerOptions}
                      value={binding.provider}
                      onChange={(v) => v && handleProviderChange(role, v)}
                    />
                    <Stack gap={4}>
                      <Autocomplete
                        label="Model"
                        data={suggestions}
                        value={binding.model}
                        onChange={(v) => handleModelChange(role, v)}
                        placeholder="model id (e.g. gpt-5.6)"
                      />
                    </Stack>
                  </Group>

                  {/* Model Metadata & Pricing Card */}
                  {activeMeta && (
                    <Box mt="xs" pt="xs" style={{ borderTop: '1px solid var(--mantine-color-default-border)' }}>
                      <Group justify="space-between" wrap="wrap" gap="xs">
                        <Group gap="xs">
                          <Text size="xs" fw={600}>
                            {activeMeta.name}
                          </Text>
                          {activeMeta.context_window && (
                            <Badge size="xs" variant="dot" color="gray">
                              <Group gap={2} wrap="nowrap">
                                <IconClock size={10} />
                                <span>{activeMeta.context_window}</span>
                              </Group>
                            </Badge>
                          )}
                          {priceText && (
                            <Badge size="xs" variant="light" color="teal">
                              <Group gap={2} wrap="nowrap">
                                <IconCoins size={10} />
                                <span>{priceText}</span>
                              </Group>
                            </Badge>
                          )}
                        </Group>
                        {activeMeta.description && (
                          <Text size="xs" c="dimmed" fs="italic">
                            {activeMeta.description}
                          </Text>
                        )}
                      </Group>
                    </Box>
                  )}
                </Paper>
              );
            })}
          </Stack>

          <Group justify="space-between" mt="md">
            <Button
              variant="subtle"
              color="gray"
              leftSection={<IconRestore size={14} />}
              onClick={handleReset}
              disabled={saving}
            >
              Reset to defaults
            </Button>
            <Group>
              <Button
                variant="subtle"
                leftSection={<IconRefresh size={14} />}
                onClick={() => load(false)}
                disabled={saving || loading}
              >
                Reload
              </Button>
              <Button variant="default" onClick={onClose} disabled={saving}>
                Cancel
              </Button>
              <Button onClick={handleSave} loading={saving}>
                Save Changes
              </Button>
            </Group>
          </Group>
        </Stack>
      ) : null}
    </Modal>
  );
}

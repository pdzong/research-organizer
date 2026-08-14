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
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconAlertCircle, IconRefresh, IconRestore } from '@tabler/icons-react';
import {
  getLlmConfig,
  updateLlmConfig,
  resetLlmConfig,
  LlmConfigResponse,
  LlmRoleBinding,
} from '../services/api';

interface Props {
  opened: boolean;
  onClose: () => void;
}

export function LlmConfigModal({ opened, onClose }: Props) {
  const [config, setConfig] = useState<LlmConfigResponse | null>(null);
  const [draft, setDraft] = useState<Record<string, LlmRoleBinding>>({});
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const cfg = await getLlmConfig();
      setConfig(cfg);
      setDraft({ ...cfg.roles });
    } catch (e: any) {
      setError(e?.message || 'Failed to load LLM config');
    } finally {
      setLoading(false);
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

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={<Title order={4}>LLM provider & model routing</Title>}
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
            Choose which provider + model handles each role. The model dropdown is filled from each
            provider&apos;s live catalog when an API key is present, and falls back to a static list otherwise.
            Custom model ids are still allowed. Changes are persisted to{' '}
            <code>backend/data/llm_config.json</code> and take effect immediately for new calls.
          </Text>

          <Paper withBorder p="sm" radius="sm">
            <Text size="sm" fw={600} mb="xs">Providers</Text>
            <Group gap="xs" wrap="wrap">
              {Object.entries(config.providers).map(([id, info]) => (
                <Tooltip
                  key={id}
                  label={
                    info.key_present
                      ? `${info.active_env} is set${
                          info.models_source === 'live'
                            ? ' · live model catalog'
                            : info.models_error
                              ? ` · static list (${info.models_error})`
                              : ' · static model list'
                        }`
                      : `Missing API key. Set one of: ${info.env_keys.join(' / ')}`
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
                    {info.key_present && (
                      <Badge
                        color={info.models_source === 'live' ? 'blue' : 'yellow'}
                        variant="light"
                      >
                        {info.models_source === 'live' ? 'live' : 'static'}
                      </Badge>
                    )}
                  </Group>
                </Tooltip>
              ))}
            </Group>
          </Paper>

          <Divider />

          <Stack gap="sm">
            {Object.entries(draft).map(([role, binding]) => {
              const providerOptions = Object.entries(config.providers).map(([pid, info]) => ({
                value: pid,
                label: `${info.label}${info.key_present ? '' : ' (no key)'}`,
              }));
              const suggestions = Array.from(
                new Set(
                  [binding.model, ...(config.providers[binding.provider]?.suggested_models || [])].filter(Boolean)
                )
              );
              const defaultBinding = config.defaults[role];
              const isDefault =
                binding.provider === defaultBinding?.provider &&
                binding.model === defaultBinding?.model;
              return (
                <Paper key={role} withBorder p="sm" radius="sm">
                  <Group justify="space-between" mb={4} wrap="nowrap">
                    <Box>
                      <Group gap="xs">
                        <Text fw={600} size="sm" tt="capitalize">{role.replace(/_/g, ' ')}</Text>
                        {!isDefault && (
                          <Badge size="xs" color="yellow" variant="light">overridden</Badge>
                        )}
                      </Group>
                      <Text size="xs" c="dimmed">{roleDescMap[role] || ''}</Text>
                    </Box>
                    <Text size="xs" c="dimmed">
                      Default: <code>{defaultBinding?.provider}/{defaultBinding?.model}</code>
                    </Text>
                  </Group>
                  <Group grow>
                    <Select
                      label="Provider"
                      data={providerOptions}
                      value={binding.provider}
                      onChange={(v) => v && handleProviderChange(role, v)}
                    />
                    <Autocomplete
                      label="Model"
                      data={suggestions}
                      value={binding.model}
                      onChange={(v) => handleModelChange(role, v)}
                      placeholder="model id (custom values allowed)"
                    />
                  </Group>
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
                onClick={load}
                disabled={saving}
              >
                Reload
              </Button>
              <Button variant="default" onClick={onClose} disabled={saving}>Cancel</Button>
              <Button onClick={handleSave} loading={saving}>Save</Button>
            </Group>
          </Group>
        </Stack>
      ) : null}
    </Modal>
  );
}

import { useState } from 'react';
import { AppShell, Title, Text, Group, SegmentedControl, ActionIcon, Tooltip } from '@mantine/core';
import { IconFlask, IconFileText, IconBulb, IconRocket, IconRobot, IconSettings, IconTelescope } from '@tabler/icons-react';
import { ReactNode } from 'react';
import { LlmConfigModal } from './LlmConfigModal';

export type AppView = 'papers' | 'discover' | 'applications' | 'solutions' | 'auto-research';

interface LayoutProps {
  children: ReactNode;
  currentView: AppView;
  onViewChange: (view: AppView) => void;
}

export function Layout({ children, currentView, onViewChange }: LayoutProps) {
  const [settingsOpen, setSettingsOpen] = useState(false);

  return (
    <AppShell
      header={{ height: 70 }}
      padding="md"
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <IconFlask size={32} color="#228be6" />
            <div>
              <Title order={2}>Research Paper Analyzer</Title>
              <Text size="xs" c="dimmed">
                Analyze papers, derive applications, generate codegen-ready system plans
              </Text>
            </div>
          </Group>

          <Group gap="md">
            <SegmentedControl
              value={currentView}
              onChange={(value) => onViewChange(value as AppView)}
              size="sm"
              data={[
                {
                  value: 'papers',
                  label: (
                    <Group gap="xs" wrap="nowrap">
                      <IconFileText size={14} />
                      <span>Papers</span>
                    </Group>
                  ),
                },
                {
                  value: 'discover',
                  label: (
                    <Group gap="xs" wrap="nowrap">
                      <IconTelescope size={14} />
                      <span>Discover</span>
                    </Group>
                  ),
                },
                {
                  value: 'applications',
                  label: (
                    <Group gap="xs" wrap="nowrap">
                      <IconBulb size={14} />
                      <span>Applications</span>
                    </Group>
                  ),
                },
                {
                  value: 'solutions',
                  label: (
                    <Group gap="xs" wrap="nowrap">
                      <IconRocket size={14} />
                      <span>Solutions</span>
                    </Group>
                  ),
                },
                {
                  value: 'auto-research',
                  label: (
                    <Group gap="xs" wrap="nowrap">
                      <IconRobot size={14} />
                      <span>Auto-Research</span>
                    </Group>
                  ),
                },
              ]}
            />

            <Tooltip label="LLM provider & model settings" withArrow>
              <ActionIcon
                variant="subtle"
                size="lg"
                onClick={() => setSettingsOpen(true)}
                aria-label="Settings"
              >
                <IconSettings size={20} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>
      </AppShell.Header>

      <AppShell.Main>
        {children}
      </AppShell.Main>

      <LlmConfigModal opened={settingsOpen} onClose={() => setSettingsOpen(false)} />
    </AppShell>
  );
}

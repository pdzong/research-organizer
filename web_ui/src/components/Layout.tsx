import { AppShell, Title, Text, Group, SegmentedControl } from '@mantine/core';
import { IconFlask, IconFileText, IconBulb, IconRocket, IconRobot } from '@tabler/icons-react';
import { ReactNode } from 'react';

export type AppView = 'papers' | 'applications' | 'solutions' | 'auto-research';

interface LayoutProps {
  children: ReactNode;
  currentView: AppView;
  onViewChange: (view: AppView) => void;
}

export function Layout({ children, currentView, onViewChange }: LayoutProps) {
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
        </Group>
      </AppShell.Header>

      <AppShell.Main>
        {children}
      </AppShell.Main>
    </AppShell>
  );
}

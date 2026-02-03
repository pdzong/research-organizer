import { AppShell, Title, Text, Group, SegmentedControl } from '@mantine/core';
import { IconFlask, IconFileText, IconBulb } from '@tabler/icons-react';
import { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
  currentView: 'papers' | 'applications';
  onViewChange: (view: 'papers' | 'applications') => void;
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
                Analyze papers from HuggingFace with AI
              </Text>
            </div>
          </Group>
          
          <SegmentedControl
            value={currentView}
            onChange={(value) => onViewChange(value as 'papers' | 'applications')}
            data={[
              {
                value: 'papers',
                label: (
                  <Group gap="xs">
                    <IconFileText size={16} />
                    <span>Papers</span>
                  </Group>
                ),
              },
              {
                value: 'applications',
                label: (
                  <Group gap="xs">
                    <IconBulb size={16} />
                    <span>Applications</span>
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

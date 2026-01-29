import { AppShell, Title, Text, Group } from '@mantine/core';
import { IconFlask } from '@tabler/icons-react';
import { ReactNode } from 'react';

interface LayoutProps {
  children: ReactNode;
}

export function Layout({ children }: LayoutProps) {
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
        </Group>
      </AppShell.Header>

      <AppShell.Main>
        {children}
      </AppShell.Main>
    </AppShell>
  );
}

import { Paper, Stack, Text, Button, Loader, Badge, Group, Card } from '@mantine/core';
import { IconBulb, IconFileText } from '@tabler/icons-react';
import { ApplicationEntry } from '../services/api';

interface ApplicationListProps {
  applications: ApplicationEntry[];
  loading: boolean;
  onSelectApplication: (application: ApplicationEntry) => void;
  selectedApplicationId: string | null;
}

export function ApplicationList({
  applications,
  loading,
  onSelectApplication,
  selectedApplicationId,
}: ApplicationListProps) {
  if (loading) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Loader size="lg" />
        <Text size="sm" c="dimmed">
          Loading applications...
        </Text>
      </Stack>
    );
  }

  if (applications.length === 0) {
    return (
      <Paper shadow="sm" p="xl" withBorder>
        <Stack align="center" gap="md">
          <IconBulb size={48} color="gray" />
          <div style={{ textAlign: 'center' }}>
            <Text size="lg" fw={600} mb="xs">
              No Applications Saved Yet
            </Text>
            <Text size="sm" c="dimmed">
              Add applications from the paper analysis view to see them here
            </Text>
          </div>
        </Stack>
      </Paper>
    );
  }

  return (
    <Stack gap="md">
      <div>
        <Text size="xl" fw={700} mb="xs">
          Saved Applications
        </Text>
        <Text size="sm" c="dimmed">
          {applications.length} application{applications.length !== 1 ? 's' : ''} saved
        </Text>
      </div>

      <Stack gap="sm">
        {applications.map((app) => (
          <Card
            key={app.id}
            shadow="sm"
            padding="lg"
            withBorder
            style={{
              cursor: 'pointer',
              borderColor: selectedApplicationId === app.id ? '#228be6' : undefined,
              borderWidth: selectedApplicationId === app.id ? 2 : 1,
            }}
            onClick={() => onSelectApplication(app)}
          >
            <Stack gap="xs">
              <Group justify="space-between" align="flex-start">
                <Badge
                  size="lg"
                  variant="filled"
                  color="cyan"
                  leftSection={<IconBulb size={14} />}
                >
                  {app.application.domain}
                </Badge>
                <Badge size="sm" variant="light" color="gray">
                  {new Date(app.added_at).toLocaleDateString()}
                </Badge>
              </Group>

              <Text size="sm" lineClamp={2}>
                {app.application.specific_utility}
              </Text>

              <Group gap="xs" mt="xs">
                <Badge
                  size="xs"
                  variant="outline"
                  leftSection={<IconFileText size={12} />}
                >
                  {app.current_paper.title.slice(0, 50)}
                  {app.current_paper.title.length > 50 ? '...' : ''}
                </Badge>
                {app.related_papers.length > 0 && (
                  <Badge size="xs" variant="light" color="blue">
                    {app.related_papers.length} related paper{app.related_papers.length !== 1 ? 's' : ''}
                  </Badge>
                )}
              </Group>

              <Button
                variant="light"
                size="xs"
                fullWidth
                mt="xs"
                onClick={(e) => {
                  e.stopPropagation();
                  onSelectApplication(app);
                }}
              >
                View Details
              </Button>
            </Stack>
          </Card>
        ))}
      </Stack>
    </Stack>
  );
}

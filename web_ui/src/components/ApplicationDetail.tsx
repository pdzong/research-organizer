import { Paper, Stack, Text, Button, Group, Badge, Divider, Card, Box } from '@mantine/core';
import { IconArrowLeft, IconBulb, IconFileText, IconCalendar, IconUsers, IconExternalLink } from '@tabler/icons-react';
import { ApplicationEntry } from '../services/api';

interface ApplicationDetailProps {
  application: ApplicationEntry;
  onBack: () => void;
}

export function ApplicationDetail({ application, onBack }: ApplicationDetailProps) {
  return (
    <Stack gap="md" h="100%">
      <Group>
        <Button
          leftSection={<IconArrowLeft size={16} />}
          variant="subtle"
          onClick={onBack}
        >
          Back to Applications
        </Button>
      </Group>

      {/* Application Header */}
      <Paper shadow="sm" p="lg" withBorder>
        <Stack gap="md">
          <Group justify="space-between" align="flex-start">
            <Badge
              size="xl"
              variant="filled"
              color="cyan"
              leftSection={<IconBulb size={18} />}
            >
              {application.application.domain}
            </Badge>
            <Badge
              size="sm"
              variant="light"
              color="gray"
              leftSection={<IconCalendar size={14} />}
            >
              Added {new Date(application.added_at).toLocaleDateString()}
            </Badge>
          </Group>

          <div>
            <Text size="sm" fw={600} c="dimmed" mb="xs">
              Application Description
            </Text>
            <Text size="md">
              {application.application.specific_utility}
            </Text>
          </div>
        </Stack>
      </Paper>

      {/* Source Paper */}
      <Paper shadow="sm" p="lg" withBorder>
        <Stack gap="md">
          <Group>
            <IconFileText size={20} color="#228be6" />
            <Text size="lg" fw={600}>
              Source Paper
            </Text>
          </Group>

          <Card withBorder bg="blue.0" style={{ borderLeft: '4px solid #228be6' }}>
            <Stack gap="xs">
              <Text size="md" fw={600}>
                {application.current_paper.title}
              </Text>
              
              {application.current_paper.authors && application.current_paper.authors.length > 0 && (
                <Group gap="xs">
                  <IconUsers size={14} color="gray" />
                  <Text size="sm" c="dimmed">
                    {application.current_paper.authors.join(', ')}
                  </Text>
                </Group>
              )}

              {application.current_paper.arxiv_id && (
                <Group gap="xs">
                  <Badge size="sm" variant="light" color="blue">
                    ArXiv: {application.current_paper.arxiv_id}
                  </Badge>
                  <Button
                    component="a"
                    href={`https://arxiv.org/abs/${application.current_paper.arxiv_id}`}
                    target="_blank"
                    size="xs"
                    variant="light"
                    rightSection={<IconExternalLink size={12} />}
                  >
                    View on ArXiv
                  </Button>
                </Group>
              )}
            </Stack>
          </Card>
        </Stack>
      </Paper>

      {/* Related Papers */}
      {application.related_papers && application.related_papers.length > 0 && (
        <Paper shadow="sm" p="lg" withBorder>
          <Stack gap="md">
            <Group justify="space-between">
              <Group>
                <IconFileText size={20} color="#228be6" />
                <Text size="lg" fw={600}>
                  Related Papers
                </Text>
              </Group>
              <Badge size="lg" variant="light" color="blue">
                {application.related_papers.length} paper{application.related_papers.length !== 1 ? 's' : ''}
              </Badge>
            </Group>

            <Stack gap="sm">
              {application.related_papers.map((paper, idx) => (
                <Card
                  key={idx}
                  withBorder
                  padding="md"
                  style={{ backgroundColor: '#f8f9fa' }}
                >
                  <Stack gap="xs">
                    <Text size="sm" fw={600}>
                      {idx + 1}. {paper.title}
                    </Text>

                    {paper.authors && paper.authors.length > 0 && (
                      <Group gap="xs">
                        <IconUsers size={12} color="gray" />
                        <Text size="xs" c="dimmed" lineClamp={1}>
                          {paper.authors.join(', ')}
                        </Text>
                      </Group>
                    )}

                    {paper.arxiv_id && (
                      <Group gap="xs">
                        <Badge size="xs" variant="outline" color="blue">
                          ArXiv: {paper.arxiv_id}
                        </Badge>
                        <Button
                          component="a"
                          href={`https://arxiv.org/abs/${paper.arxiv_id}`}
                          target="_blank"
                          size="xs"
                          variant="subtle"
                          rightSection={<IconExternalLink size={10} />}
                        >
                          View
                        </Button>
                      </Group>
                    )}
                  </Stack>
                </Card>
              ))}
            </Stack>
          </Stack>
        </Paper>
      )}

      {/* Metadata */}
      <Paper shadow="sm" p="md" withBorder bg="gray.0">
        <Group gap="xl">
          <div>
            <Text size="xs" c="dimmed" fw={600}>
              Application ID
            </Text>
            <Text size="xs" c="dimmed" style={{ fontFamily: 'monospace' }}>
              {application.id}
            </Text>
          </div>
          <Divider orientation="vertical" />
          <div>
            <Text size="xs" c="dimmed" fw={600}>
              Total Papers Referenced
            </Text>
            <Text size="xs" c="dimmed">
              {1 + application.related_papers.length} (1 source + {application.related_papers.length} related)
            </Text>
          </div>
        </Group>
      </Paper>
    </Stack>
  );
}

import { Paper, Stack, Text, Loader, Badge, Group, Card, Button } from '@mantine/core';
import { IconRocket, IconBulb, IconCalendar } from '@tabler/icons-react';
import { SolutionPlanRecord } from '../services/api';

interface SolutionListProps {
  solutions: SolutionPlanRecord[];
  loading: boolean;
  onSelectSolution: (record: SolutionPlanRecord) => void;
  selectedApplicationId: string | null;
}

export function SolutionList({
  solutions,
  loading,
  onSelectSolution,
  selectedApplicationId,
}: SolutionListProps) {
  if (loading) {
    return (
      <Stack align="center" justify="center" h={400}>
        <Loader size="lg" />
        <Text size="sm" c="dimmed">
          Loading solution plans...
        </Text>
      </Stack>
    );
  }

  if (solutions.length === 0) {
    return (
      <Paper shadow="sm" p="xl" withBorder>
        <Stack align="center" gap="md">
          <IconRocket size={48} color="gray" />
          <div style={{ textAlign: 'center' }}>
            <Text size="lg" fw={600} mb="xs">
              No System / Solution Plans Yet
            </Text>
            <Text size="sm" c="dimmed">
              Open an Application and click <b>Generate System Plan</b> to turn the
              underlying papers into a codegen-ready solution description.
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
          System / Solution Plans
        </Text>
        <Text size="sm" c="dimmed">
          {solutions.length} plan{solutions.length !== 1 ? 's' : ''} ready to feed into a code-gen LLM
        </Text>
      </div>

      <Stack gap="sm">
        {solutions.map((rec) => {
          const plan = rec.plan;
          const id = rec.application_id || '';
          const isSelected = id === selectedApplicationId;
          return (
            <Card
              key={id}
              shadow="sm"
              padding="lg"
              withBorder
              style={{
                cursor: 'pointer',
                borderColor: isSelected ? '#228be6' : undefined,
                borderWidth: isSelected ? 2 : 1,
              }}
              onClick={() => onSelectSolution(rec)}
            >
              <Stack gap="xs">
                <Group justify="space-between" align="flex-start">
                  <Group gap="xs">
                    <Badge
                      size="lg"
                      variant="filled"
                      color="grape"
                      leftSection={<IconRocket size={14} />}
                    >
                      {plan?.name || 'Untitled solution'}
                    </Badge>
                  </Group>
                  {rec.generated_at && (
                    <Badge
                      size="sm"
                      variant="light"
                      color="gray"
                      leftSection={<IconCalendar size={12} />}
                    >
                      {new Date(rec.generated_at).toLocaleDateString()}
                    </Badge>
                  )}
                </Group>

                {plan?.tagline && (
                  <Text size="sm" fs="italic" c="dimmed">
                    {plan.tagline}
                  </Text>
                )}

                <Text size="sm" lineClamp={2}>
                  {plan?.problem_statement}
                </Text>

                <Group gap="xs" mt="xs">
                  <Badge size="xs" variant="light" color="grape">
                    {plan?.modules?.length || 0} modules
                  </Badge>
                  <Badge size="xs" variant="light" color="blue">
                    {plan?.apis?.length || 0} APIs
                  </Badge>
                  <Badge size="xs" variant="light" color="teal">
                    {plan?.milestones?.length || 0} milestones
                  </Badge>
                  <Badge
                    size="xs"
                    variant="outline"
                    leftSection={<IconBulb size={12} />}
                  >
                    {plan?.key_enabling_papers?.length || 0} papers
                  </Badge>
                </Group>

                <Button
                  variant="light"
                  size="xs"
                  fullWidth
                  mt="xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    onSelectSolution(rec);
                  }}
                >
                  Open plan
                </Button>
              </Stack>
            </Card>
          );
        })}
      </Stack>
    </Stack>
  );
}

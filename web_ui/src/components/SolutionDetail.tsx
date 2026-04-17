import {
  Paper,
  Stack,
  Text,
  Button,
  Group,
  Badge,
  Card,
  Divider,
  Tabs,
  CopyButton,
  ActionIcon,
  Tooltip,
  Code,
  ScrollArea,
} from '@mantine/core';
import {
  IconArrowLeft,
  IconRocket,
  IconCopy,
  IconCheck,
  IconDownload,
  IconRefresh,
  IconFileText,
  IconCode,
  IconNetwork,
  IconBulb,
} from '@tabler/icons-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { SolutionPlanRecord } from '../services/api';

interface SolutionDetailProps {
  record: SolutionPlanRecord;
  onBack: () => void;
  onRegenerate?: () => void;
  regenerating?: boolean;
}

export function SolutionDetail({
  record,
  onBack,
  onRegenerate,
  regenerating,
}: SolutionDetailProps) {
  const plan = record.plan;
  const markdown = record.markdown || '';

  if (!plan) {
    return (
      <Stack gap="md">
        <Group>
          <Button leftSection={<IconArrowLeft size={16} />} variant="subtle" onClick={onBack}>
            Back
          </Button>
        </Group>
        <Paper shadow="sm" p="xl" withBorder>
          <Text c="dimmed">No plan data available.</Text>
        </Paper>
      </Stack>
    );
  }

  const downloadMarkdown = () => {
    const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    const safeName = (plan.name || 'solution-plan').replace(/[^a-zA-Z0-9-_]+/g, '-').toLowerCase();
    a.download = `${safeName}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <Button leftSection={<IconArrowLeft size={16} />} variant="subtle" onClick={onBack}>
          Back
        </Button>
        <Group gap="xs">
          {onRegenerate && (
            <Button
              leftSection={<IconRefresh size={14} />}
              variant="light"
              size="xs"
              loading={regenerating}
              onClick={onRegenerate}
            >
              Regenerate
            </Button>
          )}
          <Button
            leftSection={<IconDownload size={14} />}
            variant="light"
            size="xs"
            onClick={downloadMarkdown}
          >
            Download .md
          </Button>
          <CopyButton value={markdown} timeout={1500}>
            {({ copied, copy }) => (
              <Button
                leftSection={copied ? <IconCheck size={14} /> : <IconCopy size={14} />}
                variant={copied ? 'filled' : 'light'}
                color={copied ? 'teal' : 'blue'}
                size="xs"
                onClick={copy}
              >
                {copied ? 'Copied' : 'Copy markdown'}
              </Button>
            )}
          </CopyButton>
        </Group>
      </Group>

      {/* Header */}
      <Paper shadow="sm" p="lg" withBorder>
        <Stack gap="sm">
          <Group gap="xs">
            <IconRocket size={28} color="#9c36b5" />
            <div style={{ flex: 1 }}>
              <Text size="xl" fw={700}>
                {plan.name}
              </Text>
              {plan.tagline && (
                <Text size="sm" c="dimmed" fs="italic">
                  {plan.tagline}
                </Text>
              )}
            </div>
            {record.generated_at && (
              <Badge variant="light" color="gray">
                Generated {new Date(record.generated_at).toLocaleString()}
              </Badge>
            )}
          </Group>

          <Divider />

          <div>
            <Text size="sm" fw={600} c="dimmed" mb={4}>
              Problem
            </Text>
            <Text size="sm">{plan.problem_statement}</Text>
          </div>

          {plan.target_users?.length > 0 && (
            <Group gap="xs">
              {plan.target_users.map((u, i) => (
                <Badge key={i} variant="outline" color="blue" size="sm">
                  {u}
                </Badge>
              ))}
            </Group>
          )}
        </Stack>
      </Paper>

      <Tabs defaultValue="overview">
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconFileText size={14} />}>
            Overview
          </Tabs.Tab>
          <Tabs.Tab value="architecture" leftSection={<IconNetwork size={14} />}>
            Architecture
          </Tabs.Tab>
          <Tabs.Tab value="modules" leftSection={<IconCode size={14} />}>
            Modules & APIs
          </Tabs.Tab>
          <Tabs.Tab value="delivery" leftSection={<IconRocket size={14} />}>
            Delivery
          </Tabs.Tab>
          <Tabs.Tab value="prompt" leftSection={<IconBulb size={14} />}>
            Codegen prompt
          </Tabs.Tab>
          <Tabs.Tab value="markdown" leftSection={<IconFileText size={14} />}>
            Full markdown
          </Tabs.Tab>
        </Tabs.List>

        {/* OVERVIEW */}
        <Tabs.Panel value="overview" pt="md">
          <Stack gap="md">
            <Paper shadow="sm" p="lg" withBorder>
              <Text size="sm" fw={600} c="dimmed" mb="xs">
                System overview
              </Text>
              <Text size="sm" style={{ whiteSpace: 'pre-wrap' }}>
                {plan.system_overview}
              </Text>
            </Paper>

            <Paper shadow="sm" p="lg" withBorder>
              <Text size="sm" fw={600} c="dimmed" mb="xs">
                Scientific grounding
              </Text>
              <Text size="sm" style={{ whiteSpace: 'pre-wrap' }} mb="md">
                {plan.scientific_grounding}
              </Text>
              <Text size="xs" fw={600} c="dimmed" mb="xs">
                Key enabling papers
              </Text>
              <Stack gap={4}>
                {plan.key_enabling_papers?.map((p, i) => (
                  <Group key={i} gap="xs">
                    <Badge size="xs" variant="light" color="blue">
                      {i + 1}
                    </Badge>
                    <Text size="sm">{p}</Text>
                  </Group>
                ))}
              </Stack>
            </Paper>

            <Paper shadow="sm" p="lg" withBorder>
              <Text size="sm" fw={600} c="dimmed" mb="xs">
                Tech stack
              </Text>
              <Group gap="xs">
                {plan.tech_stack?.map((t, i) => (
                  <Badge key={i} variant="light" color="grape">
                    {t}
                  </Badge>
                ))}
              </Group>
            </Paper>

            <Paper shadow="sm" p="lg" withBorder>
              <Text size="sm" fw={600} c="dimmed" mb="xs">
                Success metrics
              </Text>
              <Stack gap={4}>
                {plan.success_metrics?.map((m, i) => (
                  <Text key={i} size="sm">• {m}</Text>
                ))}
              </Stack>
            </Paper>

            {plan.open_questions?.length > 0 && (
              <Paper shadow="sm" p="lg" withBorder bg="yellow.0">
                <Text size="sm" fw={600} c="dimmed" mb="xs">
                  Open questions
                </Text>
                <Stack gap={4}>
                  {plan.open_questions.map((q, i) => (
                    <Text key={i} size="sm">• {q}</Text>
                  ))}
                </Stack>
              </Paper>
            )}
          </Stack>
        </Tabs.Panel>

        {/* ARCHITECTURE */}
        <Tabs.Panel value="architecture" pt="md">
          <Paper shadow="sm" p="lg" withBorder>
            <Text size="sm" fw={600} c="dimmed" mb="xs">
              Architecture diagram
            </Text>
            <ScrollArea>
              <Code block style={{ fontSize: 12, whiteSpace: 'pre' }}>
                {plan.architecture_diagram}
              </Code>
            </ScrollArea>
          </Paper>

          {plan.integration_points?.length > 0 && (
            <Paper shadow="sm" p="lg" withBorder mt="md">
              <Text size="sm" fw={600} c="dimmed" mb="xs">
                Integration points
              </Text>
              <Stack gap={4}>
                {plan.integration_points.map((p, i) => (
                  <Text key={i} size="sm">• {p}</Text>
                ))}
              </Stack>
            </Paper>
          )}
        </Tabs.Panel>

        {/* MODULES & APIS */}
        <Tabs.Panel value="modules" pt="md">
          <Stack gap="md">
            <Paper shadow="sm" p="lg" withBorder>
              <Text size="sm" fw={600} c="dimmed" mb="md">
                Modules
              </Text>
              <Stack gap="sm">
                {plan.modules?.map((m, i) => (
                  <Card key={i} withBorder padding="md">
                    <Stack gap="xs">
                      <Group justify="space-between">
                        <Text fw={600}>{m.name}</Text>
                        <Group gap={4}>
                          {m.technologies?.map((t, ti) => (
                            <Badge key={ti} size="xs" variant="light">
                              {t}
                            </Badge>
                          ))}
                        </Group>
                      </Group>
                      <Text size="sm">{m.responsibility}</Text>
                      <Group gap="xl">
                        <div>
                          <Text size="xs" c="dimmed" fw={600}>
                            Inputs
                          </Text>
                          <Text size="xs">{m.inputs?.join(', ') || '—'}</Text>
                        </div>
                        <div>
                          <Text size="xs" c="dimmed" fw={600}>
                            Outputs
                          </Text>
                          <Text size="xs">{m.outputs?.join(', ') || '—'}</Text>
                        </div>
                      </Group>
                      {m.paper_grounding?.length > 0 && (
                        <Group gap={4}>
                          <Text size="xs" c="dimmed" fw={600}>
                            Grounded in:
                          </Text>
                          {m.paper_grounding.map((p, pi) => (
                            <Badge key={pi} size="xs" variant="outline" color="blue">
                              {p}
                            </Badge>
                          ))}
                        </Group>
                      )}
                    </Stack>
                  </Card>
                ))}
              </Stack>
            </Paper>

            {plan.data_models?.length > 0 && (
              <Paper shadow="sm" p="lg" withBorder>
                <Text size="sm" fw={600} c="dimmed" mb="md">
                  Data models
                </Text>
                <Stack gap="sm">
                  {plan.data_models.map((d, i) => (
                    <Card key={i} withBorder padding="md">
                      <Text fw={600} mb={4}>
                        {d.name}
                      </Text>
                      <Stack gap={2}>
                        {d.fields.map((f, fi) => (
                          <Text key={fi} size="xs" style={{ fontFamily: 'monospace' }}>
                            {f}
                          </Text>
                        ))}
                      </Stack>
                      {d.notes && (
                        <Text size="xs" c="dimmed" mt={4}>
                          {d.notes}
                        </Text>
                      )}
                    </Card>
                  ))}
                </Stack>
              </Paper>
            )}

            {plan.apis?.length > 0 && (
              <Paper shadow="sm" p="lg" withBorder>
                <Text size="sm" fw={600} c="dimmed" mb="md">
                  API surface
                </Text>
                <Stack gap="xs">
                  {plan.apis.map((a, i) => (
                    <Card key={i} withBorder padding="sm">
                      <Group gap="xs">
                        <Badge color="green" variant="filled">
                          {a.method}
                        </Badge>
                        <Code>{a.path}</Code>
                      </Group>
                      <Text size="sm" mt={4}>
                        {a.purpose}
                      </Text>
                      {a.request && (
                        <Text size="xs" c="dimmed" mt={2}>
                          <b>Request:</b> {a.request}
                        </Text>
                      )}
                      {a.response && (
                        <Text size="xs" c="dimmed">
                          <b>Response:</b> {a.response}
                        </Text>
                      )}
                    </Card>
                  ))}
                </Stack>
              </Paper>
            )}
          </Stack>
        </Tabs.Panel>

        {/* DELIVERY */}
        <Tabs.Panel value="delivery" pt="md">
          <Stack gap="md">
            <Paper shadow="sm" p="lg" withBorder>
              <Text size="sm" fw={600} c="dimmed" mb="md">
                Milestones
              </Text>
              <Stack gap="sm">
                {plan.milestones?.map((m, i) => (
                  <Card key={i} withBorder padding="md">
                    <Group justify="space-between">
                      <Text fw={600}>
                        {i + 1}. {m.title}
                      </Text>
                      {m.estimated_effort && (
                        <Badge variant="light" color="teal">
                          ≈ {m.estimated_effort}
                        </Badge>
                      )}
                    </Group>
                    <Stack gap={2} mt="xs">
                      {m.deliverables.map((d, di) => (
                        <Text key={di} size="sm">• {d}</Text>
                      ))}
                    </Stack>
                  </Card>
                ))}
              </Stack>
            </Paper>

            {plan.risks?.length > 0 && (
              <Paper shadow="sm" p="lg" withBorder bg="red.0">
                <Text size="sm" fw={600} c="dimmed" mb="md">
                  Risks
                </Text>
                <Stack gap="xs">
                  {plan.risks.map((r, i) => (
                    <div key={i}>
                      <Text size="sm" fw={600}>{r.description}</Text>
                      <Text size="xs" c="dimmed">Mitigation: {r.mitigation}</Text>
                    </div>
                  ))}
                </Stack>
              </Paper>
            )}
          </Stack>
        </Tabs.Panel>

        {/* CODEGEN PROMPT */}
        <Tabs.Panel value="prompt" pt="md">
          <Paper shadow="sm" p="lg" withBorder>
            <Group justify="space-between" mb="sm">
              <Text size="sm" fw={600} c="dimmed">
                Self-contained prompt for a code-generation LLM
              </Text>
              <CopyButton value={plan.code_generation_prompt} timeout={1500}>
                {({ copied, copy }) => (
                  <Tooltip label={copied ? 'Copied!' : 'Copy prompt'}>
                    <ActionIcon variant="light" onClick={copy}>
                      {copied ? <IconCheck size={16} /> : <IconCopy size={16} />}
                    </ActionIcon>
                  </Tooltip>
                )}
              </CopyButton>
            </Group>
            <Code block style={{ whiteSpace: 'pre-wrap', fontSize: 13 }}>
              {plan.code_generation_prompt}
            </Code>
          </Paper>
        </Tabs.Panel>

        {/* FULL MARKDOWN */}
        <Tabs.Panel value="markdown" pt="md">
          <Paper shadow="sm" p="lg" withBorder>
            <ScrollArea h={600}>
              <div className="markdown-body">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
              </div>
            </ScrollArea>
          </Paper>
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}

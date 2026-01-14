import { Paper, Stack, Text, Button, Loader, Alert, Group, Divider, ScrollArea, Table, Badge, Accordion, Card } from '@mantine/core';
import { IconAlertCircle, IconSparkles, IconFileText, IconArrowLeft, IconChartBar, IconBook, IconUsers, IconCalendar, IconQuote, IconWorld, IconFileDescription } from '@tabler/icons-react';
import ReactMarkdown from 'react-markdown';
import { Paper as PaperType, Analysis, PaperMetadata, CacheStatus } from '../services/api';

interface PaperDetailProps {
  paper: PaperType;
  markdown: string | null;
  summary: Analysis | null;
  metadata: PaperMetadata | null;
  cacheStatus: CacheStatus;
  loading: boolean;
  analyzing: boolean;
  loadingMetadata: boolean;
  error: string | null;
  onParse: (forceReload?: boolean) => void;
  onAnalyze: (forceReload?: boolean) => void;
  onReloadMetadata: () => void;
  onBack: () => void;
}

export function PaperDetail({
  paper,
  markdown,
  summary,
  metadata,
  cacheStatus,
  loading,
  analyzing,
  loadingMetadata,
  error,
  onParse,
  onAnalyze,
  onReloadMetadata,
  onBack,
}: PaperDetailProps) {
  return (
    <Stack gap="md" h="100%">
      <Group>
        <Button
          leftSection={<IconArrowLeft size={16} />}
          variant="subtle"
          onClick={onBack}
        >
          Back to List
        </Button>
      </Group>

      <Paper shadow="sm" p="lg" withBorder>
        <Stack gap="md">
          <div>
            <Text size="xl" fw={700}>
              {paper.title}
            </Text>
            <Text size="sm" c="dimmed" mt="xs">
              {paper.authors.join(', ')}
            </Text>
            {paper.arxiv_id && (
              <Text size="sm" c="blue" mt="xs">
                ArXiv ID: {paper.arxiv_id}
              </Text>
            )}
          </div>

          {!markdown && !loading && (
            <Button
              leftSection={<IconFileText size={16} />}
              onClick={() => onParse(false)}
              size="lg"
            >
              {cacheStatus.markdown ? 'Load Paper Content (Cached)' : 'Load Paper Content'}
            </Button>
          )}
          
          {markdown && !loading && (
            <Button
              leftSection={<IconFileText size={16} />}
              onClick={() => onParse(true)}
              size="sm"
              variant="light"
            >
              Reload Paper Content
            </Button>
          )}

          {loading && (
            <Group>
              <Loader size="sm" />
              <Text size="sm" c="dimmed">
                Downloading and parsing PDF...
              </Text>
            </Group>
          )}

          {error && (
            <Alert
              icon={<IconAlertCircle size={16} />}
              title="Error"
              color="red"
            >
              {error}
            </Alert>
          )}
        </Stack>
      </Paper>

      {/* Semantic Scholar Metadata */}
      {loadingMetadata && (
        <Paper shadow="sm" p="lg" withBorder>
          <Group>
            <Loader size="sm" />
            <Text size="sm" c="dimmed">
              Loading metadata from Semantic Scholar...
            </Text>
          </Group>
        </Paper>
      )}

      {metadata && metadata.success && (
        <Paper shadow="sm" p="lg" withBorder>
          <Group justify="space-between" mb="md">
            <Text size="lg" fw={600}>
              Paper Metadata
            </Text>
            <Button
              size="xs"
              variant="light"
              onClick={onReloadMetadata}
              loading={loadingMetadata}
              disabled={loadingMetadata}
            >
              {loadingMetadata ? 'Reloading...' : 'Reload'}
            </Button>
          </Group>
          <Accordion variant="separated">
            {/* Overview */}
            <Accordion.Item value="overview">
              <Accordion.Control icon={<IconBook size={20} />}>
                Overview & Citations
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  {metadata.tldr && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed">TL;DR</Text>
                      <Text size="sm">{metadata.tldr}</Text>
                    </div>
                  )}
                  {metadata.abstract && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed">Abstract</Text>
                      <Text size="sm">{metadata.abstract}</Text>
                    </div>
                  )}
                  <Group gap="md">
                    <Badge color="blue" leftSection={<IconQuote size={14} />}>
                      {metadata.citationCount} citations
                    </Badge>
                    <Badge color="green">
                      {metadata.influentialCitationCount} influential citations
                    </Badge>
                    <Badge color="gray">
                      {metadata.referenceCount} references
                    </Badge>
                  </Group>
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Publication Info */}
            <Accordion.Item value="publication">
              <Accordion.Control icon={<IconCalendar size={20} />}>
                Publication Information
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  {metadata.year && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed">Year</Text>
                      <Text size="sm">{metadata.year}</Text>
                    </div>
                  )}
                  {metadata.publicationDate && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed">Publication Date</Text>
                      <Text size="sm">{metadata.publicationDate}</Text>
                    </div>
                  )}
                  {metadata.venue && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed">Venue</Text>
                      <Text size="sm">{metadata.venue}</Text>
                    </div>
                  )}
                  {metadata.publicationVenue && metadata.publicationVenue.name && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed">Publication Venue</Text>
                      <Text size="sm">{metadata.publicationVenue.name}</Text>
                      {metadata.publicationVenue.type && (
                        <Badge size="xs" mt="xs">{metadata.publicationVenue.type}</Badge>
                      )}
                    </div>
                  )}
                  {metadata.journal && metadata.journal.name && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed">Journal</Text>
                      <Text size="sm">
                        {metadata.journal.name}
                        {metadata.journal.volume && ` Vol. ${metadata.journal.volume}`}
                        {metadata.journal.pages && `, pp. ${metadata.journal.pages}`}
                      </Text>
                    </div>
                  )}
                  {metadata.isOpenAccess && (
                    <Badge color="teal" leftSection={<IconWorld size={14} />}>
                      Open Access
                    </Badge>
                  )}
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>

            {/* Authors */}
            {metadata.authors && metadata.authors.length > 0 && (
              <Accordion.Item value="authors">
                <Accordion.Control icon={<IconUsers size={20} />}>
                  Authors ({metadata.authors.length})
                </Accordion.Control>
                <Accordion.Panel>
                  <Stack gap="xs">
                    {metadata.authors.map((author, idx) => (
                      <Group key={idx}>
                        {author.url ? (
                          <Text
                            size="sm"
                            component="a"
                            href={author.url}
                            target="_blank"
                            c="blue"
                            style={{ textDecoration: 'none' }}
                          >
                            {author.name}
                          </Text>
                        ) : (
                          <Text size="sm">{author.name}</Text>
                        )}
                      </Group>
                    ))}
                  </Stack>
                </Accordion.Panel>
              </Accordion.Item>
            )}

            {/* Fields of Study */}
            {(metadata.fieldsOfStudy?.length > 0 || metadata.s2FieldsOfStudy?.length > 0) && (
              <Accordion.Item value="fields">
                <Accordion.Control icon={<IconFileDescription size={20} />}>
                  Fields of Study
                </Accordion.Control>
                <Accordion.Panel>
                  <Stack gap="sm">
                    {metadata.fieldsOfStudy && metadata.fieldsOfStudy.length > 0 && (
                      <Group gap="xs">
                        {metadata.fieldsOfStudy.map((field, idx) => (
                          <Badge key={idx} variant="light">
                            {field}
                          </Badge>
                        ))}
                      </Group>
                    )}
                    {metadata.s2FieldsOfStudy && metadata.s2FieldsOfStudy.length > 0 && (
                      <div>
                        <Text size="sm" fw={600} c="dimmed" mb="xs">
                          Semantic Scholar Fields
                        </Text>
                        <Group gap="xs">
                          {metadata.s2FieldsOfStudy.map((field, idx) => (
                            <Badge key={idx} color="indigo" variant="light">
                              {field.category}
                            </Badge>
                          ))}
                        </Group>
                      </div>
                    )}
                  </Stack>
                </Accordion.Panel>
              </Accordion.Item>
            )}

            {/* External Links */}
            <Accordion.Item value="links">
              <Accordion.Control icon={<IconWorld size={20} />}>
                External Links
              </Accordion.Control>
              <Accordion.Panel>
                <Stack gap="sm">
                  {metadata.url && (
                    <Text
                      size="sm"
                      component="a"
                      href={metadata.url}
                      target="_blank"
                      c="blue"
                    >
                      View on Semantic Scholar →
                    </Text>
                  )}
                  {metadata.openAccessPdf && metadata.openAccessPdf.url && (
                    <Text
                      size="sm"
                      component="a"
                      href={metadata.openAccessPdf.url}
                      target="_blank"
                      c="blue"
                    >
                      Open Access PDF →
                    </Text>
                  )}
                  {metadata.externalIds && Object.keys(metadata.externalIds).length > 0 && (
                    <div>
                      <Text size="sm" fw={600} c="dimmed" mb="xs">
                        External IDs
                      </Text>
                      <Group gap="xs">
                        {Object.entries(metadata.externalIds).map(([key, value]) => (
                          <Badge key={key} size="sm" variant="outline">
                            {key}: {value}
                          </Badge>
                        ))}
                      </Group>
                    </div>
                  )}
                </Stack>
              </Accordion.Panel>
            </Accordion.Item>
          </Accordion>
        </Paper>
      )}

      {markdown && (
        <>
          <Paper shadow="sm" p="lg" withBorder>
            <Group justify="space-between" mb="md">
              <Text size="lg" fw={600}>
                Analysis
              </Text>
              <Group gap="xs">
                {!summary && (
                  <Button
                    leftSection={<IconSparkles size={16} />}
                    onClick={() => onAnalyze(false)}
                    loading={analyzing}
                    disabled={analyzing}
                  >
                    {analyzing ? 'Analyzing...' : (cacheStatus.analysis ? 'Load Analysis (Cached)' : 'Analyze Paper')}
                  </Button>
                )}
                {summary && (
                  <Button
                    leftSection={<IconSparkles size={16} />}
                    onClick={() => onAnalyze(true)}
                    loading={analyzing}
                    disabled={analyzing}
                    variant="light"
                    size="sm"
                  >
                    {analyzing ? 'Regenerating...' : 'Regenerate Analysis'}
                  </Button>
                )}
              </Group>
            </Group>

            {summary && (
              <Stack gap="md">
                <Paper p="md" withBorder bg="blue.0">
                  <Text size="sm" fw={600} mb="md" c="blue">
                    AI Analysis
                  </Text>
                  
                  <Stack gap="md">
                    <div>
                      <Text size="sm" fw={600} c="blue.9" mb="xs">
                        Main Contribution
                      </Text>
                      <Text size="sm">
                        {summary.summary.main_contribution}
                      </Text>
                    </div>

                    <div>
                      <Text size="sm" fw={600} c="blue.9" mb="xs">
                        Methodology
                      </Text>
                      <Text size="sm">
                        {summary.summary.methodology}
                      </Text>
                    </div>

                    <div>
                      <Text size="sm" fw={600} c="blue.9" mb="xs">
                        Key Results
                      </Text>
                      <Text size="sm">
                        {summary.summary.key_results}
                      </Text>
                    </div>

                    <div>
                      <Text size="sm" fw={600} c="blue.9" mb="xs">
                        Significance
                      </Text>
                      <Text size="sm">
                        {summary.summary.significance}
                      </Text>
                    </div>

                    <div>
                      <Text size="sm" fw={600} c="blue.9" mb="xs">
                        Limitations
                      </Text>
                      <Text size="sm">
                        {summary.summary.limitations}
                      </Text>
                    </div>
                  </Stack>
                </Paper>

                {summary.benchmarks && summary.benchmarks.length > 0 && (
                  <Paper p="md" withBorder bg="green.0">
                    <Group mb="md">
                      <IconChartBar size={20} color="green" />
                      <Text size="sm" fw={600} c="green.9">
                        Benchmarks ({summary.benchmarks.length})
                      </Text>
                    </Group>
                    
                    <Table striped highlightOnHover>
                      <Table.Thead>
                        <Table.Tr>
                          <Table.Th>Benchmark</Table.Th>
                          <Table.Th>Score</Table.Th>
                          <Table.Th>Metric</Table.Th>
                        </Table.Tr>
                      </Table.Thead>
                      <Table.Tbody>
                        {summary.benchmarks.map((benchmark, idx) => (
                          <Table.Tr key={idx}>
                            <Table.Td>
                              <Badge color="green" variant="light">
                                {benchmark.name}
                              </Badge>
                            </Table.Td>
                            <Table.Td>
                              <Text fw={600}>{benchmark.score}</Text>
                            </Table.Td>
                            <Table.Td>
                              <Text size="sm" c="dimmed">{benchmark.metric}</Text>
                            </Table.Td>
                          </Table.Tr>
                        ))}
                      </Table.Tbody>
                    </Table>
                  </Paper>
                )}
              </Stack>
            )}
          </Paper>

          <Divider my="sm" />

          <Paper shadow="sm" p="lg" withBorder style={{ flex: 1, overflow: 'hidden' }}>
            <Text size="lg" fw={600} mb="md">
              Paper Content
            </Text>
            <ScrollArea h={600}>
              <ReactMarkdown
                components={{
                  h1: ({ children }) => (
                    <Text size="xl" fw={700} mt="xl" mb="md">
                      {children}
                    </Text>
                  ),
                  h2: ({ children }) => (
                    <Text size="lg" fw={600} mt="lg" mb="sm">
                      {children}
                    </Text>
                  ),
                  h3: ({ children }) => (
                    <Text size="md" fw={600} mt="md" mb="sm">
                      {children}
                    </Text>
                  ),
                  p: ({ children }) => (
                    <Text size="sm" mb="md">
                      {children}
                    </Text>
                  ),
                  code: ({ children }) => (
                    <Paper p="xs" bg="gray.1" component="code" style={{ fontFamily: 'monospace' }}>
                      {children}
                    </Paper>
                  ),
                }}
              >
                {markdown}
              </ReactMarkdown>
            </ScrollArea>
          </Paper>
        </>
      )}
    </Stack>
  );
}

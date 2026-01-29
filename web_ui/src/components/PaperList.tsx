import { Card, Text, Group, Stack, Badge, Loader, Center, Button, TextInput, Modal } from '@mantine/core';
import { IconUsers, IconExternalLink, IconPlus } from '@tabler/icons-react';
import { useState } from 'react';
import { Paper } from '../services/api';

interface PaperListProps {
  papers: Paper[];
  loading: boolean;
  onSelectPaper: (paper: Paper) => void;
  onAddPaper: (arxivUrl: string) => Promise<void>;
  selectedPaperId: string | null;
}

export function PaperList({ papers, loading, onSelectPaper, onAddPaper, selectedPaperId }: PaperListProps) {
  const [modalOpened, setModalOpened] = useState(false);
  const [arxivUrl, setArxivUrl] = useState('');
  const [adding, setAdding] = useState(false);

  const handleAddPaper = async () => {
    if (!arxivUrl.trim()) return;
    
    try {
      setAdding(true);
      await onAddPaper(arxivUrl);
      setArxivUrl('');
      setModalOpened(false);
    } catch (error) {
      console.error('Error adding paper:', error);
    } finally {
      setAdding(false);
    }
  };

  if (loading) {
    return (
      <Center h={400}>
        <Stack align="center">
          <Loader size="lg" />
          <Text c="dimmed">Loading papers...</Text>
        </Stack>
      </Center>
    );
  }

  if (papers.length === 0) {
    return (
      <Center h={400}>
        <Text c="dimmed">No papers found</Text>
      </Center>
    );
  }

  return (
    <>
      <Stack gap="md">
        <Group justify="space-between">
          <Text size="xl" fw={700}>Research Papers ({papers.length})</Text>
          <Button
            leftSection={<IconPlus size={16} />}
            onClick={() => setModalOpened(true)}
          >
            Add Paper
          </Button>
        </Group>

        {papers.map((paper) => (
        <Card
          key={paper.id}
          shadow="sm"
          padding="lg"
          radius="md"
          withBorder
          style={{
            cursor: 'pointer',
            transition: 'transform 0.2s, box-shadow 0.2s',
            backgroundColor: selectedPaperId === paper.id ? '#f8f9fa' : 'white',
          }}
          onClick={() => onSelectPaper(paper)}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '';
          }}
        >
          <Stack gap="xs">
            <Text fw={600} size="lg">
              {paper.title}
            </Text>

            <Group gap="xs">
              <IconUsers size={16} />
              <Text size="sm" c="dimmed">
                {paper.authors.join(', ')}
              </Text>
            </Group>

            {paper.arxiv_id && (
              <Group gap="xs">
                <Badge color="blue" variant="light">
                  ArXiv: {paper.arxiv_id}
                </Badge>
                {paper.arxiv_url && (
                  <Button
                    component="a"
                    href={paper.arxiv_url}
                    target="_blank"
                    variant="subtle"
                    size="xs"
                    rightSection={<IconExternalLink size={14} />}
                    onClick={(e) => e.stopPropagation()}
                  >
                    View on ArXiv
                  </Button>
                )}
              </Group>
            )}
          </Stack>
        </Card>
      ))}
      </Stack>

      <Modal
        opened={modalOpened}
        onClose={() => setModalOpened(false)}
        title="Add New Paper"
      >
        <Stack gap="md">
          <TextInput
            label="ArXiv URL"
            placeholder="https://arxiv.org/abs/1706.03762"
            value={arxivUrl}
            onChange={(e) => setArxivUrl(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleAddPaper();
              }
            }}
          />
          <Group justify="flex-end">
            <Button variant="subtle" onClick={() => setModalOpened(false)}>
              Cancel
            </Button>
            <Button
              onClick={handleAddPaper}
              loading={adding}
              disabled={!arxivUrl.trim() || adding}
            >
              Add Paper
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}

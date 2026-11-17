# Connectors

Endpoints and setup commands were checked against each vendor's documentation
on 2026-11-17. Vendors change tool names and plans; if a connector fails,
check its docs link first.

## Summary

| Connector | Used for | Account and cost | In `.mcp.json` |
|---|---|---|---|
| alphaXiv | Find AI/ML papers, read them as text or AI reports, ask questions of a PDF, read a paper's GitHub code | Free alphaXiv account (OAuth); search and analysis count against an assistant quota | yes |
| Hugging Face | Paper search, models and datasets linked to papers, HF docs | Free HF account (OAuth) | yes |
| Asta (Ai2, Semantic Scholar graph) | Citations, references, citation counts, author search, full-text snippet search over about 12M papers | Works without a key; a free key raises rate limits | yes |
| Undermind | Exhaustive deep search on a precise, hard question; topic monitoring | Free plan with limits; Pro $16/month (academic) | yes |
| arXiv (`arxiv-mcp-server`, community) | Search arXiv, read LaTeX source one section at a time, BibTeX, topic watches | Free; needs `uv` installed | yes |
| Elicit | Tables comparing many papers, reports, scheduled research routines | Requires Elicit Pro or higher | no, optional |
| Emergent Mind skills | Trending arXiv papers by category, idea-based search, about 37K open problems from papers | Free account includes 50 API requests a month | no, installed as skills |
| Built-in web search and fetch | Blogs (Raschka, Grootendorst, Epoch AI), Hugging Face daily papers API | Included in Claude | built in |

## Claude Code (recommended)

The vault's `.mcp.json` registers the first five connectors for any Claude
Code session started inside `exploration/`. On first start, Claude Code asks
you to approve these project servers. Then authenticate the OAuth ones:

1. Start `claude` in `exploration/`, run `/mcp`.
2. For `alphaxiv`, `huggingface` and `undermind`, select the server and choose
   **Authenticate**. A browser window opens for each sign-in.
3. `asta` and `arxiv` need no sign-in.

`.claude/settings.json` pre-approves only read-only tools (alphaXiv search and
read tools, Hugging Face paper search, Asta, arXiv, web search and fetch).
Undermind deep searches, alphaXiv library edits, and all file edits still ask
for permission.

### Optional: Elicit

Only if you have Elicit Pro or higher:

```bash
claude mcp add --transport http elicit https://elicit.com/api/mcp
```

Then `/mcp`, select `elicit`, choose **Authenticate**.

### Optional: Asta API key

Request a free key from Ai2 (see the Asta docs), then replace the project
entry with a user-level one that sends the key:

```bash
claude mcp add --transport http asta https://asta-tools.allen.ai/mcp/v1 --header "x-api-key: YOUR_KEY"
```

### Emergent Mind skills

1. Create a free account at <https://www.emergentmind.com/skills>; the page
   shows your API key.
2. Paste the install prompt from that page into Claude Code. It saves two
   skills (`emergent-mind-papers`, `emergent-mind-open-problems`) into your
   skills directory and sets `EMERGENT_MIND_API_KEY`.
3. The skills tell the agent to ask before refetching once they are more than
   a month old. Say yes when that happens.

Never commit the key. It belongs in your environment, not in this repository.

### The arXiv server needs `uv`

Install `uv` once (<https://docs.astral.sh/uv/getting-started/installation/>).
`uvx arxiv-mcp-server` then downloads and runs the server from PyPI. Use the
PyPI package; an unrelated npm package has the same name. Papers it downloads
are stored in `~/.arxiv-mcp-server/papers`.

## Claude Desktop and claude.ai

If you use the chat apps instead of Claude Code, add connectors under
**Settings > Connectors > Add custom connector**:

| Name | URL | Notes |
|---|---|---|
| Hugging Face | `https://huggingface.co/mcp?login` | Also listed in the connector gallery |
| Asta | `https://asta-tools.allen.ai/mcp/v1` | |
| Undermind | `https://mcp.undermind.ai/mcp` | |
| Elicit | `https://elicit.com/api/mcp` | Pro plan or higher |
| alphaXiv | `https://api.alphaxiv.org/mcp/v1` | alphaXiv documents that browser-hosted clients (claude.ai in a browser) are not supported; use Claude Desktop or Claude Code |

The local arXiv server works only in Claude Desktop (through
`claude_desktop_config.json`) or Claude Code. Chat apps also cannot commit to
this repository, so card updates have to be copied back by hand; Claude Code
avoids that.

## Documentation links

- alphaXiv: <https://www.alphaxiv.org/docs/mcp>
- Hugging Face: <https://huggingface.co/docs/hub/en/agents-mcp>
- Undermind: <https://www.undermind.ai/mcp>
- Elicit: <https://support.elicit.com/en/articles/14757404-use-elicit-via-mcp-server>
- Emergent Mind: <https://www.emergentmind.com/skills>, API <https://www.emergentmind.com/docs/api>
- arXiv MCP server: <https://github.com/blazickjp/arxiv-mcp-server>
- Hugging Face daily papers API: `GET https://huggingface.co/api/daily_papers` with `date`, `week`, `month`, `sort=trending|publishedAt`, `limit`, `p`

# Exploration vault

A personal, growing map of research questions, kept in Git and maintained with
a Claude agent. Instead of one-off summaries, each question gets a concept
card that is examined with the same seven questions (scarce resource,
trade-off, boundary, lineage, measurement, adoption, combination) and written
in depth levels, from a one-line headline down to theorems and sources. A
weekly radar checks new papers against the cards' open questions, which is how
"new transformer"-class shifts should show up early.

This folder is independent of the Research Paper Analyzer app in the rest of
the repository. Its radar and card format are meant to feed the app's planned
technology-radar phase (`ROADMAP.md`, P4) later.

## Contents

| Path | What it is |
|---|---|
| `CLAUDE.md` | Agent instructions: the method, depth levels, evidence rules, tool order, file conventions |
| `CONNECTORS.md` | Every connector and MCP server, what it is for, cost, and setup |
| `.mcp.json` | Project MCP servers for Claude Code (alphaXiv, Hugging Face, Asta, Undermind, arXiv) |
| `.claude/settings.json` | Pre-approves read-only research tools |
| `.claude/skills/` | `/investigate`, `/deepen`, `/radar`, `/connect` |
| `templates/concept-card.md` | Card template |
| `cards/` | Concept cards; starts with `attention-efficiency.md` and three stubs |
| `INDEX.md` | All cards and all open questions |
| `radar/` | Weekly radar reports |

## Setup on a new machine

1. **Install prerequisites**
   - Git (on Windows, Git for Windows; Claude Code uses its Bash).
   - Claude Code. Native installer:
     - Windows PowerShell: `irm https://claude.ai/install.ps1 | iex`
     - macOS or Linux: `curl -fsSL https://claude.ai/install.sh | bash`
   - `uv`, for the arXiv MCP server:
     <https://docs.astral.sh/uv/getting-started/installation/>
2. **Clone the repository**

   ```bash
   git clone -b feat/exploration-vault https://github.com/pdzong/research-organizer.git research_agent
   cd research_agent/exploration
   ```

   After the branch is merged, clone `main` instead.
3. **Start Claude Code in this folder** and sign in with your Claude
   subscription:

   ```bash
   claude
   ```

   Starting inside `exploration/` matters: that is where Claude Code finds
   `CLAUDE.md`, `.mcp.json`, the settings and the skills.
4. **Approve and authenticate connectors.** Approve the project MCP servers
   when asked, then run `/mcp` and authenticate `alphaxiv`, `huggingface` and
   `undermind` (each opens a browser sign-in). Details and optional
   connectors (Elicit, Emergent Mind skills, Asta key) are in
   `CONNECTORS.md`.
5. **Check it works**: ask "List the connected MCP servers and the tools each
   one exposes." All five should appear.
6. **First real task**: run

   ```text
   /investigate attention-efficiency
   ```

   The seed card's paper citations were written from memory and are marked
   `Verified: no`; this run verifies them, fixes anything wrong and extends
   the card.

## Using it

- **When something catches your eye** (a paper, a trend, a question):
  `/investigate <question or URL>`. Read the L0 and L1 sections; stop there
  if that is enough.
- **When you have energy to go deeper**: `/deepen <card> L2` (then L3, L4).
  Each level ends with a couple of questions to check understanding.
- **Weekly, about 20 minutes**: `/radar`. Read the "Worth your attention"
  section and choose which suggested card updates to apply.
- **When two ideas seem related**: `/connect <card A> <card B>`.

Every session ends with a commit and push of `exploration/` only, so the vault
stays in sync across machines.

## Notes

- API keys (Emergent Mind, Asta, Hugging Face tokens) belong in your
  environment, never in this repository.
- The agent must label limits as proven, conditional, empirical,
  interpretation or speculation, and mark anything it could not verify. If a
  card makes a claim without a label or source, ask the agent to fix it.

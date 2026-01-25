# Atlas v0 Demo

## Setup

1. Make sure you run the script with Python 3.8+.
2. Initialize the workspace once before using it:
   ```bash
   python -m atlas init
   ```
  This creates `.atlas/{project,memory,arch}.json` with empty JSON. If you want the interactive repo scan, run:
   ```bash
   python -m atlas onboard
   ```

## Core commands

- `python -m atlas onboard` — scans the repo for key files (README, build files) and asks onboarding questions to seed `project.json`.
- `python -m atlas project --show` — prints the current goals, constraints, architecture summary, and coding conventions.
- `python -m atlas project --goal "..." --constraint "..." --architecture "..." --convention "..."` — append new guidance to the project registry. Repeat `--goal`/`--constraint` to add multiple entries.
- `python -m atlas memory list [--limit N]` — show the latest memory entries that Atlas can retrieve during prompt execution.
- `python -m atlas memory add --text "..." [--intent "..."] [--note "..."] [--tags tag1,tag2]` — insert a manual memory entry.
- `python -m atlas arch list` — review all architecture nodes and edges.
- `python -m atlas arch add-node --name "Payment Service" --type service --description "..."` — register new components.
- `python -m atlas arch add-edge --source "Payment Service" --target "Webhook Handler" --label "notifies"` — declare dependencies/data flow.
- `python -m atlas run --prompt "..." [--mode atlas|baseline] [--note "..."] [--tags ...]` — show the difference between a stateless Codex (`baseline`) and Atlas (`atlas`). The Atlas run automatically injects retrieved memory, architecture context, and runs the goal validator before persisting a new memory entry.
- `python -m atlas demo` — execute the scripted 10-minute demo (baseline → Atlas → memory recall) described in Part B. It seeds architecture nodes, performs the baseline/Atlas runs, and executes a follow-up question.

## Data files

- `.atlas/project.json` stores project goals, constraints, an architecture summary, and coding conventions. The CLI keeps this file in sync whenever you update guidance.
- `.atlas/memory.json` persists timestamped summaries of each Atlas interaction (prompt, response sketch, intent, tags, note, and the embedding used for retrieval).
- `.atlas/arch.json` keeps track of nodes (services, APIs, models) and edges (dependencies/data flow) for architecture awareness.

## How the demo fulfills the spec

1. **Persistent memory**: Each `atlas.py run --mode atlas` call writes a memory entry, and future prompts retrieve the most similar entries via cosine similarity on simple token embeddings.
2. **Intent tracking**: The script extracts the first clause of the prompt as the intent, stores it, and surfaces it in the generated response summary.
3. **Architecture awareness**: `arch.json` holds node/edge metadata; the `run` command prints the current graph when formatting the Atlas response and demonstrates how new nodes/edges can be added manually.
4. **Context retrieval**: Retrieved memory entries are explicitly listed in the response, showing how Atlas layers past decisions into new prompts.
5. **Goal validation**: After generating a response sketch, Atlas checks whether keywords from each project goal appear in the response and prints a pass/fail list.

## Next steps

1. Add real Codex/OpenAI calls inside `Atlas.generate_response` when you have credentials and want an actual code assistant.
2. Extend the vector store to use FAISS or another library by replacing `embed_text` with an API-backed embedding and plugging in the new similarity check.
3. Hook this CLI into a minimal web UI or terminal TUI to better match a live demo. Running `python -m atlas demo` is already a first draft of the scripted walkthrough.

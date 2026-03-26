# 🧠 Obsidian AI

An intelligent automation system that organizes your Obsidian vault using **LangGraph** and **OpenAI**. It watches your `Index/` inbox folder, analyzes new notes, and automatically classifies, formats, and integrates them into your knowledge system following the **Forever Notes** methodology.

---

## 🧩 Why Obsidian AI?

Manual organization is the primary reason most personal knowledge management systems fail. Obsidian AI was built to solve:

- **Organizational Fatigue**: Automatically follows the **Forever Notes** methodology so you don't have to worry about where things go or how to name them.
- **English-Only Consistency**: Enforces the methodology's rule that all permanent notes should be in English, providing translation or reformatting if needed.
- **Knowledge Fragmentation**: Instead of having 10 small notes on the same topic, the **Knowledge Integrator** automatically merges related thoughts into existing notes.
- **Discoverability**: Automatically maintains "Breadcrumbs" and "Hubs" (Maps of Content), ensuring every note is linked and easy to find.

---

## ⚡ How It Works

When you drop a new `.md` file into your `Index/` folder, the system automatically:

1. **Summarizes & extracts keywords** — Generates a summary and identifies key topics
2. **Scans for related notes** — Searches your vault for existing notes that share keywords
3. **Decides the action** — Determines whether to **CREATE** a new note or **MERGE** with an existing one
4. **Routes to the right folder** — Selects the appropriate `collections/` subfolder
5. **Moves the file** — Physically places the note in its destination
6. **Adds metadata** — Injects breadcrumbs navigation and tags following Forever Notes rules
7. **Indexes in the Hub** — Adds a `[[wikilink]]` to the corresponding Hub (Map of Content)

```
Index/new_note.md
      │
      ▼
┌─────────────────────────┐
│  Node 1: Summary &      │
│  Keywords (LLM)         │
└──────────┬──────────────┘
           ▼
┌─────────────────────────┐
│  Node 2: Semantic       │
│  Scanner (Keyword Match)│
└──────────┬──────────────┘
           ▼
┌─────────────────────────┐
│  Node 3: Knowledge      │
│  Integrator (LLM)       │
└──────────┬──────────────┘
           │
     ┌─────┴──────┐
     │            │
   CREATE       MERGE
     │            │
     ▼            │
┌──────────┐      │
│ Node 4:  │      │
│ Folder   │      │
│ Router   │      │
│ (LLM)    │      │
└────┬─────┘      │
     │            │
     ▼            ▼
┌─────────────────────────┐
│  Node 5: File System    │
│  Executor (System)      │
└──────────┬──────────────┘
           ▼
┌─────────────────────────┐
│  Node 6: Metadata       │
│  Architect (Rule-based) │
└──────────┬──────────────┘
           ▼
┌─────────────────────────┐
│  Node 7: Hub Indexer    │
│  (Rule-based)           │
└──────────┬──────────────┘
           ▼
         [END]
```

---

## 📁 Project Structure

```
obsidian-ai/
├── main.py                    # Entry point — starts the monitor
├── pyproject.toml             # Dependencies (uv)
├── .env                       # Environment variables
├── Forever Notes Overview.md  # The methodology manual
│
├── src/
│   ├── monitor.py             # Watchdog — watches Index/ for new files
│   ├── run_workflow.py        # Initializes state and runs the LangGraph
│   ├── graph.py               # All 7 nodes + graph definition
│   ├── state.py               # NoteState TypedDict + Pydantic models
│   │
│   ├── config/
│   │   └── config.py          # OBSIDIAN_VAULT_PATH, MODEL_NAME, etc.
│   │
│   └── utils/
│       ├── vault_explorer.py  # scan_vault, filter_content, scan_hubs
│       └── logger.py          # Logging configuration
│
└── logs/
    └── app.log                # Application logs
```

---

## 🚀 Setup

### Prerequisites

- Python 3.14+
- An Obsidian vault with the Forever Notes structure
- OpenAI API key

### Installation

```bash
# Clone the repo
git clone https://github.com/your-username/obsidian-ai.git
cd obsidian-ai

# Install dependencies with uv
uv sync

# Configure environment
cp .env.example .env
```

### Environment Variables

```env
OBSIDIAN_VAULT_PATH=/path/to/your/vault/Index
OPENAI_API_KEY=sk-your-api-key
```

### Run

```bash
uv run python main.py
```

The system will start watching your `Index/` folder. Drop any `.md` file there and watch it get automatically organized.

---

## 🏗️ Vault Structure (Forever Notes)

The system expects this structure in your Obsidian vault:

```
vault/
├── ✱ Home.md              # System center — links to all hubs
├── Index/                  # Inbox — drop new notes here
├── hubs/                   # Maps of Content (MOC)
│   ├── ✱ Python Hub.md
│   ├── ✱ Tech Hub.md
│   └── ...
├── collections/            # Organized notes
│   ├── Professional/
│   │   ├── Python/
│   │   ├── English/
│   │   └── ...
│   └── Projects/
│       └── ...
└── templates/
```

---

## 🔧 Tech Stack

| Technology | Purpose | Why? |
|---|---|---|
| **LangGraph** | Orchestration | Enables complex, stateful workflows with decision loops (like the Merge vs Create logic). |
| **OpenAI (gpt-4o-mini)** | Reasoning | Provides high-quality semantic analysis (summarization, routing) with extremely low latency and cost. |
| **Watchdog** | Monitoring | Allows for a frictionless experience by automating the workflow the moment you save a file. |
| **Pydantic** | Validation | Guarantees that the AI's output is structured and safe for filesystem operations. |
| **uv** | Environment | Modern, ultra-fast Python dependency management for a seamless developer experience. |

---

## 📌 Node Details

| Node | Type | Description |
|---|---|---|
| **1. Summary & Keywords** | LLM | Generates a summary and extracts keywords from the raw note |
| **2. Semantic Scanner** | Code | Searches the vault for notes sharing keywords |
| **3. Knowledge Integrator** | LLM | Decides CREATE or MERGE based on related notes |
| **4. Folder Router** | LLM | Chooses the destination folder in `collections/` |
| **5. File System Executor** | System | Moves files (CREATE) or merges content (MERGE) |
| **6. Metadata Architect** | Rule-based | Adds breadcrumbs, tags, and formats content via LLM |
| **7. Hub Indexer** | Rule-based | Adds a `[[wikilink]]` to the corresponding Hub file |

---

## 📝 License

MIT

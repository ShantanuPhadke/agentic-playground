#!/usr/bin/env python3
"""Simple Atlas v0 demo orchestrator following the provided spec."""

from __future__ import annotations

import argparse
import json
import math
import re
import textwrap
import uuid
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

DATA_DIR = Path(".atlas")
PROJECT_FILE = DATA_DIR / "project.json"
MEMORY_FILE = DATA_DIR / "memory.json"
ARCH_FILE = DATA_DIR / "arch.json"
README_FILES = ("README.md", "README.rst", "README.txt")
KEY_FILES = (
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Pipfile",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "Makefile",
    "Dockerfile",
    "docker-compose.yml",
    "tsconfig.json",
    ".python-version",
    ".nvmrc",
)

DEFAULT_PROJECT = {
    "goals": [
        "Build a payment-processing API that can safely ingest Stripe events.",
        "Keep architectural decisions visible across workflow steps.",
        "Validate output against stated goals before committing code."
    ],
    "constraints": [
        "Prefer Node.js async/await routines and RESTful services.",
        "Document decisions so future steps can recall context."
    ],
    "architecture_summary": "API Gateway routes to Payment Service, Webhook Handler, and Notification Service.",
    "coding_conventions": "CamelCase for functions, keep helpers under 30 lines."
}

DEFAULT_MEMORY: List[Dict] = []
DEFAULT_ARCH = {"nodes": [], "edges": []}


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default):
    if not path.exists() or path.stat().st_size == 0:
        return deepcopy(default)
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def tokenize(text: str) -> List[str]:
    return re.findall(r"[a-zA-Z]+", text.lower())


def embed_text(text: str) -> Dict[str, float]:
    tokens = tokenize(text)
    if not tokens:
        return {}
    counts = Counter(tokens)
    total = sum(counts.values())
    return {token: counts[token] / total for token in sorted(counts)}


def cosine_similarity(a: Dict[str, float], b: Dict[str, float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(a[key] * b.get(key, 0.0) for key in a)
    norm_a = math.sqrt(sum(value * value for value in a.values()))
    norm_b = math.sqrt(sum(value * value for value in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def summarize_text(text: str, width: int = 120) -> str:
    return textwrap.shorten(text.strip(), width=width, placeholder="...")


def find_repo_root(start: Path) -> Path:
    start = start.resolve()
    for parent in (start, *start.parents):
        if (parent / ".git").exists():
            return parent
    return start


def safe_read_text(path: Path, max_chars: int = 4000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")[:max_chars]
    except OSError:
        return ""


def load_repo_signals(repo_root: Path) -> Dict[str, str]:
    signals: Dict[str, str] = {}
    for name in README_FILES:
        readme_path = repo_root / name
        if readme_path.exists():
            signals[name] = safe_read_text(readme_path)
            break
    for name in KEY_FILES:
        path = repo_root / name
        if path.exists():
            signals[name] = safe_read_text(path)
    return signals


def extract_readme_summary(text: str) -> str:
    for line in text.splitlines():
        cleaned = line.strip()
        if cleaned:
            return cleaned
    return ""


def detect_project_name(signals: Dict[str, str], repo_root: Path) -> str:
    package_text = signals.get("package.json", "")
    if package_text:
        try:
            payload = json.loads(package_text)
            if isinstance(payload, dict):
                name = payload.get("name")
                if isinstance(name, str) and name.strip():
                    return name.strip()
        except json.JSONDecodeError:
            pass
    pyproject_text = signals.get("pyproject.toml", "")
    if pyproject_text:
        match = re.search(r'name\\s*=\\s*"([^"]+)"', pyproject_text)
        if match:
            return match.group(1).strip()
    return repo_root.name


def detect_stack(signals: Dict[str, str]) -> List[str]:
    stack = []
    combined = " ".join(signals.values()).lower()
    if "package.json" in signals:
        stack.append("Node.js")
    if "tsconfig.json" in signals or "typescript" in combined:
        stack.append("TypeScript")
    if any(name in signals for name in ("pyproject.toml", "requirements.txt", "Pipfile")):
        stack.append("Python")
    if "fastapi" in combined:
        stack.append("FastAPI")
    if "django" in combined:
        stack.append("Django")
    if "go.mod" in signals:
        stack.append("Go")
    if "Cargo.toml" in signals:
        stack.append("Rust")
    if any(name in signals for name in ("pom.xml", "build.gradle", "build.gradle.kts")):
        stack.append("Java")
    return list(dict.fromkeys(stack))


def infer_goals(project_name: str, summary: str) -> List[str]:
    if summary:
        return [summary if summary.endswith(".") else f"{summary}."]
    if project_name:
        return [f"Deliver core features for {project_name}."]
    return []


def infer_constraints(stack: List[str]) -> List[str]:
    if stack:
        return [f"Prefer {stack[0]} conventions."]
    return []


def infer_architecture(stack: List[str]) -> str:
    if "FastAPI" in stack:
        return "FastAPI service with REST endpoints."
    if "Django" in stack:
        return "Django service with REST endpoints."
    if "Node.js" in stack:
        return "Node.js service exposing REST endpoints."
    if "Go" in stack:
        return "Go service exposing REST endpoints."
    if "Rust" in stack:
        return "Rust service exposing REST endpoints."
    if "Java" in stack:
        return "Java service exposing REST endpoints."
    return ""


def infer_conventions(stack: List[str]) -> str:
    if "Python" in stack:
        return "snake_case functions, type hints preferred."
    if "Node.js" in stack or "TypeScript" in stack:
        return "camelCase functions, lint with eslint."
    if "Go" in stack:
        return "gofmt formatting, short functions."
    if "Rust" in stack:
        return "rustfmt formatting, clippy for linting."
    if "Java" in stack:
        return "camelCase methods, standard formatter."
    return ""


def prompt_text(question: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    response = input(f"{question}{suffix}: ").strip()
    return response or default


def prompt_list(question: str, default_items: Iterable[str]) -> List[str]:
    defaults = [item.strip() for item in default_items if item.strip()]
    suffix = f" [{', '.join(defaults)}]" if defaults else ""
    response = input(f"{question}{suffix}: ").strip()
    if response:
        return [item.strip() for item in response.split(",") if item.strip()]
    return defaults


def prompt_yes_no(question: str, default: bool = False) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    response = input(f"{question} {suffix}: ").strip().lower()
    if not response:
        return default
    return response.startswith("y")


def onboard_project(storage: "AtlasStorage") -> None:
    repo_root = find_repo_root(Path.cwd())
    signals = load_repo_signals(repo_root)
    readme_summary = extract_readme_summary(
        next((signals[name] for name in README_FILES if name in signals), "")
    )
    stack = detect_stack(signals)
    project_name = detect_project_name(signals, repo_root)

    existing = load_json(storage.project_file, {})
    existing_is_default = existing == DEFAULT_PROJECT
    if existing and not existing_is_default:
        if not prompt_yes_no("Project config already exists. Update it?", default=False):
            print("Onboarding canceled.")
            return
    if existing_is_default:
        if not prompt_yes_no("Project config matches demo defaults. Replace them?", default=True):
            print("Keeping existing project config.")
            return

    print("\nRepo scan summary:")
    print(f"- Repo root: {repo_root}")
    if project_name:
        print(f"- Project name: {project_name}")
    if stack:
        print(f"- Detected stack: {', '.join(stack)}")
    if readme_summary:
        print(f"- README summary: {summarize_text(readme_summary, width=100)}")
    print("\nAnswer a few questions to seed project.json. Press enter to accept defaults.\n")

    defaults = existing if (existing and not existing_is_default) else {}
    default_goals = defaults.get("goals") or infer_goals(project_name, readme_summary)
    default_constraints = defaults.get("constraints") or infer_constraints(stack)
    default_arch = defaults.get("architecture_summary") or infer_architecture(stack)
    default_conventions = defaults.get("coding_conventions") or infer_conventions(stack)

    goals = prompt_list("Project goals (comma-separated)", default_goals)
    constraints = prompt_list("Constraints (comma-separated)", default_constraints)
    architecture_summary = prompt_text("Architecture summary", default_arch)
    coding_conventions = prompt_text("Coding conventions", default_conventions)

    seeded = {
        "goals": goals,
        "constraints": constraints,
        "architecture_summary": architecture_summary,
        "coding_conventions": coding_conventions,
    }
    storage.persist_project(seeded)
    print(f"\nProject config saved to {storage.project_file}\n")


class AtlasStorage:
    def __init__(self, base_dir: Path = DATA_DIR):
        self.base_dir = base_dir
        self.project_file = self.base_dir / "project.json"
        self.memory_file = self.base_dir / "memory.json"
        self.arch_file = self.base_dir / "arch.json"

    def ensure_structure(self, seed_project: bool = False) -> None:
        ensure_dir(self.base_dir)
        if not self.project_file.exists():
            write_json(self.project_file, DEFAULT_PROJECT if seed_project else {})
        if not self.memory_file.exists():
            write_json(self.memory_file, [])
        if not self.arch_file.exists():
            write_json(self.arch_file, {})

    def load_project(self) -> Dict:
        return load_json(self.project_file, DEFAULT_PROJECT)

    def load_memory(self) -> List[Dict]:
        return load_json(self.memory_file, DEFAULT_MEMORY)

    def load_architecture(self) -> Dict:
        return load_json(self.arch_file, DEFAULT_ARCH)

    def persist_project(self, data: Dict) -> None:
        write_json(self.project_file, data)

    def persist_memory(self, data: List[Dict]) -> None:
        write_json(self.memory_file, data)

    def persist_architecture(self, data: Dict) -> None:
        write_json(self.arch_file, data)


class Atlas:
    """Minimal Atlas v0 layer that fulfills the spec from the PDF."""

    def __init__(self, storage: AtlasStorage):
        self.storage = storage
        self.storage.ensure_structure()
        self.reload()

    def reload(self) -> None:
        self.project = self.storage.load_project()
        self.memory = self.storage.load_memory()
        self.architecture = self.storage.load_architecture()

    def update_project(
        self,
        goals: Iterable[str] = (),
        constraints: Iterable[str] = (),
        architecture_summary: Optional[str] = None,
        coding_conventions: Optional[str] = None,
    ) -> None:
        changed = False
        if goals:
            self.project.setdefault("goals", [])
            self.project["goals"].extend([goal.strip() for goal in goals if goal.strip()])
            changed = True
        if constraints:
            self.project.setdefault("constraints", [])
            self.project["constraints"].extend(
                [constraint.strip() for constraint in constraints if constraint.strip()]
            )
            changed = True
        if architecture_summary:
            self.project["architecture_summary"] = architecture_summary.strip()
            changed = True
        if coding_conventions:
            self.project["coding_conventions"] = coding_conventions.strip()
            changed = True
        if changed:
            self.storage.persist_project(self.project)
            self.reload()

    def describe_project(self) -> str:
        lines = [
            "Project Goals:",
            *(f"- {goal}" for goal in self.project.get("goals", [])),
            "Constraints:",
            *(f"- {constraint}" for constraint in self.project.get("constraints", [])),
            "Architecture Summary:",
            f"- {self.project.get('architecture_summary', '')}",
            "Coding Conventions:",
            f"- {self.project.get('coding_conventions', '')}",
        ]
        return "\n".join(lines)

    def add_memory_entry(
        self,
        prompt: str,
        intent: str,
        response: str,
        mode: str,
        note: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        skip_save: bool = False,
    ) -> Dict:
        entry = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "prompt": prompt.strip(),
            "intent": intent.strip(),
            "summary": summarize_text(response),
            "response": response.strip(),
            "note": note.strip() if note else "",
            "tags": [tag.strip() for tag in tags or [] if tag.strip()],
            "mode": mode,
            "embedding": embed_text(f"{prompt} {response}"),
        }
        self.memory.append(entry)
        if not skip_save:
            self.storage.persist_memory(self.memory)
            self.reload()
        return entry

    def list_memory(self, limit: int = 20) -> List[Dict]:
        return self.memory[-limit:]

    def retrieve(self, intent: str, limit: int = 3) -> List[Dict]:
        needle = embed_text(intent)
        scored: List[Tuple[float, Dict]] = []
        for entry in self.memory:
            score = cosine_similarity(needle, entry.get("embedding", {}))
            scored.append((score, entry))
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [entry for score, entry in scored[:limit] if score > 0]

    def add_arch_node(self, name: str, node_type: str, description: str) -> None:
        nodes = self.architecture.setdefault("nodes", [])
        nodes.append({"name": name.strip(), "type": node_type.strip(), "description": description.strip()})
        self.storage.persist_architecture(self.architecture)
        self.reload()

    def add_arch_edge(self, source: str, target: str, label: str) -> None:
        edges = self.architecture.setdefault("edges", [])
        edges.append({"source": source.strip(), "target": target.strip(), "label": label.strip()})
        self.storage.persist_architecture(self.architecture)
        self.reload()

    def describe_architecture(self) -> str:
        lines = ["Architecture Nodes:"]
        for node in self.architecture.get("nodes", []):
            lines.append(f"- {node['name']} ({node['type']}): {node['description']}")
        if not self.architecture.get("nodes"):
            lines.append("- (no nodes registered yet)")
        lines.append("Architecture Edges:")
        for edge in self.architecture.get("edges", []):
            lines.append(f"- {edge['source']} -> {edge['target']} ({edge['label']})")
        if not self.architecture.get("edges"):
            lines.append("- (no edges registered yet)")
        return "\n".join(lines)

    def generate_response(
        self,
        prompt: str,
        intent: str,
        retrieved: List[Dict],
        architecture_summary: str,
        note: Optional[str],
        mode: str,
    ) -> str:
        parts = [
            f"Atlas mode: {mode}",
            f"Intent captured: {intent}",
            f"Prompt: {prompt}",
            "Suggested plan:",
        ]
        if retrieved:
            parts.append("- Recall from memory:")
            for entry in retrieved:
                parts.append(f"  · {entry['summary']} (intent: {entry['intent']})")
        else:
            parts.append("- No similar memory, starting fresh.")
        parts.append(f"- Architecture reminder: {architecture_summary}")
        if note:
            parts.append(f"- Engineer note: {note.strip()}")
        parts.append("- Outline implementation steps:")
        parts.extend(
            [
                "  1. Revisit previous decisions/conventions.",
                "  2. Update architecture graph if the request introduces new components.",
                "  3. Ensure code can be validated vs goals before finalizing.",
            ]
        )
        return "\n".join(parts)

    def goal_validation(self, response: str) -> Dict[str, bool]:
        tokens = set(tokenize(response))
        results = {}
        for goal in self.project.get("goals", []):
            goal_tokens = set(tokenize(goal))
            results[goal] = bool(tokens & goal_tokens)
        return results

    def run_prompt(
        self, prompt: str, mode: str = "atlas", note: Optional[str] = None, tags: Optional[Iterable[str]] = None
    ) -> None:
        prompt = prompt.strip()
        if not prompt:
            raise ValueError("Prompt cannot be empty.")
        intent = prompt.split(".")[0]
        retrieved = []
        print(f"\nRunning Atlas (mode={mode}) for prompt:\n{prompt}\n")
        if mode == "baseline":
            response = self.generate_response(prompt, intent, [], self.project.get("architecture_summary", ""), note, mode)
            print("Baseline Codex output (stateless) would look like:\n")
            print(response)
            print("\nBaseline notes: no memory or architecture was injected.\n")
            return
        retrieved = self.retrieve(intent)
        arch_context = self.describe_architecture()
        response = self.generate_response(prompt, intent, retrieved, arch_context, note, mode)
        print("Atlas-enhanced response:\n")
        print(response)
        print("\nGoal validation:")
        validation = self.goal_validation(response)
        satisfied = sum(1 for ok in validation.values() if ok)
        total = len(validation)
        if total:
            print(f"- Goals satisfied: {satisfied}/{total}")
            for goal, ok in validation.items():
                print(f"  [{'✔' if ok else '✖'}] {goal}")
        else:
            print("- No goals recorded yet.")
        self.add_memory_entry(prompt, intent, response, mode, note=note, tags=tags)


def demo_sequence(atlas: Atlas) -> None:
    print("\n=== Atlas v0 Demo Sequence ===")
    sample_prompt = (
        "We are building a payment processing service. Create a Node.js API with Stripe integration."
    )
    atlas.run_prompt(sample_prompt, mode="baseline")
    atlas.add_arch_node("API Gateway", "service", "Routes HTTP requests and enforces auth.")
    atlas.add_arch_node("Payment Service", "service", "Handles Stripe charges and retries.")
    atlas.add_arch_node("Webhook Handler", "service", "Processes Stripe webhook payloads.")
    atlas.add_arch_edge("API Gateway", "Payment Service", "routes to")
    atlas.add_arch_edge("Payment Service", "Webhook Handler", "notifies")
    atlas.run_prompt(sample_prompt, mode="atlas", note="Initial payment service setup", tags=["architecture"])
    followup = "Why did we choose async webhooks?"
    atlas.run_prompt(followup, mode="atlas", note="Clarify webhook decision", tags=["reasoning"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Atlas v0 demo orchestrator.")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("init", help="Initialize .atlas data directory with empty JSON files.")

    project_parser = subparsers.add_parser("project", help="Inspect or update project config.")
    project_parser.add_argument("--show", action="store_true", help="Print current project summary.")
    project_parser.add_argument("--goal", action="append", help="Add a project goal.")
    project_parser.add_argument("--constraint", action="append", help="Add a project constraint.")
    project_parser.add_argument("--architecture", help="Set a short architecture summary.")
    project_parser.add_argument("--convention", help="Set coding conventions.")

    memory_parser = subparsers.add_parser("memory", help="Work with Atlas memory.")
    memory_parser.add_argument("action", choices=["list", "add"], help="Action to perform.")
    memory_parser.add_argument("--text", help="Text describing the memory entry.")
    memory_parser.add_argument("--intent", help="Explicit intent for the memory.")
    memory_parser.add_argument("--note", help="Optional note/journal.")
    memory_parser.add_argument("--tags", help="Comma-separated tags.")
    memory_parser.add_argument("--limit", type=int, default=10, help="Limit number of memories shown.")

    arch_parser = subparsers.add_parser("arch", help="Inspect or modify architecture graph.")
    arch_parser.add_argument("action", choices=["list", "add-node", "add-edge"], help="Graph operation.")
    arch_parser.add_argument("--name", help="Node name.")
    arch_parser.add_argument("--type", help="Node type or role.")
    arch_parser.add_argument("--description", help="Node description.")
    arch_parser.add_argument("--source", help="Edge source node.")
    arch_parser.add_argument("--target", help="Edge target node.")
    arch_parser.add_argument("--label", help="Edge label describing relationship.")

    run_parser = subparsers.add_parser("run", help="Run a prompt through Atlas.")
    run_parser.add_argument("--prompt", required=True, help="User engineering prompt.")
    run_parser.add_argument("--mode", choices=["atlas", "baseline"], default="atlas", help="Mode to execute.")
    run_parser.add_argument("--note", help="Short note for memory.")
    run_parser.add_argument("--tags", help="Comma-separated tags for the memory entry.")

    subparsers.add_parser("onboard", help="Scan repo and seed project.json with prompts.")
    subparsers.add_parser("demo", help="Run the scripted demo sequence.")
    subparsers.add_parser("show", help="Show current project, memory, and architecture summaries.")

    args = parser.parse_args()
    if args.command == "init":
        storage = AtlasStorage()
        storage.ensure_structure(seed_project=False)
        print(f"Initialized atlas data in {storage.base_dir.resolve()}")
        return
    if args.command == "onboard":
        storage = AtlasStorage()
        storage.ensure_structure(seed_project=False)
        onboard_project(storage)
        return

    storage = AtlasStorage()
    atlas = Atlas(storage)

    if args.command == "project":
        if args.show or not any((args.goal, args.constraint, args.architecture, args.convention)):
            print(atlas.describe_project())
        if any((args.goal, args.constraint, args.architecture, args.convention)):
            atlas.update_project(
                goals=args.goal or (),
                constraints=args.constraint or (),
                architecture_summary=args.architecture,
                coding_conventions=args.convention,
            )
            print("Project updated.")
        return

    if args.command == "memory":
        if args.action == "list":
            for entry in atlas.list_memory(limit=args.limit):
                print(f"- [{entry['timestamp']}] intent={entry['intent']} tags={entry['tags']} summary={entry['summary']}")
            if not atlas.memory:
                print("No memory entries yet.")
        elif args.action == "add":
            if not args.text:
                raise SystemExit("Provide --text when adding memory.")
            tags = [tag.strip() for tag in (args.tags or "").split(",") if tag.strip()]
            intent = args.intent or args.text.split()[0]
            atlas.add_memory_entry(args.text, intent, args.text, mode="manual", note=args.note, tags=tags)
            print("Memory entry added.")
        return

    if args.command == "arch":
        if args.action == "list":
            print(atlas.describe_architecture())
        elif args.action == "add-node":
            if not all((args.name, args.type, args.description)):
                raise SystemExit("add-node requires --name, --type, and --description.")
            atlas.add_arch_node(args.name, args.type, args.description)
            print("Node added.")
        elif args.action == "add-edge":
            if not all((args.source, args.target, args.label)):
                raise SystemExit("add-edge requires --source, --target, and --label.")
            atlas.add_arch_edge(args.source, args.target, args.label)
            print("Edge added.")
        return

    if args.command == "run":
        tags = [tag.strip() for tag in (args.tags or "").split(",") if tag.strip()]
        atlas.run_prompt(prompt=args.prompt, mode=args.mode, note=args.note, tags=tags)
        return

    if args.command == "demo":
        demo_sequence(atlas)
        return
    if args.command == "show":
        print(atlas.describe_project())
        print("\nMemory entries:", len(atlas.memory))
        print("\n" + atlas.describe_architecture())
        return

    parser.print_help()


if __name__ == "__main__":
    main()

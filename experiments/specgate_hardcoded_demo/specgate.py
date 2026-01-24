import json
import os
import sys
import time
from datetime import datetime

REGISTRY_PATH = ".specgate/registry.json"
TOKENS_PATH = "design-tokens.json"
ARTIFACTS_DIR = "artifacts"

def load_json(path: str):
    with open(path, "r") as f:
        return json.load(f)

def classify_prompt(prompt: str) -> dict:
    p = prompt.lower()
    signals = {
        "payments": any(k in p for k in ["payment", "pay", "checkout", "card", "billing", "stripe"]),
        "ui": any(k in p for k in ["button", "ui", "page", "screen", "component"])
    }
    domain = "payments" if signals["payments"] else "general"
    return {"domain": domain, "signals": signals}

def registry_match(registry: dict, domain: str) -> dict:
    services = [s for s in registry.get("services", []) if s.get("type") == domain]
    preferred = next((s for s in services if s.get("status") == "preferred"), None)
    legacy = next((s for s in services if s.get("status") == "legacy"), None)
    return {"services": services, "preferred": preferred, "legacy": legacy}

def ask_clarifying_question(match: dict) -> dict:
    # For demo: only ask if both preferred & legacy exist
    pref = match.get("preferred")
    leg = match.get("legacy")
    if pref and leg:
        print("\nSpecGate Clarification:")
        print(f"I see this involves payments. Should I use the legacy '{leg['name']}' API or the preferred '{pref['name']}' wrapper?")
        print("1) Legacy (Pay-Old)  2) Preferred (Pay-Secure)")
        choice = input("Select 1 or 2: ").strip()
        return {"choice": "legacy" if choice == "1" else "preferred"}
    return {"choice": "preferred"}

def build_manifest(prompt: str, registry: dict, match: dict, decision: dict) -> dict:
    chosen = match["legacy"] if decision["choice"] == "legacy" else match["preferred"]
    policies = registry.get("policies", [])
    ui_constraints = registry.get("ui", {}).get("constraints", {})

    manifest = {
        "specgate_version": "0.1",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "input_prompt": prompt,
        "routing": {
            "domain": "payments",
            "chosen_service": chosen["name"],
            "service_version": chosen["version"]
        },
        "constraints": {
            "auth": chosen["constraints"].get("requiredAuth"),
            "pci": chosen["constraints"].get("pci"),
            "auditLogging": chosen["constraints"].get("auditLogging", False),
            "ui": {
                "design_tokens_file": registry.get("ui", {}).get("designTokensFile"),
                "buttonsUseTokens": ui_constraints.get("buttonsUseTokens", True),
                "noInlineHexColors": ui_constraints.get("noInlineHexColors", True)
            }
        },
        "policy_checks": [
            {"id": p["id"], "rule": p["rule"], "status": "enforced"} for p in policies
        ],
        "files": [
            {
                "path": "app/Checkout.tsx",
                "change_type": "modify",
                "intent": "Add a payment button that uses design tokens and routes through chosen payments service."
            },
            {
                "path": "app/paymentsClient.ts",
                "change_type": "create",
                "intent": f"Client wrapper for {chosen['name']} with required auth and audit logging hooks."
            }
        ],
        "acceptance_criteria": [
            "Payment button uses design tokens (no inline hex colors).",
            f"Payments flow uses {chosen['name']} ({chosen['version']}).",
            "No PII stored in logs.",
            "All changes limited to files listed in manifest.",
            "Button uses design tokens",
            # Example lint check below
            "No inline hex colors"
        ],
        "handoff_to_coding_agent": {
            "instruction": "Generate or modify ONLY the files listed. Follow constraints and acceptance criteria exactly."
        }
    }
    return manifest

def print_baseline_fail(prompt: str):
    # Demo-only: show what a naive LLM might do
    print("\n--- Baseline (No SpecGate) ---")
    print(f"User prompt: {prompt}")
    print("Naive output risk: picks random payments API, misses auth/policy constraints, uses inline styles.\n")

def main():
    if len(sys.argv) < 2:
        print("Usage: python specgate.py \"<prompt>\"")
        sys.exit(1)

    prompt = sys.argv[1]

    os.makedirs(ARTIFACTS_DIR, exist_ok=True)

    print_baseline_fail(prompt)

    print("--- SpecGate v0 ---")
    print("Loading registry...")
    registry = load_json(REGISTRY_PATH)
    time.sleep(0.4)

    cls = classify_prompt(prompt)
    print(f"Detected domain: {cls['domain']}")
    time.sleep(0.3)

    match = registry_match(registry, cls["domain"])
    if not match["services"]:
        print("No matching services found. Exiting.")
        sys.exit(1)

    print("Registry match:")
    for s in match["services"]:
        print(f" - {s['name']} ({s['status']}, {s['version']})")
    time.sleep(0.3)

    decision = ask_clarifying_question(match)

    manifest = build_manifest(prompt, registry, match, decision)

    out_path = os.path.join(ARTIFACTS_DIR, "spec_manifest.json")
    with open(out_path, "w") as f:
        json.dump(manifest, f, indent=2)

    print("\n--- Signed-Off Spec (Manifest) ---")
    print(json.dumps(manifest, indent=2))

    print(f"\nSaved: {out_path}")

    print("\n--- Handoff ---")
    print("Copy/paste the manifest into Codex with this instruction:")
    print("“Use the JSON manifest as the contract. Generate code changes that satisfy it. Only touch listed files.”")

if __name__ == "__main__":
    main()

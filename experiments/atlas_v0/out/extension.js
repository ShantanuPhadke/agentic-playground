"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = activate;
exports.deactivate = deactivate;
const vscode = __importStar(require("vscode"));
const child_process_1 = require("child_process");
const path = __importStar(require("path"));
const fs = __importStar(require("fs"));
function runPython(workspacePath, args) {
    return new Promise((resolve, reject) => {
        const py = (0, child_process_1.spawn)("python", ["-m", "atlas", ...args], {
            cwd: workspacePath,
            env: { ...process.env }
        });
        let stdout = "";
        let stderr = "";
        py.stdout.on("data", (d) => (stdout += d.toString()));
        py.stderr.on("data", (d) => (stderr += d.toString()));
        py.on("error", (err) => reject(err));
        py.on("close", (code) => {
            if (code === 0) {
                resolve({ stdout, stderr });
                return;
            }
            reject(new Error(stderr || `atlas exited with code ${code}`));
        });
    });
}
function readAtlasFile(workspacePath, rel, fallback = "") {
    const filePath = path.join(workspacePath, rel);
    if (!fs.existsSync(filePath))
        return fallback;
    return fs.readFileSync(filePath, "utf8");
}
function parseJson(raw) {
    if (!raw.trim())
        return undefined;
    try {
        return JSON.parse(raw);
    }
    catch {
        return undefined;
    }
}
function getAtlasCounts(workspacePath) {
    const memoryRaw = readAtlasFile(workspacePath, ".atlas/memory.json");
    const archRaw = readAtlasFile(workspacePath, ".atlas/arch.json");
    const memoryData = parseJson(memoryRaw);
    const archData = parseJson(archRaw);
    const memory = Array.isArray(memoryData) ? memoryData.length : 0;
    const archNodes = archData && typeof archData === "object" && Array.isArray(archData.nodes)
        ? archData.nodes.length
        : 0;
    const archEdges = archData && typeof archData === "object" && Array.isArray(archData.edges)
        ? archData.edges.length
        : 0;
    return { memory, archNodes, archEdges };
}
function formatDelta(delta) {
    if (delta > 0)
        return `+${delta}`;
    if (delta < 0)
        return `${delta}`;
    return "0";
}
function writeLastRunSummary(workspacePath, prompt, stdout, before, after) {
    const timestamp = new Date().toISOString();
    const lines = [
        "# Atlas run",
        "",
        `Prompt: ${prompt}`,
        `Timestamp: ${timestamp}`,
        "",
        "## Diff summary",
        `- Memory entries: ${before.memory} -> ${after.memory} (${formatDelta(after.memory - before.memory)})`,
        `- Architecture nodes: ${before.archNodes} -> ${after.archNodes} (${formatDelta(after.archNodes - before.archNodes)})`,
        `- Architecture edges: ${before.archEdges} -> ${after.archEdges} (${formatDelta(after.archEdges - before.archEdges)})`,
        "",
        "## Atlas output",
        "```",
        stdout.trim() ? stdout.trim() : "(no stdout)",
        "```"
    ];
    const atlasDir = path.join(workspacePath, ".atlas");
    fs.mkdirSync(atlasDir, { recursive: true });
    fs.writeFileSync(path.join(atlasDir, "last_run.md"), lines.join("\n"), "utf8");
}
function escapeHtml(s) {
    return s
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}
function getNonce() {
    const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let text = "";
    for (let i = 0; i < 32; i += 1) {
        text += possible.charAt(Math.floor(Math.random() * possible.length));
    }
    return text;
}
function renderWebview(panel, workspacePath, lastPrompt) {
    const memory = readAtlasFile(workspacePath, ".atlas/memory.json", "[]");
    const arch = readAtlasFile(workspacePath, ".atlas/arch.json", "{}");
    const summary = readAtlasFile(workspacePath, ".atlas/last_run.md", "Run Atlas to generate last_run.md.");
    const nonce = getNonce();
    panel.webview.html = `<!DOCTYPE html>
  <html lang="en">
    <head>
      <meta charset="UTF-8" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta
        http-equiv="Content-Security-Policy"
        content="default-src 'none'; style-src 'unsafe-inline'; script-src 'nonce-${nonce}';"
      />
      <title>Atlas Demo</title>
      <style>
        :root {
          --bg-0: #f9f3e7;
          --bg-1: #e7f2ef;
          --bg-2: #f4e1c5;
          --ink: #1d2420;
          --muted: #5b6a60;
          --panel: #fffaf1;
          --panel-2: #f7efe2;
          --border: #d7cbbb;
          --accent: #ef7c3b;
          --accent-2: #0f8b8d;
          --shadow: rgba(18, 28, 22, 0.18);
          --code-bg: #111715;
          --code-ink: #e9f0ea;
        }

        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          font-family: "Space Grotesk", "Avenir Next", "Gill Sans", "Trebuchet MS", sans-serif;
          color: var(--ink);
          background: linear-gradient(135deg, var(--bg-0), var(--bg-1) 55%, var(--bg-2));
          min-height: 100vh;
        }

        body::before {
          content: "";
          position: fixed;
          inset: 0;
          background:
            radial-gradient(circle at 12% 18%, rgba(239, 124, 59, 0.15), transparent 45%),
            radial-gradient(circle at 88% 10%, rgba(15, 139, 141, 0.12), transparent 45%),
            repeating-linear-gradient(120deg, rgba(29, 36, 32, 0.05) 0 1px, transparent 1px 12px);
          pointer-events: none;
        }

        .page {
          position: relative;
          padding: 20px 24px 28px;
        }

        header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          margin-bottom: 16px;
        }

        .title {
          font-size: 22px;
          letter-spacing: 0.5px;
          text-transform: uppercase;
        }

        .subtitle {
          color: var(--muted);
          font-size: 13px;
        }

        .grid {
          display: grid;
          grid-template-columns: minmax(220px, 1fr) minmax(220px, 1.4fr) minmax(220px, 1.4fr);
          grid-template-rows: auto auto;
          gap: 14px;
        }

        .card {
          background: linear-gradient(160deg, var(--panel), var(--panel-2));
          border: 1px solid var(--border);
          border-radius: 18px;
          box-shadow: 0 12px 30px var(--shadow);
          padding: 16px;
          display: flex;
          flex-direction: column;
          min-height: 180px;
          animation: rise 0.6s ease both;
        }

        .card h3 {
          margin: 0 0 10px;
          font-size: 14px;
          text-transform: uppercase;
          letter-spacing: 1.2px;
          color: var(--muted);
        }

        .card--prompt {
          animation-delay: 0.05s;
        }

        .card--memory {
          animation-delay: 0.12s;
        }

        .card--arch {
          animation-delay: 0.18s;
        }

        .card--summary {
          grid-column: 1 / -1;
          min-height: 150px;
          animation-delay: 0.24s;
        }

        textarea {
          width: 100%;
          min-height: 160px;
          border-radius: 12px;
          border: 1px solid var(--border);
          padding: 12px;
          font-family: "IBM Plex Mono", "SF Mono", "Menlo", monospace;
          font-size: 12px;
          background: #ffffff;
          color: var(--ink);
          resize: vertical;
        }

        button {
          margin-top: 12px;
          border: none;
          border-radius: 999px;
          padding: 10px 16px;
          font-size: 13px;
          font-weight: 600;
          text-transform: uppercase;
          letter-spacing: 1px;
          color: #ffffff;
          background: linear-gradient(120deg, var(--accent), #ffb072);
          cursor: pointer;
          box-shadow: 0 8px 16px rgba(239, 124, 59, 0.35);
          transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        button:hover {
          transform: translateY(-1px);
          box-shadow: 0 10px 18px rgba(239, 124, 59, 0.45);
        }

        .pill {
          display: inline-flex;
          align-items: center;
          gap: 6px;
          padding: 6px 10px;
          border-radius: 999px;
          background: rgba(15, 139, 141, 0.12);
          color: var(--muted);
          font-size: 11px;
          margin-top: 8px;
        }

        pre {
          flex: 1;
          background: var(--code-bg);
          color: var(--code-ink);
          border-radius: 12px;
          padding: 12px;
          margin: 0;
          overflow: auto;
          font-size: 11px;
          line-height: 1.5;
          font-family: "IBM Plex Mono", "SF Mono", "Menlo", monospace;
        }

        @keyframes rise {
          from {
            opacity: 0;
            transform: translateY(12px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @media (max-width: 980px) {
          .grid {
            grid-template-columns: 1fr;
          }
          .card--summary {
            grid-column: 1;
          }
        }
      </style>
    </head>
    <body>
      <div class="page">
        <header>
          <div>
            <div class="title">Atlas Intelligence Console</div>
            <div class="subtitle">Run your prompt and inspect persistent artifacts.</div>
          </div>
          <div class="pill">Workspace: .atlas</div>
        </header>
        <section class="grid">
          <div class="card card--prompt">
            <h3>Prompt</h3>
            <textarea id="promptInput" placeholder="Describe the engineering task...">${escapeHtml(lastPrompt)}</textarea>
            <button id="runBtn">Run Atlas</button>
            <div class="pill" id="status">Ready for execution</div>
          </div>
          <div class="card card--memory">
            <h3>memory.json</h3>
            <pre>${escapeHtml(memory)}</pre>
          </div>
          <div class="card card--arch">
            <h3>arch.json</h3>
            <pre>${escapeHtml(arch)}</pre>
          </div>
          <div class="card card--summary">
            <h3>last_run.md</h3>
            <pre>${escapeHtml(summary)}</pre>
          </div>
        </section>
      </div>
      <script nonce="${nonce}">
        const vscode = acquireVsCodeApi();
        const runBtn = document.getElementById("runBtn");
        const promptInput = document.getElementById("promptInput");
        const status = document.getElementById("status");

        function setStatus(text) {
          if (status) {
            status.textContent = text;
          }
        }

        function runPrompt() {
          const prompt = promptInput.value.trim();
          if (!prompt) {
            setStatus("Enter a prompt to run.");
            return;
          }
          setStatus("Running Atlas...");
          vscode.postMessage({ type: "runPrompt", prompt });
        }

        runBtn.addEventListener("click", runPrompt);
        promptInput.addEventListener("keydown", (event) => {
          if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
            runPrompt();
          }
        });
      </script>
    </body>
  </html>`;
}
function activate(context) {
    const getWorkspacePath = () => {
        const ws = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
        if (!ws)
            throw new Error("Open a folder/workspace first.");
        return ws;
    };
    let panel;
    let lastPrompt = "";
    const ensurePanel = (workspacePath) => {
        if (panel) {
            panel.reveal(vscode.ViewColumn.Beside);
            renderWebview(panel, workspacePath, lastPrompt);
            return panel;
        }
        panel = vscode.window.createWebviewPanel("atlasDemo", "Atlas Demo", vscode.ViewColumn.Beside, {
            enableScripts: true
        });
        panel.onDidDispose(() => (panel = undefined));
        panel.webview.onDidReceiveMessage(async (message) => {
            if (!message || message.type !== "runPrompt")
                return;
            const prompt = String(message.prompt || "").trim();
            if (!prompt) {
                vscode.window.showWarningMessage("Enter a prompt before running Atlas.");
                return;
            }
            lastPrompt = prompt;
            try {
                const ws = getWorkspacePath();
                await runPromptFlow(ws, prompt);
            }
            catch (err) {
                const messageText = err instanceof Error ? err.message : String(err);
                vscode.window.showErrorMessage(`Atlas run failed: ${messageText}`);
            }
        });
        renderWebview(panel, workspacePath, lastPrompt);
        return panel;
    };
    const runPromptFlow = async (workspacePath, prompt) => {
        const before = getAtlasCounts(workspacePath);
        try {
            const result = await runPython(workspacePath, ["run", "--prompt", prompt]);
            const after = getAtlasCounts(workspacePath);
            writeLastRunSummary(workspacePath, prompt, result.stdout, before, after);
            if (panel) {
                renderWebview(panel, workspacePath, lastPrompt);
            }
            vscode.window.showInformationMessage("Atlas run complete. Artifacts updated.");
        }
        catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            vscode.window.showErrorMessage(`Atlas run failed: ${message}`);
        }
    };
    context.subscriptions.push(vscode.commands.registerCommand("atlas.initProject", async () => {
        try {
            const ws = getWorkspacePath();
            await runPython(ws, ["init"]);
            ensurePanel(ws);
            vscode.window.showInformationMessage("Atlas initialized (.atlas/ created).");
        }
        catch (err) {
            const message = err instanceof Error ? err.message : String(err);
            vscode.window.showErrorMessage(`Atlas init failed: ${message}`);
        }
    }));
    context.subscriptions.push(vscode.commands.registerCommand("atlas.runPrompt", async () => {
        const ws = getWorkspacePath();
        ensurePanel(ws);
        const prompt = await vscode.window.showInputBox({
            prompt: "Atlas prompt",
            placeHolder: "Describe what you want Atlas to do"
        });
        if (!prompt)
            return;
        lastPrompt = prompt;
        await runPromptFlow(ws, prompt);
    }));
}
function deactivate() { }
//# sourceMappingURL=extension.js.map
"""
TUTIVRA — Educational Visual Generator

Generates HTML/CSS visual content for each scene based on its visual_type.
Uses deterministic rendering (no image generation API needed) for:
  - equations     → KaTeX-rendered LaTeX
  - code          → syntax-highlighted code blocks
  - bullet_list   → styled bullet lists
  - comparison    → side-by-side table
  - table         → HTML table
  - flowchart     → Mermaid diagram (rendered in browser)
  - timeline      → horizontal CSS timeline
  - diagram       → descriptive labeled diagram or Mermaid
  - graph         → Chart.js or ASCII art fallback
  - none          → empty / avatar-only

Each generate_* function returns an HTML string.
The Streamlit UI embeds this via st.components.v1.html().
"""

import re
import json
from typing import Any


# ════════════════════════════════════════════════════════════
# MAIN DISPATCHER
# ════════════════════════════════════════════════════════════

def generate_visual(
    visual_type: str,
    visual_content: str,
    on_screen_text: str = "",
    subject_area: str = "",
) -> str:
    """
    Generate an HTML visual for a scene.

    Args:
        visual_type:    One of the defined visual types.
        visual_content: The content to render (LaTeX, code, text, etc.)
        on_screen_text: Caption / subtitle to display.
        subject_area:   Subject hint for context-aware rendering.

    Returns:
        HTML string to embed in the UI.
    """

    vt = visual_type.lower().strip()
    vc = visual_content.strip() if visual_content else ""

    if vt == "equation":
        html = _render_equation(vc)
    elif vt == "code":
        html = _render_code(vc, subject_area)
    elif vt == "bullet_list":
        html = _render_bullet_list(vc)
    elif vt == "comparison":
        html = _render_comparison(vc)
    elif vt == "table":
        html = _render_table(vc)
    elif vt == "flowchart":
        html = _render_flowchart(vc)
    elif vt == "timeline":
        html = _render_timeline(vc)
    elif vt == "diagram":
        html = _render_diagram(vc)
    elif vt == "graph":
        html = _render_graph(vc)
    else:
        html = ""

    # Wrap with caption if provided
    if on_screen_text and html:
        html = _wrap_with_caption(html, on_screen_text)
    elif on_screen_text and not html:
        html = _render_caption_only(on_screen_text)

    return html


# ════════════════════════════════════════════════════════════
# VISUAL RENDERERS
# ════════════════════════════════════════════════════════════

def _render_equation(content: str) -> str:
    """
    Render a LaTeX equation using KaTeX (CDN, no server needed).
    content can be LaTeX with or without $$ delimiters.
    """
    # Clean up delimiters
    content = content.strip()
    if content.startswith("$$") and content.endswith("$$"):
        latex = content[2:-2].strip()
    elif content.startswith("$") and content.endswith("$"):
        latex = content[1:-1].strip()
    else:
        latex = content

    # Escape for JSON embedding
    latex_escaped = latex.replace("\\", "\\\\").replace('"', '\\"')

    return f"""
<div class="tutivra-visual equation-visual">
  <link rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css"
    crossorigin="anonymous">
  <script defer
    src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"
    crossorigin="anonymous"></script>
  <div id="katex-eq-{abs(hash(content)) % 100000}" class="katex-display-box">
    <span class="katex-loading">Loading equation...</span>
  </div>
  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      var el = document.getElementById("katex-eq-{abs(hash(content)) % 100000}");
      if (el && window.katex) {{
        try {{
          katex.render("{latex_escaped}", el, {{
            displayMode: true,
            throwOnError: false
          }});
        }} catch(e) {{
          el.innerHTML = "<code>{latex}</code>";
        }}
      }}
    }});
    // Also try immediately if DOM already loaded
    (function() {{
      function tryRender() {{
        var el = document.getElementById("katex-eq-{abs(hash(content)) % 100000}");
        if (el && window.katex) {{
          try {{
            katex.render("{latex_escaped}", el, {{
              displayMode: true,
              throwOnError: false
            }});
          }} catch(e) {{
            el.innerHTML = "<pre>{latex}</pre>";
          }}
        }} else if (el) {{
          setTimeout(tryRender, 300);
        }}
      }}
      setTimeout(tryRender, 100);
    }})();
  </script>
  <style>
    .equation-visual {{
      background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
      padding: 40px;
      border-radius: 16px;
      text-align: center;
      min-height: 120px;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .katex-display-box {{
      color: white;
      font-size: 1.8em;
    }}
    .katex {{ color: #f0e6ff !important; }}
    .katex-loading {{ color: #aaa; font-style: italic; }}
  </style>
</div>"""


def _render_code(content: str, subject_area: str = "") -> str:
    """Syntax-highlighted code block using highlight.js."""

    # Detect language from content or subject hint
    lang = _detect_code_language(content, subject_area)
    escaped = content.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f"""
<div class="tutivra-visual code-visual">
  <link rel="stylesheet"
    href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/atom-one-dark.min.css">
  <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
  <div class="code-header">
    <span class="lang-badge">{lang.upper()}</span>
    <span class="code-title">Code Example</span>
  </div>
  <pre><code class="language-{lang}">{escaped}</code></pre>
  <script>hljs.highlightAll();</script>
  <style>
    .code-visual {{
      background: #1e1e2e;
      border-radius: 12px;
      overflow: hidden;
    }}
    .code-header {{
      display: flex;
      align-items: center;
      gap: 10px;
      padding: 10px 16px;
      background: #313244;
      border-bottom: 1px solid #45475a;
    }}
    .lang-badge {{
      background: #cba6f7;
      color: #1e1e2e;
      padding: 2px 8px;
      border-radius: 4px;
      font-size: 0.75em;
      font-weight: bold;
    }}
    .code-title {{ color: #cdd6f4; font-size: 0.85em; }}
    .code-visual pre {{
      margin: 0;
      padding: 20px;
      font-size: 0.95em;
      overflow-x: auto;
    }}
    .code-visual code {{
      font-family: 'JetBrains Mono', 'Fira Code', monospace;
    }}
  </style>
</div>"""


def _render_bullet_list(content: str) -> str:
    """Render a styled bullet list from newline-separated text."""

    lines = [l.strip() for l in content.split("\n") if l.strip()]

    items_html = ""
    for i, line in enumerate(lines):
        # Strip leading bullet characters
        line = re.sub(r"^[-•*]\s*", "", line)
        items_html += f"""
        <li class="bullet-item" style="animation-delay: {i * 0.15}s">
          <span class="bullet-dot"></span>
          <span class="bullet-text">{line}</span>
        </li>"""

    return f"""
<div class="tutivra-visual bullet-visual">
  <ul class="bullet-list">{items_html}</ul>
  <style>
    .bullet-visual {{
      background: linear-gradient(135deg, #1a1a2e, #16213e);
      padding: 30px;
      border-radius: 16px;
    }}
    .bullet-list {{
      list-style: none;
      padding: 0;
      margin: 0;
    }}
    .bullet-item {{
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 10px 0;
      border-bottom: 1px solid rgba(255,255,255,0.08);
      animation: slideIn 0.4s ease forwards;
      opacity: 0;
    }}
    @keyframes slideIn {{
      from {{ transform: translateX(-20px); opacity: 0; }}
      to   {{ transform: translateX(0);     opacity: 1; }}
    }}
    .bullet-dot {{
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: linear-gradient(135deg, #a78bfa, #60a5fa);
      flex-shrink: 0;
      margin-top: 5px;
    }}
    .bullet-text {{
      color: #e2e8f0;
      font-size: 1.05em;
      line-height: 1.5;
    }}
  </style>
</div>"""


def _render_comparison(content: str) -> str:
    """Render a side-by-side comparison table."""

    lines = [l.strip() for l in content.split("\n") if l.strip()]
    rows = []
    header = ["Item A", "Item B"]

    for line in lines:
        if "vs" in line.lower() or "|" in line:
            parts = re.split(r"\s+vs\s+|\|", line, maxsplit=1)
            if len(parts) == 2:
                rows.append((parts[0].strip(), parts[1].strip()))
            elif ": " in line:
                rows.append((line, ""))
        elif ":" in line:
            k, _, v = line.partition(":")
            rows.append((k.strip(), v.strip()))
        else:
            rows.append((line, ""))

    if not rows:
        return _render_bullet_list(content)

    # Extract header if first row looks like headers
    if rows and ("vs" in rows[0][0].lower() or
                  rows[0][0].lower() in ("concept a", "left", "a", "item a")):
        header = [rows[0][0], rows[0][1]]
        rows = rows[1:]

    rows_html = "".join(
        f"<tr><td>{a}</td><td>{b}</td></tr>"
        for a, b in rows
    )

    return f"""
<div class="tutivra-visual comparison-visual">
  <table class="comparison-table">
    <thead>
      <tr>
        <th class="col-a">{header[0]}</th>
        <th class="col-b">{header[1]}</th>
      </tr>
    </thead>
    <tbody>{rows_html}</tbody>
  </table>
  <style>
    .comparison-visual {{
      background: linear-gradient(135deg, #0f172a, #1e293b);
      padding: 24px;
      border-radius: 16px;
      overflow: hidden;
    }}
    .comparison-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.95em;
    }}
    .comparison-table th {{
      padding: 12px 16px;
      text-align: center;
      font-weight: 600;
      font-size: 1em;
    }}
    .col-a {{ background: #312e81; color: #a5b4fc; }}
    .col-b {{ background: #1e3a5f; color: #93c5fd; }}
    .comparison-table td {{
      padding: 10px 16px;
      color: #cbd5e1;
      border-bottom: 1px solid rgba(255,255,255,0.07);
    }}
    .comparison-table tr:nth-child(even) td {{
      background: rgba(255,255,255,0.04);
    }}
  </style>
</div>"""


def _render_table(content: str) -> str:
    """Render a structured table from pipe-separated or newline content."""

    lines = [l.strip() for l in content.split("\n") if l.strip()]

    if not lines:
        return ""

    rows = []
    for line in lines:
        if "|" in line:
            cells = [c.strip() for c in line.split("|") if c.strip()]
            rows.append(cells)
        else:
            rows.append([line])

    # Filter out separator rows (--- lines)
    rows = [r for r in rows if not all(re.match(r"^[-:]+$", c) for c in r)]

    if not rows:
        return _render_bullet_list(content)

    header_row = rows[0]
    data_rows = rows[1:]

    header_html = "".join(f"<th>{h}</th>" for h in header_row)
    body_html = "".join(
        "<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>"
        for row in data_rows
    )

    return f"""
<div class="tutivra-visual table-visual">
  <table class="data-table">
    <thead><tr>{header_html}</tr></thead>
    <tbody>{body_html}</tbody>
  </table>
  <style>
    .table-visual {{
      background: #0f172a;
      padding: 24px;
      border-radius: 16px;
      overflow-x: auto;
    }}
    .data-table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 0.9em;
    }}
    .data-table th {{
      background: #1e40af;
      color: #bfdbfe;
      padding: 10px 14px;
      text-align: left;
      font-weight: 600;
    }}
    .data-table td {{
      padding: 9px 14px;
      color: #cbd5e1;
      border-bottom: 1px solid rgba(255,255,255,0.08);
    }}
    .data-table tr:hover td {{ background: rgba(255,255,255,0.05); }}
  </style>
</div>"""


def _render_flowchart(content: str) -> str:
    """Render a Mermaid flowchart diagram."""

    # Check if content is already Mermaid syntax
    if not content.strip().startswith(("graph", "flowchart", "sequenceDiagram",
                                        "classDiagram", "stateDiagram")):
        # Wrap plain text as a simple linear flowchart
        steps = [l.strip() for l in content.split("\n") if l.strip()]
        nodes = []
        links = []
        for i, step in enumerate(steps[:8]):  # max 8 nodes
            clean = re.sub(r"[^a-zA-Z0-9 ]", "", step)[:40]
            nodes.append(f'    N{i}["{clean}"]')
            if i > 0:
                links.append(f"    N{i-1} --> N{i}")
        mermaid_code = "graph TD\n" + "\n".join(nodes + links)
    else:
        mermaid_code = content

    return f"""
<div class="tutivra-visual flowchart-visual">
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <div class="mermaid">
{mermaid_code}
  </div>
  <script>
    mermaid.initialize({{
      startOnLoad: true,
      theme: 'dark',
      themeVariables: {{
        primaryColor: '#4c1d95',
        primaryTextColor: '#f3e8ff',
        lineColor: '#a78bfa',
        background: '#1e1b4b'
      }}
    }});
  </script>
  <style>
    .flowchart-visual {{
      background: #1e1b4b;
      padding: 24px;
      border-radius: 16px;
      overflow: auto;
    }}
  </style>
</div>"""


def _render_timeline(content: str) -> str:
    """Render a horizontal/vertical timeline."""

    items = [l.strip() for l in content.split("\n") if l.strip()]
    items_html = ""

    for i, item in enumerate(items[:8]):
        # Parse "Year: Event" or "Step: Description"
        if ":" in item:
            label, _, desc = item.partition(":")
            label = label.strip()
            desc = desc.strip()
        else:
            label = str(i + 1)
            desc = item

        items_html += f"""
        <div class="timeline-item">
          <div class="timeline-marker">{label}</div>
          <div class="timeline-content">{desc}</div>
        </div>"""

    return f"""
<div class="tutivra-visual timeline-visual">
  <div class="timeline">{items_html}</div>
  <style>
    .timeline-visual {{
      background: linear-gradient(135deg, #0c0a1e, #1a0533);
      padding: 30px;
      border-radius: 16px;
    }}
    .timeline {{
      display: flex;
      flex-direction: column;
      gap: 0;
      position: relative;
    }}
    .timeline::before {{
      content: '';
      position: absolute;
      left: 28px;
      top: 0;
      bottom: 0;
      width: 2px;
      background: linear-gradient(180deg, #7c3aed, #2563eb);
    }}
    .timeline-item {{
      display: flex;
      align-items: flex-start;
      gap: 20px;
      padding: 14px 0;
      position: relative;
    }}
    .timeline-marker {{
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: linear-gradient(135deg, #7c3aed, #2563eb);
      color: white;
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: bold;
      font-size: 0.85em;
      flex-shrink: 0;
      z-index: 1;
      text-align: center;
      padding: 4px;
    }}
    .timeline-content {{
      color: #e2e8f0;
      font-size: 0.95em;
      line-height: 1.5;
      padding-top: 16px;
      flex: 1;
    }}
  </style>
</div>"""


def _render_diagram(content: str) -> str:
    """
    Render a labeled diagram. If content has Mermaid syntax, use that.
    Otherwise render as a structured description.
    """

    if any(kw in content.lower() for kw in
           ["graph", "flowchart", "sequencediagram", "-->", "->"]):
        return _render_flowchart(content)

    # Fallback: render as descriptive bullet list with diagram header
    return f"""
<div class="tutivra-visual diagram-visual">
  <div class="diagram-header">Diagram</div>
  {_render_bullet_list(content)}
  <style>
    .diagram-visual {{ padding: 0; }}
    .diagram-header {{
      background: linear-gradient(90deg, #7c3aed, #2563eb);
      color: white;
      padding: 10px 20px;
      font-weight: 600;
      border-radius: 12px 12px 0 0;
      margin-bottom: -16px;
    }}
  </style>
</div>"""


def _render_graph(content: str) -> str:
    """
    Render a graph using Chart.js if data is parseable.
    Falls back to bullet list.
    """

    # Try to parse key: value pairs
    lines = [l.strip() for l in content.split("\n") if l.strip() and ":" in l]

    if len(lines) >= 2:
        labels = []
        values = []
        for line in lines[:10]:
            k, _, v = line.partition(":")
            labels.append(k.strip())
            try:
                values.append(float(v.strip().replace(",", "")))
            except ValueError:
                values.append(0)

        labels_json = json.dumps(labels)
        values_json = json.dumps(values)
        chart_id = f"chart-{abs(hash(content)) % 100000}"

        return f"""
<div class="tutivra-visual graph-visual">
  <canvas id="{chart_id}" height="200"></canvas>
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
  <script>
    (function() {{
      var ctx = document.getElementById('{chart_id}');
      if (!ctx) return;
      new Chart(ctx, {{
        type: 'bar',
        data: {{
          labels: {labels_json},
          datasets: [{{
            label: 'Values',
            data: {values_json},
            backgroundColor: 'rgba(139, 92, 246, 0.7)',
            borderColor: 'rgba(167, 139, 250, 1)',
            borderWidth: 2,
            borderRadius: 6,
          }}]
        }},
        options: {{
          responsive: true,
          plugins: {{
            legend: {{ labels: {{ color: '#e2e8f0' }} }},
          }},
          scales: {{
            x: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
            y: {{ ticks: {{ color: '#94a3b8' }}, grid: {{ color: 'rgba(255,255,255,0.1)' }} }},
          }}
        }}
      }});
    }})();
  </script>
  <style>
    .graph-visual {{
      background: #0f172a;
      padding: 24px;
      border-radius: 16px;
    }}
  </style>
</div>"""

    # Fallback to bullet list
    return _render_bullet_list(content)


# ════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════

def _wrap_with_caption(html: str, caption: str) -> str:
    return f"""
<div class="tutivra-scene-container">
  {html}
  <div class="scene-caption">{caption}</div>
  <style>
    .tutivra-scene-container {{ display: flex; flex-direction: column; gap: 12px; }}
    .scene-caption {{
      text-align: center;
      color: #94a3b8;
      font-size: 0.9em;
      font-style: italic;
      padding: 6px 0;
    }}
  </style>
</div>"""


def _render_caption_only(caption: str) -> str:
    return f"""
<div class="tutivra-visual caption-visual">
  <p class="caption-text">{caption}</p>
  <style>
    .caption-visual {{
      background: linear-gradient(135deg, #1e293b, #0f172a);
      padding: 40px 30px;
      border-radius: 16px;
      text-align: center;
    }}
    .caption-text {{
      color: #e2e8f0;
      font-size: 1.4em;
      font-weight: 500;
      margin: 0;
      line-height: 1.6;
    }}
  </style>
</div>"""


def _detect_code_language(code: str, subject_area: str = "") -> str:
    """Heuristic language detection for syntax highlighting."""

    code_lower = code.lower()

    if "def " in code or "import " in code and "class " in code:
        return "python"
    if "public class" in code or "System.out" in code:
        return "java"
    if "#include" in code or "cout <<" in code or "int main" in code:
        return "cpp"
    if "function " in code or "const " in code or "=>" in code:
        return "javascript"
    if "SELECT " in code_lower or "FROM " in code_lower:
        return "sql"
    if "<html" in code_lower or "<div" in code_lower:
        return "html"
    if "{" in code and ":" in code and ";" in code:
        return "css"

    subject = subject_area.lower()
    if "python" in subject:
        return "python"
    if "java" in subject and "javascript" not in subject:
        return "java"
    if "javascript" in subject or "js" in subject:
        return "javascript"

    return "python"  # Default to Python

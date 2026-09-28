"""Write data/labeler.html: a self-contained page for blind labeling.

Open it in a browser, pick a value per question for each diff, then click
"Download labels.csv" and save it over data/labels.csv. Progress autosaves in the
browser (localStorage), so closing the tab doesn't lose work. Nothing about a
diff's source (model / planted) is embedded.
"""

import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIELDS = [
    ("no_narration", "Every added comment explains intent/constraint/reason; none just restates the adjacent code (no comments = yes)", ["yes", "no"]),
    ("density", "How dense are the added comments?", ["none", "appropriate", "excessive"]),
    ("format", "Added comments/docstrings: consistent, inconsistent (mixed styles, casing, # spacing), malformed (misplaced docstring, cut off, wrong line)", ["consistent", "inconsistent", "malformed", "none"]),
    ("accurate", "Every added comment accurately describes what the code does (no comments = yes)", ["yes", "no"]),
    ("no_placeholder", "No placeholder/hedging comments ('in a real implementation', 'for simplicity', ownerless TODO) and no commented-out code", ["yes", "no"]),
    ("explains_why", "Wherever the change is non-obvious, a comment says why (nothing non-obvious = yes)", ["yes", "no"]),
    ("overall_slop", "Gut call: would you flag these comments in code review?", ["yes", "no"]),
]

PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>Comment-slop labeler</title>
<style>
body{font:14px/1.45 system-ui,sans-serif;max-width:1000px;margin:0 auto;padding:16px;background:#fafafa;color:#1a1a1a}
.card{background:#fff;border:1px solid #ddd;border-radius:8px;padding:14px;margin:14px 0}
pre{background:#f4f4f4;padding:10px;overflow-x:auto;font-size:12.5px;line-height:1.35}
.ln{display:block}.add{color:#116329;background:#e6ffec}.del{color:#82071e;background:#ffebe9}
.q{margin:6px 0}.q b{display:inline-block;min-width:120px}.q small{color:#555;display:block}
label{margin-right:12px;cursor:pointer}.done{border-color:#2da44e}
#bar{position:sticky;top:0;background:#fafafa;padding:8px 0;border-bottom:1px solid #ddd;z-index:1}
button{font-size:14px;padding:6px 12px}
</style></head><body>
<div id="bar"><b>Comment-slop labeler</b> · judge only comments/docstrings on <code>+</code> lines ·
<span id="progress"></span> <button onclick="dl()">Download labels.csv</button></div>
CARDS
<script>
const FIELDS=FIELDS_JSON, IDS=IDS_JSON, KEY="jev-slop-labels";
let st={}; try{st=JSON.parse(localStorage.getItem(KEY))||{}}catch(e){}
function save(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){} render()}
function render(){let n=0;for(const id of IDS){const ok=FIELDS.every(f=>st[id]&&st[id][f]);
 document.getElementById("c-"+id).classList.toggle("done",ok);if(ok)n++}
 document.getElementById("progress").textContent=n+" / "+IDS.length+" done"}
document.querySelectorAll("input[type=radio]").forEach(r=>{const[id,f]=r.name.split("|");
 if(st[id]&&st[id][f]===r.value)r.checked=true;
 r.onchange=()=>{st[id]=st[id]||{};st[id][f]=r.value;save()}});
document.querySelectorAll("textarea").forEach(t=>{const id=t.dataset.id;t.value=(st[id]&&st[id].notes)||"";
 t.oninput=()=>{st[id]=st[id]||{};st[id].notes=t.value;save()}});
function esc(s){s=s||"";return /[",\\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s}
function dl(){const cols=["id",...FIELDS,"notes"];const rows=[cols.join(",")];
 for(const id of IDS){const r=st[id]||{};rows.push([id,...FIELDS.map(f=>r[f]||""),esc(r.notes)].join(","))}
 const a=document.createElement("a");a.href=URL.createObjectURL(new Blob([rows.join("\\n")+"\\n"],{type:"text/csv"}));
 a.download="labels.csv";a.click()}
render();
</script></body></html>"""


def diff_html(diff: str) -> str:
    out = []
    for line in diff.splitlines():
        cls = "add" if line.startswith("+") and not line.startswith("+++") else \
              "del" if line.startswith("-") and not line.startswith("---") else ""
        esc = html.escape(line) or " "
        # Every line is its own block span; joining with "" avoids pre's newline doubling the spacing.
        out.append(f'<span class="ln {cls}">{esc}</span>')
    return "".join(out)


def main() -> None:
    diffs = [json.loads(l) for l in (ROOT / "data" / "diffs.jsonl").read_text().splitlines()]
    cards = []
    for d in diffs:
        qs = []
        for fid, text, values in FIELDS:
            radios = "".join(f'<label><input type="radio" name="{d["id"]}|{fid}" value="{v}"> {v}</label>' for v in values)
            qs.append(f'<div class="q"><b>{fid}</b> {radios}<small>{html.escape(text)}</small></div>')
        cards.append(f'<div class="card" id="c-{d["id"]}"><h3>{d["id"]}</h3><p><b>Task:</b> {html.escape(d["issue_text"])}</p>'
                     f'<pre>{diff_html(d["diff"])}</pre>{"".join(qs)}'
                     f'<div class="q"><b>notes</b> <textarea data-id="{d["id"]}" rows="1" cols="60"></textarea></div></div>')
    page = (PAGE.replace("CARDS", "\n".join(cards))
                .replace("FIELDS_JSON", json.dumps([f[0] for f in FIELDS]))
                .replace("IDS_JSON", json.dumps([d["id"] for d in diffs])))
    (ROOT / "data" / "labeler.html").write_text(page)
    print("wrote data/labeler.html")


if __name__ == "__main__":
    main()

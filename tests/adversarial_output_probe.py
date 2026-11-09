"""Standalone adversarial probe for confined output paths (PR #149221).

Confirms the FOUR injection classes from the catalog review are BLOCKED through
the model-facing handlers, plus the review's named examples, plus that a
legitimate bare-filename write succeeds and stays confined. Prints a clear
BLOCKED/ALLOWED table and exits 0 only if every attack is blocked and the
legitimate write is confined.

Run:  env -u PYTHONPATH python tests/adversarial_output_probe.py
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from plugin import handle_bim_render_view, handle_bim_takeoff
from plugin.bim_engine import _OUTPUT_SUBDIR

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
IFC = os.path.join(ROOT, "samples", "sample_house.ifc")

tmp = tempfile.TemporaryDirectory(prefix="bim-probe-home-")
os.environ["HERMES_HOME"] = tmp.name
OUT_ROOT = os.path.abspath(os.path.join(tmp.name, _OUTPUT_SUBDIR))

# Four attack classes. Payloads carry the correct suffix where relevant so a
# rejection proves the *path* rule, not the suffix rule.
CLASSES = [
    ("absolute path", handle_bim_render_view, "output_html",
     ["/tmp/pwn.html", "C:\\Windows\\pwn.html", "C:pwn.html"]),
    (".. traversal", handle_bim_render_view, "output_html",
     ["../escape.html", "..\\escape.html", "a/../../escape.html"]),
    ("wrong/missing suffix", handle_bim_takeoff, "output_xlsx",
     ["evil.txt", "evil", "evil.xlsx.txt"]),
    ("path separators", handle_bim_render_view, "output_html",
     ["sub/pwn.html", "sub\\pwn.html"]),
]
# The reviewer's named examples (also blocked: separators ~ and suffix).
REVIEW_EXAMPLES = [
    ("~/.bashrc (review)", handle_bim_render_view, "output_html",
     os.path.join("~", ".bashrc")),
    ("~/.ssh/authorized_keys (review)", handle_bim_render_view, "output_html",
     os.path.join("~", ".ssh", "authorized_keys")),
]


def is_error(resp):
    return str(resp).startswith("Error")


ok = True
print("=== four attack classes ===")
for label, fn, key, payloads in CLASSES:
    blocked = 0
    for value in payloads:
        args = {"ifc_path": IFC, key: value, "max_elements": 5}
        resp = fn(args)
        blocked += 1 if is_error(resp) else 0
        if not is_error(resp):
            print(f"  [ALLOWED!!] {label}: {value!r} -> {str(resp)[:100]}")
    all_blocked = (blocked == len(payloads))
    print(f"[{'BLOCKED' if all_blocked else 'FAILED '}] {label}: "
          f"{blocked}/{len(payloads)} payloads rejected")
    ok = ok and all_blocked

print("=== reviewer examples ===")
for label, fn, key, value in REVIEW_EXAMPLES:
    resp = fn({"ifc_path": IFC, key: value, "max_elements": 5})
    b = is_error(resp)
    print(f"[{'BLOCKED' if b else 'FAILED '}] {label}: {value!r} -> {str(resp)[:100]}")
    ok = ok and b

print("=== legitimate write ===")
resp = handle_bim_render_view({
    "ifc_path": IFC, "output_html": "probe_safe.html", "max_elements": 5,
})
if is_error(resp):
    print(f"[FAILED] legitimate write rejected: {str(resp)[:160]}")
    ok = False
else:
    data = json.loads(resp)
    final = data["output_html"]
    confined = os.path.commonpath([os.path.abspath(final), OUT_ROOT]) == OUT_ROOT
    exists = os.path.isfile(final)
    print(f"[{'OK' if confined and exists else 'FAILED'}] "
          f"confined={confined} exists={exists} -> {final}")
    ok = ok and confined and exists

tmp.cleanup()
print("PROBE RESULT:", "ALL ATTACKS BLOCKED + LEGIT WRITE CONFINED" if ok else "FAILURE")
sys.exit(0 if ok else 1)

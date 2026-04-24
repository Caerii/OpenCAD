from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from opencad_tree.models import FeatureTree


def build_system_prompt(tree_state: FeatureTree) -> str:
    tree_json = json.dumps(tree_state.model_dump(), indent=2, sort_keys=True)
    return (
        "OpenCAD Agent System Prompt\n"
        "\n"
        "Current feature tree state (JSON):\n"
        f"{tree_json}\n"
        "\n"
        "Available operations and their schemas:\n"
        "- add_sketch(name, entities, constraints) -> sketch_id\n"
        "- extrude(sketch_id, depth, name) -> feature_id\n"
        "- boolean_cut(base_id, tool_id, name) -> feature_id\n"
        "- fillet_edges(shape_id, edge_selection, radius, name) -> feature_id\n"
        "- add_cylinder(position, radius, height, name) -> feature_id\n"
        "- get_tree_state() -> FeatureTree JSON\n"
        "- get_shape_info(shape_id) -> dimensions, volume, surface_area\n"
        "\n"
        "Parametric features:\n"
        "- Nodes may have typed_parameters and parameter_bindings.\n"
        "- Bindings can include an 'expression' field for computed values.\n"
        "- Suppressed nodes (and their descendants) are transitively suppressed.\n"
        "\n"
        "Instruction: always name features descriptively.\n"
        "Instruction: verify shapes exist and are not suppressed before referencing them.\n"
        "Instruction: plan the full sequence before executing.\n"
    )


@lru_cache(maxsize=1)
def _load_example_scripts() -> str:
    examples_dir = Path(__file__).resolve().parents[2] / "examples"
    example_files = [
        "hardware_mounting_bracket.py",
        "hardware_pcb_carrier.py",
        "software_hmi_panel.py",
    ]
    snippets: list[str] = []
    for filename in example_files:
        path = examples_dir / filename
        if not path.exists():
            continue
        snippet = path.read_text(encoding="utf-8").strip()
        snippets.append(f"examples/{filename}:\n```python\n{snippet}\n```")
    return "\n\n".join(snippets)


_API_REFERENCE = """\
Sketch methods (all return self for chaining):
  Sketch(name=str, plane=str, origin=tuple)
  .line(start=(x,y), end=(x,y))
  .rect(width, height, *, origin=(x,y))
  .circle(radius, *, center=(x,y), subtract=bool)   # subtract cuts a hole in the profile

Part methods (all return self for chaining):
  Part(name=str)
  .box(length, width, height, *, name=str)
  .cylinder(radius, height, *, name=str)
  .sphere(radius, *, name=str)
  .extrude(sketch, *, depth, both=False, name=str)   # sketch is a Sketch instance, NO subtract arg
  .union(other_part, *, name=str)
  .cut(other_part, *, name=str)
  .fillet(*, edges=None|"all"|"top"|[id,...], radius, name=str)
  .chamfer(*, edges=None|"all"|"top"|[id,...], distance, name=str)
  .offset(distance, *, name=str)
  .linear_pattern(*, direction=(x,y,z), count, spacing, name=str)
  .circular_pattern(*, axis_origin=(x,y,z), axis_direction=(x,y,z), count, angle=360.0, name=str)
  .mirror(*, plane_origin=(x,y,z), plane_normal=(x,y,z), name=str)
"""


def build_code_generation_prompt(tree_state: FeatureTree) -> str:
    base_prompt = build_system_prompt(tree_state)
    examples = _load_example_scripts()
    return (
        f"{base_prompt}\n"
        "Generate OpenCAD Python code that matches the concise fluent style used in the repository examples.\n"
        "Requirements:\n"
        "- Return only valid Python code.\n"
        "- Use `from opencad import Part, Sketch`.\n"
        "- Prefer a named sketch variable followed by a named Part fluent chain.\n"
        "- Use descriptive names for sketches, parts, and operations.\n"
        "- Keep the script self-contained and aligned with the examples below.\n"
        "- Do not enclose the returned code with comment markers, or markers saying it's python, assume that the code is executed.\n"
        "\n"
        "API reference (use ONLY these signatures — do not invent parameters):\n"
        f"{_API_REFERENCE}\n"
        "Reference examples:\n"
        f"{examples}\n"
    )

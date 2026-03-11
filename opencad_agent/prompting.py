from __future__ import annotations

import json
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


def _load_example_scripts() -> str:
    examples_dir = Path(__file__).resolve().parents[1] / "examples"
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
        snippets.append(f"examples/{filename}:\n```python\n{path.read_text(encoding='utf-8').strip()}\n```")
    return "\n\n".join(snippets)


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
        "\n"
        "Reference examples:\n"
        f"{examples}\n"
    )

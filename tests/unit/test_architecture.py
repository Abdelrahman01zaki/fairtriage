import ast
from pathlib import Path

import ai_intelligence_lab.allocation as allocation_package


def test_the_allocation_core_never_imports_a_specific_domain():
    root = Path(allocation_package.__file__).parent
    offenders = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            offenders.extend(
                f"{path.name}: {name}"
                for name in names
                if name.startswith("ai_intelligence_lab.fairtriage")
            )

    assert offenders == []

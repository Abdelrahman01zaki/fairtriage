import ast
from pathlib import Path

import ai_intelligence_lab.fairtriage.benchmark.stats as stats_module

PACKAGE_OR_RELATIVE = ("ai_intelligence_lab", ".")


def package_imports(source: str) -> list[str]:
    """Every name imported from this package, absolute or relative."""
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            names.append("." * node.level + (node.module or ""))
    return [name for name in names if name.startswith(PACKAGE_OR_RELATIVE)]


def test_the_paired_statistics_import_nothing_from_this_package():
    source = Path(stats_module.__file__).read_text(encoding="utf-8")

    assert package_imports(source) == []


def test_the_import_check_sees_absolute_and_relative_imports():
    source = (
        "import ai_intelligence_lab.fairtriage\n"
        "from ai_intelligence_lab import fairtriage\n"
        "from . import records\n"
        "import math\n"
    )

    assert package_imports(source) == [
        "ai_intelligence_lab.fairtriage",
        "ai_intelligence_lab",
        ".",
    ]

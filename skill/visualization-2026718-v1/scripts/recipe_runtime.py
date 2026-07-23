#!/usr/bin/env python3
"""Deterministic Recipe materialization, preflight, and rendering helpers.

This module deliberately does not perform semantic vision.  It creates and runs
backend-pure plotting pipelines, records exact render artifacts, and leaves the
native pixel review to Codex through the visual-review controller.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable


SKILL_ROOT = Path(__file__).resolve().parents[1]
RECIPES_ROOT = SKILL_ROOT / "assets" / "recipes"


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def _json(path: Path) -> dict[str, Any]:
    value = json.loads(_read_text(path))
    if not isinstance(value, dict):
        raise ValueError(f"Expected a JSON object: {path}")
    return value


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_recipe(recipe_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[a-z0-9-]+", recipe_id or ""):
        raise ValueError(f"Invalid Recipe ID: {recipe_id!r}")
    directory = (RECIPES_ROOT / recipe_id).resolve()
    try:
        directory.relative_to(RECIPES_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("Recipe path escapes the bundled Recipe root") from exc
    metadata_path = directory / "recipe.json"
    if not metadata_path.exists():
        raise FileNotFoundError(f"Recipe not found: {recipe_id}")
    recipe = _json(metadata_path)
    if recipe.get("id") != recipe_id:
        raise ValueError(f"Recipe directory/metadata ID mismatch: {recipe_id}")
    recipe["_directory"] = directory
    recipe["_metadata_path"] = metadata_path
    return recipe


def _declared_parameter_names(recipe: dict[str, Any]) -> list[str]:
    """Return the stable, unique runtime parameter names declared by a Recipe."""
    names: list[str] = []
    for parameter in recipe.get("parameters") or []:
        if not isinstance(parameter, dict):
            continue
        name = str(parameter.get("name") or "")
        if name and name not in names:
            names.append(name)
    return names


def validate_runtime_parameters(
    recipe: dict[str, Any],
    parameters: dict[str, Any] | None,
    *,
    bind_input: bool = True,
) -> dict[str, Any]:
    """Fail closed when a render receives undeclared or rebound parameters.

    The renderer supplies the input artifact as the callable's first argument.
    Therefore callers may configure only the remaining parameters and may not
    rebind that input through ``--params-json``.
    """
    if parameters is None:
        parameters = {}
    if not isinstance(parameters, dict):
        raise ValueError(f"{recipe.get('id')}: runtime parameters must be an object")
    declared = _declared_parameter_names(recipe)
    declared_set = set(declared)
    unknown = sorted(str(name) for name in parameters if str(name) not in declared_set)
    if unknown:
        raise ValueError(
            f"{recipe.get('id')}: undeclared runtime parameter(s): {', '.join(unknown)}"
        )
    explicit_input = recipe.get("input_parameter")
    inferred_input = (
        declared[0]
        if declared
        and declared[0] in {"data", "object", "adata", "matrix", "matrix_data"}
        else None
    )
    bound_input = str(explicit_input or inferred_input or "") or None
    if bound_input and bound_input not in declared_set:
        raise ValueError(
            f"{recipe.get('id')}: input_parameter '{bound_input}' is not declared"
        )
    if bound_input and bound_input in parameters:
        raise ValueError(
            f"{recipe.get('id')}: input parameter '{bound_input}' is bound by --input and cannot be overridden"
        )
    return {
        "policy": "declared-only",
        "recipe_id": recipe.get("id"),
        "declared": declared,
        "bound_input": bound_input,
        "provided": sorted(str(name) for name in parameters),
        "status": "pass",
    }


def validate_component_parameters(
    chain: list[dict[str, Any]],
    component_kwargs: dict[str, Any] | None,
) -> dict[str, Any]:
    """Validate the nested parameter object used by a composed Recipe chain."""
    values = dict(component_kwargs or {})
    selected = {str(recipe.get("id")): recipe for recipe in chain}
    allowed_top_level = set(selected)
    if chain and chain[0].get("backend") == "python":
        allowed_top_level.add("__runtime__")
    unknown_components = sorted(str(name) for name in values if str(name) not in allowed_top_level)
    if unknown_components:
        raise ValueError(
            "composition received parameters for undeclared component(s): "
            + ", ".join(unknown_components)
        )
    checks: list[dict[str, Any]] = []
    for recipe_id, recipe in selected.items():
        payload = values.get(recipe_id, {})
        if not isinstance(payload, dict):
            raise ValueError(f"{recipe_id}: component parameters must be an object")
        checks.append(validate_runtime_parameters(recipe, payload, bind_input=True))
    if "__runtime__" in values:
        runtime = values["__runtime__"]
        if not isinstance(runtime, dict):
            raise ValueError("__runtime__: component parameters must be an object")
        unknown_runtime = sorted(set(runtime) - {"figure_size_inches"})
        if unknown_runtime:
            raise ValueError(
                "__runtime__: undeclared runtime parameter(s): "
                + ", ".join(unknown_runtime)
            )
    return {
        "policy": "declared-only",
        "composition_order": [recipe.get("id") for recipe in chain],
        "components": checks,
        "status": "pass",
    }


def recipe_code(recipe: dict[str, Any]) -> tuple[Path, str]:
    relative = str((recipe.get("files") or {}).get("code") or "")
    if not relative:
        raise ValueError(f"{recipe.get('id')}: files.code is missing")
    path = (Path(recipe["_directory"]) / relative).resolve()
    try:
        path.relative_to(SKILL_ROOT.resolve())
    except ValueError as exc:
        raise ValueError(f"{recipe.get('id')}: code path escapes the Skill root") from exc
    if not path.exists():
        raise FileNotFoundError(f"{recipe.get('id')}: code file is missing: {relative}")
    return path, _read_text(path)


def detect_entrypoint(recipe: dict[str, Any], code: str | None = None) -> str:
    declared = recipe.get("entrypoint") or (recipe.get("files") or {}).get("entrypoint")
    if declared:
        return str(declared)
    code = code if code is not None else recipe_code(recipe)[1]
    if recipe.get("backend") == "python":
        tree = ast.parse(code)
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_"):
                return node.name
    else:
        match = re.search(r"(?m)^\s*([A-Za-z][A-Za-z0-9_.]*)\s*<-\s*function\s*\(", code)
        if match:
            return match.group(1)
    raise ValueError(f"{recipe.get('id')}: no callable entrypoint found")


def build_chain(
    base_id: str,
    backend: str,
    adapter_id: str | None = None,
    modifier_ids: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    backend = str(backend).lower()
    if backend not in {"python", "r"}:
        raise ValueError("backend must be python or r")
    base = load_recipe(base_id)
    if base.get("kind") != "base_recipe":
        raise ValueError(f"{base_id} is not a base_recipe")
    ids = [*([adapter_id] if adapter_id else []), base_id, *(modifier_ids or [])]
    chain = [load_recipe(str(item)) for item in ids]
    for item in chain:
        if item.get("backend") != backend:
            raise ValueError(f"Backend mismatch: {item.get('id')} is {item.get('backend')}, requested {backend}")
    if adapter_id and chain[0].get("kind") != "adapter":
        raise ValueError(f"{adapter_id} is not an adapter")
    allowed_order = {"adapter": 0, "base_recipe": 1, "semantic_modifier": 2, "aesthetic_modifier": 3, "layout": 4, "export": 5}
    orders = [allowed_order.get(str(item.get("kind")), -1) for item in chain]
    if any(value < 0 for value in orders) or orders != sorted(orders):
        raise ValueError("Component order must be adapter -> base -> semantic -> aesthetic -> layout -> export")
    _validate_chain_compatibility(chain)
    return chain


def _contract_values(values: Iterable[Any]) -> set[str]:
    return {re.sub(r"[^a-z0-9]", "", str(value).lower()) for value in values if value is not None}


def _validate_chain_compatibility(chain: list[dict[str, Any]]) -> None:
    """Enforce declared allow-lists, object contracts, capabilities, and conflicts."""
    adapter = next((item for item in chain if item.get("kind") == "adapter"), None)
    base = next(item for item in chain if item.get("kind") == "base_recipe")
    selected_ids = {str(item.get("id")) for item in chain}
    for item in chain:
        conflicts = {str(value) for value in (item.get("conflicts") or [])}
        hit = sorted(conflicts & selected_ids)
        if hit:
            raise ValueError(f"{item.get('id')} conflicts with: {', '.join(hit)}")
    if adapter:
        provided = _contract_values((adapter.get("provides") or {}).get("object_types") or [])
        required = _contract_values((base.get("requires") or {}).get("object_types") or [])
        if provided and required and not provided & required:
            raise ValueError(f"{adapter.get('id')} output does not satisfy {base.get('id')} input")
        provided_caps = set((adapter.get("provides") or {}).get("capabilities") or [])
        required_caps = set((base.get("requires") or {}).get("capabilities") or [])
        if not required_caps.issubset(provided_caps):
            raise ValueError(f"{adapter.get('id')} lacks capabilities required by {base.get('id')}: {sorted(required_caps - provided_caps)}")
    objects = _contract_values((base.get("provides") or {}).get("object_types") or [])
    capabilities = set((base.get("provides") or {}).get("capabilities") or [])
    for component in [item for item in chain if item.get("kind") not in {"adapter", "base_recipe"}]:
        base_rules = base.get("compatible_with") or {}
        allowed_ids = set(base_rules.get("ids") or []) if isinstance(base_rules, dict) else set()
        allowed_kinds = set(base_rules.get("kinds") or []) if isinstance(base_rules, dict) else set()
        if allowed_ids and component.get("id") not in allowed_ids:
            raise ValueError(f"{component.get('id')} is not allowed by {base.get('id')}")
        if allowed_kinds and component.get("kind") not in allowed_kinds:
            raise ValueError(f"{component.get('kind')} is not allowed by {base.get('id')}")
        required_objects = _contract_values((component.get("requires") or {}).get("object_types") or [])
        if required_objects and objects and not required_objects & objects:
            raise ValueError(f"{component.get('id')} object requirement is not satisfied")
        required_caps = set((component.get("requires") or {}).get("capabilities") or [])
        if component.get("kind") == "semantic_modifier" and not required_caps.issubset(capabilities):
            raise ValueError(f"{component.get('id')} capability requirement is not satisfied: {sorted(required_caps - capabilities)}")
        provided_objects = _contract_values((component.get("provides") or {}).get("object_types") or [])
        if provided_objects:
            objects = provided_objects
        capabilities.update((component.get("provides") or {}).get("capabilities") or [])


def locate_rscript() -> str | None:
    found = shutil.which("Rscript")
    if found:
        return found
    candidates = [
        Path(r"C:\Program Files\R\R-4.5.3\bin\Rscript.exe"),
        Path(r"C:\Program Files\R\R-4.5.3\bin\x64\Rscript.exe"),
    ]
    base = Path(r"C:\Program Files\R")
    if base.exists():
        candidates.extend(sorted(base.glob(r"R-*\bin\Rscript.exe"), reverse=True))
        candidates.extend(sorted(base.glob(r"R-*\bin\x64\Rscript.exe"), reverse=True))
    return next((str(path) for path in candidates if path.exists()), None)


def _r_child_environment() -> tuple[dict[str, str], dict[str, Any]]:
    """Return an isolated R child environment with native Windows architecture restored."""
    environment = dict(os.environ)
    architecture: dict[str, Any] = {
        "platform": "windows" if os.name == "nt" else "non-windows",
        "parent_environment_modified": False,
    }
    if os.name != "nt" or sys.maxsize <= 2**32:
        return environment, architecture

    observed = environment.get("PROCESSOR_ARCHITECTURE", "").strip().upper()
    if observed and observed not in {"AMD64", "X64", "X86_64"}:
        raise RuntimeError(
            "PROCESSOR_ARCHITECTURE conflicts with the native 64-bit Python process"
        )
    environment["PROCESSOR_ARCHITECTURE"] = "AMD64"
    architecture.update(
        {
            "native_architecture": "X64",
            "processor_architecture": "AMD64",
            "processor_architecture_restored": not bool(observed),
        }
    )
    return environment, architecture


def _python_dependency_name(package: str) -> str:
    mapping = {
        "Pillow": "PIL",
        "scikit-learn": "sklearn",
        "adjustText": "adjustText",
    }
    return mapping.get(package, package.replace("-", "_"))


def preflight_chain(chain: list[dict[str, Any]]) -> dict[str, Any]:
    if not chain:
        raise ValueError("Recipe chain is empty")
    backend = str(chain[0].get("backend"))
    checks: list[dict[str, Any]] = []
    packages = sorted({str(pkg) for recipe in chain for pkg in ((recipe.get("requires") or {}).get("packages") or [])})
    syntax_ok = True
    for recipe in chain:
        path, code = recipe_code(recipe)
        entrypoint = None
        error = None
        try:
            entrypoint = detect_entrypoint(recipe, code)
            if backend == "python":
                ast.parse(code, filename=str(path))
        except Exception as exc:  # exact error is part of the preflight contract
            syntax_ok = False
            error = f"{type(exc).__name__}: {exc}"
        checks.append({"recipe_id": recipe.get("id"), "code": str(path), "entrypoint": entrypoint, "syntax": "pass" if error is None else "fail", "error": error})

    missing: list[str] = []
    runtime: dict[str, Any]
    if backend == "python":
        for package in packages:
            if importlib.util.find_spec(_python_dependency_name(package)) is None:
                missing.append(package)
        runtime = {"backend": "python", "executable": sys.executable, "version": sys.version.split()[0]}
    else:
        rscript = locate_rscript()
        runtime = {"backend": "r", "executable": rscript}
        if not rscript:
            missing.append("Rscript")
        elif packages:
            try:
                child_environment, architecture = _r_child_environment()
                runtime["child_architecture"] = architecture
            except RuntimeError as exc:
                child_environment = None
                runtime["probe_error"] = str(exc)
            encoded = json.dumps(packages)
            expression = (
                "pkgs <- jsonlite::fromJSON(commandArgs(trailingOnly=TRUE)[1]); "
                "missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly=TRUE)]; "
                "cat(paste(missing, collapse='\\n')); quit(status=if(length(missing)) 7 else 0)"
            )
            # jsonlite itself is not a Recipe dependency, so fall back to one
            # requireNamespace expression per package when it is unavailable.
            try:
                if child_environment is None:
                    raise RuntimeError(runtime["probe_error"])
                process = subprocess.run(
                    [rscript, "-e", expression, encoded],
                    env=child_environment,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )
                if process.returncode:
                    fallback_expr = "pkgs <- c(" + ",".join(json.dumps(pkg) for pkg in packages) + "); missing <- pkgs[!vapply(pkgs, requireNamespace, logical(1), quietly=TRUE)]; cat(paste(missing, collapse='\\n')); quit(status=if(length(missing)) 7 else 0)"
                    process = subprocess.run(
                        [rscript, "-e", fallback_expr],
                        env=child_environment,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        errors="replace",
                        timeout=30,
                    )
                if process.returncode == 7:
                    missing.extend(line.strip() for line in process.stdout.splitlines() if line.strip())
                elif process.returncode:
                    runtime["probe_error"] = (process.stderr or process.stdout).strip()[-1000:] or f"R dependency probe exited non-zero ({process.returncode})"
                    runtime["probe_returncode"] = process.returncode
            except RuntimeError:
                pass
            except subprocess.TimeoutExpired as exc:
                runtime["probe_error"] = f"R dependency probe timed out after {exc.timeout} seconds"
                runtime["probe_returncode"] = "timeout"

    return {
        "ok": syntax_ok and not missing and not runtime.get("probe_error"),
        "backend": backend,
        "recipes": [recipe.get("id") for recipe in chain],
        "runtime": runtime,
        "packages": packages,
        "missing_dependencies": sorted(set(missing)),
        "code_checks": checks,
    }


def _python_target_expression(recipe: dict[str, Any]) -> str:
    required = {str(value).lower().replace(" ", "") for value in ((recipe.get("requires") or {}).get("object_types") or [])}
    if any("axes" in value for value in required):
        return "axes"
    if any("figure" in value for value in required):
        return "figure"
    return "current"


def materialize_python(chain: list[dict[str, Any]]) -> tuple[str, dict[str, str]]:
    sections: list[str] = ["\"\"\"Materialized by visualization-2026718-v1; no implicit execution or saving.\"\"\"\nfrom __future__ import annotations"]
    entrypoints: dict[str, str] = {}
    for recipe in chain:
        _, code = recipe_code(recipe)
        entrypoints[str(recipe["id"])] = detect_entrypoint(recipe, code)
        code = re.sub(r"(?m)^\s*from __future__ import annotations\s*$", "", code).strip()
        sections.append(f"# ===== {recipe['id']} ({recipe['kind']}) =====\n{code}")

    adapter = next((item for item in chain if item.get("kind") == "adapter"), None)
    base = next(item for item in chain if item.get("kind") == "base_recipe")
    components = [item for item in chain if item.get("kind") not in {"adapter", "base_recipe"}]
    lines = [
        "def build_plot(data, component_kwargs=None):",
        "    \"\"\"Run the declared component interfaces and return the plot object.",
        "",
        "    ``component_kwargs`` is keyed by Recipe ID.  No data/statistical",
        "    transformation is invented by this wrapper.",
        "    \"\"\"",
        "    component_kwargs = dict(component_kwargs or {})",
        "    runtime_kwargs = dict(component_kwargs.pop('__runtime__', {}))",
        "    current = data",
        "    figure = None",
        "    axes = None",
    ]
    if adapter:
        lines.append(f"    current = {entrypoints[str(adapter['id'])]}(current, **dict(component_kwargs.get({adapter['id']!r}, {{}})))")
    lines.extend(
        [
            f"    current = {entrypoints[str(base['id'])]}(current, **dict(component_kwargs.get({base['id']!r}, {{}})))",
            "    if isinstance(current, tuple) and len(current) == 2:",
            "        figure, axes = current",
            "    elif hasattr(current, 'figure'):",
            "        axes = current",
            "        figure = current.figure",
            "    elif hasattr(current, 'savefig'):",
            "        figure = current",
        ]
    )
    lines.extend(
        [
            "    if figure is not None and runtime_kwargs.get('figure_size_inches'):",
            "        width, height = runtime_kwargs['figure_size_inches']",
            "        figure.set_size_inches(float(width), float(height), forward=True)",
            "        figure.canvas.draw()",
        ]
    )
    for component in components:
        component_id = str(component["id"])
        entrypoint = entrypoints[component_id]
        target = _python_target_expression(component)
        lines.extend(
            [
                f"    result = {entrypoint}({target}, **dict(component_kwargs.get({component_id!r}, {{}})))",
                "    if result is not None:",
                "        current = result",
                "        if hasattr(result, 'figure'):",
                "            axes, figure = result, result.figure",
                "        elif hasattr(result, 'savefig'):",
                "            figure = result",
            ]
        )
    lines.extend(["    return (figure, axes) if figure is not None and axes is not None else (figure if figure is not None else current)", ""])
    sections.append("\n".join(lines))
    code = "\n\n".join(sections).rstrip() + "\n"
    ast.parse(code, filename="<materialized-plot-recipe>")
    return code, entrypoints


def materialize_r(chain: list[dict[str, Any]]) -> tuple[str, dict[str, str]]:
    sections: list[str] = ["# Materialized by visualization-2026718-v1; no implicit execution or saving."]
    entrypoints: dict[str, str] = {}
    for recipe in chain:
        _, code = recipe_code(recipe)
        entrypoints[str(recipe["id"])] = detect_entrypoint(recipe, code)
        sections.append(f"# ===== {recipe['id']} ({recipe['kind']}) =====\n{code.rstrip()}")
    adapter = next((item for item in chain if item.get("kind") == "adapter"), None)
    base = next(item for item in chain if item.get("kind") == "base_recipe")
    components = [item for item in chain if item.get("kind") not in {"adapter", "base_recipe"}]
    lines = [
        "build_plot <- function(data, component_args = list()) {",
        "  get_args <- function(id) { value <- component_args[[id]]; if (is.null(value)) list() else value }",
        "  current <- data",
    ]
    if adapter:
        lines.append(f"  current <- do.call({entrypoints[str(adapter['id'])]}, c(list(current), get_args({json.dumps(str(adapter['id']))})))")
    lines.append(f"  current <- do.call({entrypoints[str(base['id'])]}, c(list(current), get_args({json.dumps(str(base['id']))})))")
    for component in components:
        component_id = str(component["id"])
        lines.append(f"  current <- do.call({entrypoints[component_id]}, c(list(current), get_args({json.dumps(component_id)})))")
    lines.extend(["  current", "}", ""])
    sections.append("\n".join(lines))
    return "\n\n".join(sections).rstrip() + "\n", entrypoints


def materialize_chain(chain: list[dict[str, Any]], output_dir: Path | None = None) -> dict[str, Any]:
    backend = str(chain[0].get("backend"))
    code, entrypoints = materialize_python(chain) if backend == "python" else materialize_r(chain)
    digest = hashlib.sha256("|".join(str(item["id"]) for item in chain).encode("utf-8")).hexdigest()[:12]
    candidate_id = f"candidate-{digest}"
    preflight = preflight_chain(chain)
    validation = {"schema": "pass", "syntax": "pass", "dependencies": "pass" if preflight["ok"] else "blocked"}
    result: dict[str, Any] = {
        "schema_version": "2.0",
        "id": candidate_id,
        "backend": backend,
        "entrypoint": "build_plot",
        "composition_order": [item.get("id") for item in chain],
        "component_entrypoints": entrypoints,
        "code": code,
        "preflight": preflight,
        "validation": validation,
        "status": "materialized_candidate",
        "promotable": False,
    }
    if output_dir is not None:
        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        code_name = "candidate.py" if backend == "python" else "candidate.R"
        code_path = output_dir / code_name
        code_path.write_text(code, encoding="utf-8", newline="\n")
        result["code_path"] = str(code_path)
        result["code_sha256"] = _sha256(code_path)
        metadata = {key: value for key, value in result.items() if key != "code"}
        _write_json(output_dir / "composition.json", metadata)
    return result


def _load_python_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load Python module: {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_input(path: Path):
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        import pandas as pd

        return pd.read_csv(path, sep="\t" if suffix == ".tsv" else ",")
    if suffix in {".json", ".jsonl"}:
        import pandas as pd

        return pd.read_json(path, lines=suffix == ".jsonl")
    if suffix == ".h5ad":
        import anndata as ad

        return ad.read_h5ad(path)
    raise ValueError("Supported runtime inputs are CSV, TSV, JSON, JSONL, and H5AD")


def _extract_figure(value: Any):
    if isinstance(value, tuple) and len(value) == 2:
        figure, axes = value
        if hasattr(figure, "savefig"):
            return figure, axes
    if hasattr(value, "savefig"):
        return value, None
    if hasattr(value, "figure") and hasattr(value.figure, "savefig"):
        return value.figure, value
    raise TypeError("Recipe did not return a Matplotlib Figure/Axes contract")


def render_python_recipe(
    recipe_id: str,
    input_path: Path,
    output_dir: Path,
    parameters: dict[str, Any] | None = None,
    width_mm: float = 85.0,
    height_mm: float = 70.0,
    dpi: int = 300,
) -> dict[str, Any]:
    recipe = load_recipe(recipe_id)
    if recipe.get("backend") != "python":
        raise ValueError("render_python_recipe requires a Python Recipe")
    parameter_contract = validate_runtime_parameters(recipe, parameters, bind_input=True)
    preflight = preflight_chain([recipe])
    if not preflight["ok"]:
        raise RuntimeError("Preflight failed: " + json.dumps(preflight, ensure_ascii=False))
    code_path, code = recipe_code(recipe)
    module = _load_python_module(code_path, "plot_code_retriever_runtime_" + hashlib.sha1(recipe_id.encode()).hexdigest()[:10])
    entrypoint = detect_entrypoint(recipe, code)
    data = load_input(input_path.resolve())
    result = getattr(module, entrypoint)(data, **dict(parameters or {}))
    figure, _ = _extract_figure(result)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    parameters_path = output_dir / f"{recipe_id}-parameters.json"
    parameters_path.write_text(
        json.dumps(parameters or {}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    # Formal Recipe previews follow the library convention: <id>.png plus a
    # <id>-final.png companion at the declared physical size.
    original = output_dir / f"{recipe_id}.png"
    final = output_dir / f"{recipe_id}-final.png"
    figure.savefig(original, dpi=150, bbox_inches="tight")
    figure.set_size_inches(width_mm / 25.4, height_mm / 25.4, forward=True)
    # The delivery artifact must honor the declared physical canvas exactly.
    # ``bbox_inches='tight'`` expands/shrinks the PNG around artists and breaks
    # the mm contract even when the figure size itself is correct.
    figure.savefig(final, dpi=dpi, bbox_inches=None)
    return {
        "status": "rendered_pending_native_review",
        "recipe_id": recipe_id,
        "backend": "python",
        "input_path": str(input_path.resolve()),
        "input_sha256": _sha256(input_path.resolve()),
        "code_path": str(code_path),
        "code_sha256": _sha256(code_path),
        "parameters": parameters or {},
        "parameters_path": str(parameters_path),
        "parameters_sha256": _sha256(parameters_path),
        "parameter_contract": parameter_contract,
        "original": {"path": str(original), "sha256": _sha256(original)},
        "final": {"path": str(final), "sha256": _sha256(final), "width_mm": width_mm, "height_mm": height_mm, "dpi": dpi},
        "preflight": preflight,
        "visual_review_completed": False,
        "note": "Open both artifacts with native image viewing; this renderer does not perform semantic vision.",
    }


def render_python_chain(
    chain: list[dict[str, Any]],
    input_path: Path,
    output_dir: Path,
    component_kwargs: dict[str, Any] | None = None,
    width_mm: float = 85.0,
    height_mm: float = 70.0,
    dpi: int = 300,
) -> dict[str, Any]:
    if not chain or chain[0].get("backend") != "python":
        raise ValueError("render_python_chain requires a Python Recipe chain")
    parameter_contract = validate_component_parameters(chain, component_kwargs)
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    materialized = materialize_chain(chain, output_dir)
    if not materialized["preflight"]["ok"]:
        raise RuntimeError("Preflight failed: " + json.dumps(materialized["preflight"], ensure_ascii=False))
    namespace: dict[str, Any] = {"__name__": "plot_code_retriever_materialized"}
    exec(compile(materialized["code"], "<visualization-2026718-v1-materialized>", "exec"), namespace, namespace)
    data = load_input(input_path.resolve())
    user_component_kwargs = dict(component_kwargs or {})
    result = namespace["build_plot"](data, user_component_kwargs)
    figure, _ = _extract_figure(result)
    candidate_id = str(materialized["id"])
    parameters_path = output_dir / f"{candidate_id}-parameters.json"
    parameters_path.write_text(
        json.dumps(component_kwargs or {}, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    original = output_dir / f"{candidate_id}-original.png"
    final = output_dir / f"{candidate_id}-final.png"
    figure.savefig(original, dpi=150, bbox_inches="tight")
    # Rebuild at the final physical size so layout- and label-aware modifiers
    # make decisions in the same geometry that is actually delivered. Merely
    # resizing an already-laid-out figure can reintroduce collisions.
    final_component_kwargs = dict(user_component_kwargs)
    final_component_kwargs["__runtime__"] = {
        "figure_size_inches": [width_mm / 25.4, height_mm / 25.4]
    }
    final_result = namespace["build_plot"](data, final_component_kwargs)
    final_figure, _ = _extract_figure(final_result)
    final_figure.savefig(final, dpi=dpi, bbox_inches=None)
    code_path = Path(str(materialized["code_path"]))
    code_sha = _sha256(code_path)
    return {
        "status": "rendered_pending_native_review",
        "candidate_id": candidate_id,
        "backend": "python",
        "composition_order": materialized["composition_order"],
        "input_path": str(input_path.resolve()),
        "input_sha256": _sha256(input_path.resolve()),
        "code_sha256": code_sha,
        "code_path": str(code_path),
        "component_kwargs": component_kwargs or {},
        "parameters_path": str(parameters_path),
        "parameters_sha256": _sha256(parameters_path),
        "component_parameter_contract": parameter_contract,
        "original": {"path": str(original), "sha256": _sha256(original)},
        "final": {"path": str(final), "sha256": _sha256(final), "width_mm": width_mm, "height_mm": height_mm, "dpi": dpi},
        "preflight": materialized["preflight"],
        "visual_review_completed": False,
        "note": "Open both artifacts with native image viewing; this renderer does not perform semantic vision.",
    }


def _r_literal(value: Any) -> str:
    """Encode JSON-shaped Python values as inert R literals.

    Runtime parameters never become executable R source.  Mapping keys are
    represented through ``setNames`` so Recipe IDs containing hyphens remain
    valid names.
    """

    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, int) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("R runtime parameters cannot contain NaN or infinity")
        return repr(value)
    if isinstance(value, (str, Path)):
        return json.dumps(str(value), ensure_ascii=False)
    if isinstance(value, (list, tuple)):
        encoded = ", ".join(_r_literal(item) for item in value)
        if value and all(item is None or isinstance(item, (bool, int, float, str, Path)) for item in value):
            return "c(" + encoded + ")"
        return "list(" + encoded + ")"
    if isinstance(value, dict):
        keys = list(value)
        values = ", ".join(_r_literal(value[key]) for key in keys)
        names = ", ".join(_r_literal(str(key)) for key in keys)
        return f"stats::setNames(list({values}), c({names}))"
    raise ValueError(f"Unsupported R runtime parameter type: {type(value).__name__}")


def _tail(value: Any, limit: int = 4000) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        text = value.decode("utf-8", errors="replace")
    else:
        text = str(value)
    return text[-limit:]


def _read_r_status(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    result: dict[str, str] = {}
    for line in _read_text(path).splitlines():
        key, separator, value = line.partition("\t")
        if separator and key:
            result[key] = value
    return result


def _valid_png(path: Path) -> bool:
    try:
        return path.is_file() and path.stat().st_size > 24 and path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    except OSError:
        return False


def _r_expected_side_effect(recipe_or_chain: dict[str, Any] | list[dict[str, Any]]) -> bool:
    if isinstance(recipe_or_chain, list):
        base = next((item for item in recipe_or_chain if item.get("kind") == "base_recipe"), recipe_or_chain[-1])
    else:
        base = recipe_or_chain
    object_types = _contract_values((base.get("provides") or {}).get("object_types") or [])
    return "graphicssideeffect" in object_types or "basegraphicssideeffect" in object_types


def _r_expected_matrix(recipe_or_chain: dict[str, Any] | list[dict[str, Any]]) -> bool:
    if isinstance(recipe_or_chain, list):
        adapter = next((item for item in recipe_or_chain if item.get("kind") == "adapter"), None)
        target = adapter or next(
            (item for item in recipe_or_chain if item.get("kind") == "base_recipe"), recipe_or_chain[0]
        )
    else:
        target = recipe_or_chain
    object_types = _contract_values((target.get("requires") or {}).get("object_types") or [])
    return "matrix" in object_types or "numericmatrix" in object_types


def _r_runner_source(
    *,
    code_path: Path,
    input_path: Path,
    entrypoint: str,
    parameters: dict[str, Any],
    composition: bool,
    side_effect: bool,
    matrix_input: bool,
    original_path: Path,
    final_path: Path,
    status_path: Path,
    original_width_mm: float,
    original_height_mm: float,
    width_mm: float,
    height_mm: float,
    dpi: int,
) -> str:
    """Build the auditable base-R runner used by ``Rscript --vanilla``."""

    parameter_literal = _r_literal(parameters)
    return f'''# Generated by visualization-2026718-v1 recipe_runtime.py.
# This runner renders deterministic artifacts but performs no semantic vision.
code_path <- {_r_literal(code_path.resolve().as_posix())}
input_path <- {_r_literal(input_path.resolve().as_posix())}
original_path <- {_r_literal(original_path.resolve().as_posix())}
final_path <- {_r_literal(final_path.resolve().as_posix())}
status_path <- {_r_literal(status_path.resolve().as_posix())}
entrypoint_name <- {_r_literal(entrypoint)}
runtime_parameters <- {parameter_literal}
composition_mode <- {"TRUE" if composition else "FALSE"}
side_effect_mode <- {"TRUE" if side_effect else "FALSE"}
matrix_input_mode <- {"TRUE" if matrix_input else "FALSE"}

sanitize_status <- function(value) {{
  value <- paste(as.character(value), collapse = ",")
  gsub("[\\r\\n\\t]+", " ", value)
}}
write_status <- function(values) {{
  lines <- vapply(names(values), function(key) paste(key, sanitize_status(values[[key]]), sep = "\\t"), character(1))
  writeLines(lines, status_path, useBytes = TRUE)
}}
load_runtime_input <- function(path) {{
  normalize_delimited <- function(value) {{
    if (!isTRUE(matrix_input_mode)) return(value)
    if (is.matrix(value)) return(value)
    if (!is.data.frame(value)) return(as.matrix(value))
    if (ncol(value) > 1L) {{
      first_name <- tolower(names(value)[1])
      identifier_name <- first_name %in% c("row", "rowname", "rownames", "feature", "gene", "source", "id", "x")
      remaining_numeric <- all(vapply(value[-1], is.numeric, logical(1)))
      first_values <- as.character(value[[1]])
      usable_names <- all(!is.na(first_values) & nzchar(first_values)) && !anyDuplicated(first_values)
      if (remaining_numeric && usable_names && (identifier_name || !is.numeric(value[[1]]))) {{
        rownames(value) <- first_values
        value <- value[-1]
      }}
    }}
    as.matrix(value)
  }}
  extension <- tolower(tools::file_ext(path))
  if (extension == "rds") return(readRDS(path))
  if (extension == "csv") return(normalize_delimited(utils::read.csv(path, check.names = FALSE, stringsAsFactors = FALSE)))
  if (extension == "tsv") return(normalize_delimited(utils::read.delim(path, check.names = FALSE, stringsAsFactors = FALSE)))
  if (extension %in% c("json", "jsonl")) {{
    if (!requireNamespace("jsonlite", quietly = TRUE)) stop("JSON input requires package 'jsonlite'.")
    if (extension == "jsonl") {{
      connection <- file(path, open = "rb")
      on.exit(close(connection), add = TRUE)
      return(normalize_delimited(jsonlite::stream_in(connection, verbose = FALSE, simplifyDataFrame = TRUE)))
    }}
    return(normalize_delimited(jsonlite::fromJSON(path, simplifyVector = TRUE, simplifyDataFrame = TRUE, simplifyMatrix = TRUE)))
  }}
  stop("R runtime inputs must be trusted local RDS, CSV, TSV, JSON, or JSONL.")
}}
open_png <- function(path, width_mm, height_mm, dpi) {{
  grDevices::png(filename = path, width = width_mm, height = height_mm, units = "mm", res = dpi, bg = "white")
}}
draw_on_device <- function(path, width_mm, height_mm, dpi, draw_function) {{
  open_png(path, width_mm, height_mm, dpi)
  device <- grDevices::dev.cur()
  closed <- FALSE
  on.exit({{
    if (!closed && device %in% grDevices::dev.list()) try(grDevices::dev.off(device), silent = TRUE)
  }}, add = TRUE)
  value <- draw_function()
  grDevices::dev.off(device)
  closed <- TRUE
  invisible(value)
}}
save_ggplot <- function(plot, path, width_mm, height_mm, dpi) {{
  if (!requireNamespace("ggplot2", quietly = TRUE)) stop("Rendering a ggplot/patchwork object requires package 'ggplot2'.")
  ggplot2::ggsave(filename = path, plot = plot, width = width_mm, height = height_mm,
                  units = "mm", dpi = dpi, bg = "white", limitsize = FALSE)
}}
save_grid_object <- function(object, path, width_mm, height_mm, dpi, heatmap = FALSE) {{
  draw_on_device(path, width_mm, height_mm, dpi, function() {{
    grid::grid.newpage()
    if (isTRUE(heatmap)) ComplexHeatmap::draw(object) else grid::grid.draw(object)
  }})
}}
save_recorded_plot <- function(object, path, width_mm, height_mm, dpi) {{
  draw_on_device(path, width_mm, height_mm, dpi, function() grDevices::replayPlot(object))
}}

exit_status <- 0L
tryCatch({{
  if (!file.exists(code_path)) stop("Recipe code file is unavailable.")
  if (!file.exists(input_path)) stop("Runtime input file is unavailable.")
  recipe_env <- new.env(parent = baseenv())
  sys.source(code_path, envir = recipe_env, keep.source = TRUE)
  if (!exists(entrypoint_name, envir = recipe_env, inherits = FALSE)) stop("Declared entrypoint was not defined: ", entrypoint_name)
  target <- get(entrypoint_name, envir = recipe_env, inherits = FALSE)
  if (!is.function(target)) stop("Declared entrypoint is not callable: ", entrypoint_name)
  data <- load_runtime_input(input_path)
  invoke <- if (isTRUE(composition_mode)) {{
    function() do.call(target, list(data, runtime_parameters))
  }} else {{
    function() do.call(target, c(list(data), runtime_parameters))
  }}

  if (isTRUE(side_effect_mode)) {{
    first_result <- draw_on_device(original_path, {original_width_mm!r}, {original_height_mm!r}, 150L, invoke)
    final_result <- draw_on_device(final_path, {width_mm!r}, {height_mm!r}, {int(dpi)}L, invoke)
    object_class <- paste(class(final_result), collapse = ",")
    renderer <- "base_graphics_side_effect"
  }} else {{
    result <- invoke()
    object_class <- paste(class(result), collapse = ",")
    renderable <- result
    if (is.list(result) && !is.null(result$plot) && inherits(result$plot, c("ggplot", "patchwork"))) renderable <- result$plot
    if (inherits(renderable, c("ggplot", "patchwork"))) {{
      save_ggplot(renderable, original_path, {original_width_mm!r}, {original_height_mm!r}, 150L)
      save_ggplot(renderable, final_path, {width_mm!r}, {height_mm!r}, {int(dpi)}L)
      renderer <- "ggplot2_ggsave"
    }} else if (inherits(renderable, c("Heatmap", "HeatmapList"))) {{
      if (!requireNamespace("ComplexHeatmap", quietly = TRUE)) stop("Rendering a Heatmap object requires package 'ComplexHeatmap'.")
      save_grid_object(renderable, original_path, {original_width_mm!r}, {original_height_mm!r}, 150L, heatmap = TRUE)
      save_grid_object(renderable, final_path, {width_mm!r}, {height_mm!r}, {int(dpi)}L, heatmap = TRUE)
      renderer <- "ComplexHeatmap_draw"
    }} else if (grid::is.grob(renderable)) {{
      save_grid_object(renderable, original_path, {original_width_mm!r}, {original_height_mm!r}, 150L, heatmap = FALSE)
      save_grid_object(renderable, final_path, {width_mm!r}, {height_mm!r}, {int(dpi)}L, heatmap = FALSE)
      renderer <- "grid_draw"
    }} else if (inherits(renderable, "recordedplot")) {{
      save_recorded_plot(renderable, original_path, {original_width_mm!r}, {original_height_mm!r}, 150L)
      save_recorded_plot(renderable, final_path, {width_mm!r}, {height_mm!r}, {int(dpi)}L)
      renderer <- "replayPlot"
    }} else {{
      stop("Unsupported R plot object contract: ", paste(class(renderable), collapse = ","),
           ". Supported contracts are ggplot/patchwork, ComplexHeatmap Heatmap/HeatmapList, grid grob, recordedplot, or a declared graphics_side_effect Recipe.")
    }}
  }}
  if (!file.exists(original_path) || file.info(original_path)$size <= 24) stop("Original PNG was not created or is empty.")
  if (!file.exists(final_path) || file.info(final_path)$size <= 24) stop("Final PNG was not created or is empty.")
  write_status(list(STATUS = "OK", OBJECT_CLASS = object_class, RENDERER = renderer,
                    ENTRYPOINT = entrypoint_name, NATIVE_REVIEW = "pending_native_review"))
}}, error = function(error) {{
  exit_status <<- 9L
  write_status(list(STATUS = "BLOCKED", ERROR_CLASS = paste(class(error), collapse = ","),
                    ERROR_MESSAGE = conditionMessage(error), ENTRYPOINT = entrypoint_name,
                    NATIVE_REVIEW = "not_started"))
}})
quit(save = "no", status = exit_status, runLast = FALSE)
'''


def _r_blocked_result(
    *,
    reason: str,
    stage: str,
    input_path: Path,
    code_path: Path,
    preflight: dict[str, Any],
    identity: dict[str, Any],
    process: subprocess.CompletedProcess[str] | None = None,
    status_record: dict[str, str] | None = None,
    partial_paths: Iterable[Path] = (),
    runner_path: Path | None = None,
) -> dict[str, Any]:
    partial = []
    for path in partial_paths:
        if path.is_file():
            partial.append({"path": str(path), "sha256": _sha256(path), "usable": False})
    result: dict[str, Any] = {
        "ok": False,
        "status": "blocked",
        "backend": "r",
        **identity,
        "stage": stage,
        "reason": reason,
        "input_path": str(input_path.resolve()),
        "input_sha256": _sha256(input_path.resolve()) if input_path.is_file() else None,
        "data_sha256": _sha256(input_path.resolve()) if input_path.is_file() else None,
        "code_path": str(code_path.resolve()),
        "code_sha256": _sha256(code_path.resolve()) if code_path.is_file() else None,
        "preflight": preflight,
        "r_status": status_record or {},
        "partial_artifacts": partial,
        "visual_review_completed": False,
        "native_review_status": "not_started",
    }
    if runner_path and runner_path.is_file():
        result["runner_path"] = str(runner_path)
        result["runner_sha256"] = _sha256(runner_path)
    if process is not None:
        result["r_process"] = {
            "returncode": process.returncode,
            "stdout_tail": _tail(process.stdout),
            "stderr_tail": _tail(process.stderr),
        }
    return result


def _run_r_render(
    *,
    input_path: Path,
    code_path: Path,
    entrypoint: str,
    parameters: dict[str, Any],
    output_dir: Path,
    artifact_stem: str,
    preflight: dict[str, Any],
    identity: dict[str, Any],
    composition: bool,
    side_effect: bool,
    matrix_input: bool,
    width_mm: float,
    height_mm: float,
    dpi: int,
    timeout_seconds: float,
) -> dict[str, Any]:
    input_path = input_path.resolve()
    code_path = code_path.resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"Runtime input is missing: {input_path}")
    if input_path.suffix.lower() not in {".rds", ".csv", ".tsv", ".json", ".jsonl"}:
        raise ValueError("R runtime inputs must be trusted local RDS, CSV, TSV, JSON, or JSONL")
    if not code_path.is_file():
        raise FileNotFoundError(f"R Recipe code is missing: {code_path}")
    if not math.isfinite(width_mm) or not math.isfinite(height_mm) or width_mm <= 0 or height_mm <= 0:
        raise ValueError("width_mm and height_mm must be finite positive values")
    if not isinstance(dpi, int) or isinstance(dpi, bool) or dpi <= 0:
        raise ValueError("dpi must be a positive integer")
    if not math.isfinite(timeout_seconds) or timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be positive")
    if not preflight.get("ok"):
        return _r_blocked_result(
            reason="R Recipe preflight failed; rendering was not attempted.",
            stage="preflight",
            input_path=input_path,
            code_path=code_path,
            preflight=preflight,
            identity=identity,
        )
    rscript = (preflight.get("runtime") or {}).get("executable") or locate_rscript()
    if not rscript:
        return _r_blocked_result(
            reason="Rscript is unavailable.",
            stage="preflight",
            input_path=input_path,
            code_path=code_path,
            preflight=preflight,
            identity=identity,
        )

    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    safe_stem = re.sub(r"[^A-Za-z0-9_.-]", "-", artifact_stem)
    original = output_dir / f"{safe_stem}-original.png"
    final = output_dir / f"{safe_stem}-final.png"
    status_path = output_dir / f"{safe_stem}-runtime-status.tsv"
    runner_path = output_dir / f"{safe_stem}-runtime.R"
    for stale in (original, final, status_path):
        stale.unlink(missing_ok=True)
    original_width_mm = max(160.0, float(width_mm))
    original_height_mm = original_width_mm * float(height_mm) / float(width_mm)
    runner_source = _r_runner_source(
        code_path=code_path,
        input_path=input_path,
        entrypoint=entrypoint,
        parameters=parameters,
        composition=composition,
        side_effect=side_effect,
        matrix_input=matrix_input,
        original_path=original,
        final_path=final,
        status_path=status_path,
        original_width_mm=original_width_mm,
        original_height_mm=original_height_mm,
        width_mm=float(width_mm),
        height_mm=float(height_mm),
        dpi=dpi,
    )
    runner_path.write_text(runner_source, encoding="utf-8", newline="\n")
    try:
        child_environment, _architecture = _r_child_environment()
        process = subprocess.run(
            [str(rscript), "--vanilla", str(runner_path)],
            cwd=str(output_dir),
            env=child_environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            check=False,
        )
    except RuntimeError as exc:
        return _r_blocked_result(
            reason=f"R child environment is invalid: {exc}",
            stage="execute",
            input_path=input_path,
            code_path=code_path,
            preflight=preflight,
            identity=identity,
            partial_paths=(original, final),
            runner_path=runner_path,
        )
    except subprocess.TimeoutExpired as exc:
        return _r_blocked_result(
            reason=f"R rendering timed out after {timeout_seconds:g} seconds.",
            stage="execute",
            input_path=input_path,
            code_path=code_path,
            preflight=preflight,
            identity=identity,
            partial_paths=(original, final),
            runner_path=runner_path,
            status_record={"STATUS": "TIMEOUT", "STDOUT": _tail(exc.stdout), "STDERR": _tail(exc.stderr)},
        )
    status_record = _read_r_status(status_path)
    if process.returncode != 0:
        return _r_blocked_result(
            reason=f"Rscript exited non-zero ({process.returncode}); artifacts, if any, are not accepted.",
            stage="execute",
            input_path=input_path,
            code_path=code_path,
            preflight=preflight,
            identity=identity,
            process=process,
            status_record=status_record,
            partial_paths=(original, final),
            runner_path=runner_path,
        )
    if status_record.get("STATUS") != "OK":
        message = status_record.get("ERROR_MESSAGE") or "R runner did not produce an OK status record."
        return _r_blocked_result(
            reason=message,
            stage="object_contract" if "Unsupported R plot object" in message else "execute",
            input_path=input_path,
            code_path=code_path,
            preflight=preflight,
            identity=identity,
            process=process,
            status_record=status_record,
            partial_paths=(original, final),
            runner_path=runner_path,
        )
    if not _valid_png(original) or not _valid_png(final):
        return _r_blocked_result(
            reason="R returned success but one or both PNG artifacts failed signature/size validation.",
            stage="artifact_validation",
            input_path=input_path,
            code_path=code_path,
            preflight=preflight,
            identity=identity,
            process=process,
            status_record=status_record,
            partial_paths=(original, final),
            runner_path=runner_path,
        )
    return {
        "ok": True,
        "status": "rendered_pending_native_review",
        "backend": "r",
        **identity,
        "entrypoint": entrypoint,
        "input_path": str(input_path),
        "input_sha256": _sha256(input_path),
        "data_sha256": _sha256(input_path),
        "code_path": str(code_path),
        "code_sha256": _sha256(code_path),
        "runner_path": str(runner_path),
        "runner_sha256": _sha256(runner_path),
        "parameters": parameters,
        "original": {
            "path": str(original),
            "sha256": _sha256(original),
            "width_mm": original_width_mm,
            "height_mm": original_height_mm,
            "dpi": 150,
        },
        "final": {
            "path": str(final),
            "sha256": _sha256(final),
            "width_mm": width_mm,
            "height_mm": height_mm,
            "dpi": dpi,
        },
        "r_process": {
            "returncode": process.returncode,
            "stdout_tail": _tail(process.stdout),
            "stderr_tail": _tail(process.stderr),
        },
        "r_status": status_record,
        "preflight": preflight,
        "visual_review_completed": False,
        "native_review_status": "pending_native_review",
        "note": "Open both artifacts with native image viewing; R and Python metadata checks do not perform semantic vision.",
    }


def render_r_recipe(
    recipe_id: str,
    input_path: Path,
    output_dir: Path,
    parameters: dict[str, Any] | None = None,
    width_mm: float = 85.0,
    height_mm: float = 70.0,
    dpi: int = 300,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    recipe = load_recipe(recipe_id)
    if recipe.get("backend") != "r":
        raise ValueError("render_r_recipe requires an R Recipe")
    normalized_parameters = dict(parameters or {})
    parameter_contract = validate_runtime_parameters(
        recipe, normalized_parameters, bind_input=True
    )
    code_path, code = recipe_code(recipe)
    entrypoint = detect_entrypoint(recipe, code)
    preflight = preflight_chain([recipe])
    result = _run_r_render(
        input_path=input_path,
        code_path=code_path,
        entrypoint=entrypoint,
        parameters=normalized_parameters,
        output_dir=output_dir,
        artifact_stem=recipe_id,
        preflight=preflight,
        identity={"recipe_id": recipe_id},
        composition=False,
        side_effect=_r_expected_side_effect(recipe),
        matrix_input=_r_expected_matrix(recipe),
        width_mm=width_mm,
        height_mm=height_mm,
        dpi=dpi,
        timeout_seconds=timeout_seconds,
    )
    result.setdefault("recipe_kind", recipe.get("kind"))
    result["parameter_contract"] = parameter_contract
    return result


def render_r_chain(
    chain: list[dict[str, Any]],
    input_path: Path,
    output_dir: Path,
    component_kwargs: dict[str, Any] | None = None,
    width_mm: float = 85.0,
    height_mm: float = 70.0,
    dpi: int = 300,
    timeout_seconds: float = 120.0,
) -> dict[str, Any]:
    if not chain or chain[0].get("backend") != "r":
        raise ValueError("render_r_chain requires an R Recipe chain")
    normalized_component_kwargs = dict(component_kwargs or {})
    parameter_contract = validate_component_parameters(
        chain, normalized_component_kwargs
    )
    output_dir = output_dir.resolve()
    materialized = materialize_chain(chain, output_dir)
    code_path = Path(str(materialized["code_path"]))
    identity = {
        "candidate_id": materialized["id"],
        "composition_order": materialized["composition_order"],
        "component_entrypoints": materialized["component_entrypoints"],
    }
    result = _run_r_render(
        input_path=input_path,
        code_path=code_path,
        entrypoint="build_plot",
        parameters=normalized_component_kwargs,
        output_dir=output_dir,
        artifact_stem=str(materialized["id"]),
        preflight=materialized["preflight"],
        identity=identity,
        composition=True,
        side_effect=_r_expected_side_effect(chain),
        matrix_input=_r_expected_matrix(chain),
        width_mm=width_mm,
        height_mm=height_mm,
        dpi=dpi,
        timeout_seconds=timeout_seconds,
    )
    if "parameters" in result:
        result["component_kwargs"] = result.pop("parameters")
    result["component_parameter_contract"] = parameter_contract
    return result


def _parse_json_argument(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    path = Path(value)
    if path.exists():
        return _json(path)
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError("JSON parameters must be an object")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Materialize, preflight, and render visualization-2026718-v1 Recipes")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preflight", "materialize"):
        command = sub.add_parser(name)
        command.add_argument("--backend", required=True, choices=["python", "r"])
        command.add_argument("--base-id", required=True)
        command.add_argument("--adapter-id")
        command.add_argument("--modifier", action="append", default=[])
        if name == "materialize":
            command.add_argument("--output-dir", type=Path)
    render = sub.add_parser("render")
    render.add_argument("--recipe-id", required=True)
    render.add_argument("--input", required=True, type=Path)
    render.add_argument("--output-dir", required=True, type=Path)
    render.add_argument("--params-json")
    render.add_argument("--width-mm", type=float, default=85.0)
    render.add_argument("--height-mm", type=float, default=70.0)
    render.add_argument("--dpi", type=int, default=300)
    render.add_argument("--timeout-seconds", type=float, default=120.0)
    render_chain = sub.add_parser("render-composition")
    render_chain.add_argument("--backend", required=True, choices=["python", "r"])
    render_chain.add_argument("--base-id", required=True)
    render_chain.add_argument("--adapter-id")
    render_chain.add_argument("--modifier", action="append", default=[])
    render_chain.add_argument("--input", required=True, type=Path)
    render_chain.add_argument("--output-dir", required=True, type=Path)
    render_chain.add_argument("--component-kwargs")
    render_chain.add_argument("--width-mm", type=float, default=85.0)
    render_chain.add_argument("--height-mm", type=float, default=70.0)
    render_chain.add_argument("--dpi", type=int, default=300)
    render_chain.add_argument("--timeout-seconds", type=float, default=120.0)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command in {"preflight", "materialize"}:
            chain = build_chain(args.base_id, args.backend, args.adapter_id, args.modifier)
            result = preflight_chain(chain) if args.command == "preflight" else materialize_chain(chain, args.output_dir)
        elif args.command == "render":
            recipe = load_recipe(args.recipe_id)
            parameters = _parse_json_argument(args.params_json)
            if recipe.get("backend") == "r":
                result = render_r_recipe(
                    args.recipe_id,
                    args.input,
                    args.output_dir,
                    parameters,
                    args.width_mm,
                    args.height_mm,
                    args.dpi,
                    args.timeout_seconds,
                )
            elif recipe.get("backend") == "python":
                result = render_python_recipe(args.recipe_id, args.input, args.output_dir, parameters, args.width_mm, args.height_mm, args.dpi)
            else:
                raise ValueError(f"Unsupported Recipe backend: {recipe.get('backend')}")
        else:
            chain = build_chain(args.base_id, args.backend, args.adapter_id, args.modifier)
            component_kwargs = _parse_json_argument(args.component_kwargs)
            if args.backend == "r":
                result = render_r_chain(
                    chain,
                    args.input,
                    args.output_dir,
                    component_kwargs,
                    args.width_mm,
                    args.height_mm,
                    args.dpi,
                    args.timeout_seconds,
                )
            else:
                result = render_python_chain(chain, args.input, args.output_dir, component_kwargs, args.width_mm, args.height_mm, args.dpi)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result.get("ok", True) else 8
    except Exception as exc:
        print(json.dumps({"ok": False, "error": type(exc).__name__, "message": str(exc)}, ensure_ascii=False, indent=2), file=sys.stderr)
        return 8


if __name__ == "__main__":
    raise SystemExit(main())

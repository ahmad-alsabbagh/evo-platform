"""Validate Agent Skills metadata without executing skill resources."""
import argparse
import json
from pathlib import Path
import unicodedata

import yaml


class UniqueLoader(yaml.SafeLoader):
    """Reject ambiguous duplicate mapping keys."""


def unique_mapping(loader, node):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node)
        if not isinstance(key, str):
            raise ValueError("YAML mapping keys must be strings")
        if key in result:
            raise ValueError(f"Duplicate YAML key: {key}")
        result[key] = loader.construct_object(value_node)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def validate_skill(directory):
    directory = Path(directory)
    source = directory / "SKILL.md"
    if directory.is_symlink() or source.is_symlink():
        raise ValueError("Evo import policy rejects symlinked skill roots or SKILL.md")
    raw = source.read_bytes()
    if len(raw) > 262144:
        raise ValueError("Evo import policy limits SKILL.md to 256 KiB")
    lines = raw.decode("utf-8").splitlines()
    if not lines or lines[0] != "---":
        raise ValueError("SKILL.md must start with YAML frontmatter")
    try:
        end = lines.index("---", 1)
    except ValueError as exc:
        raise ValueError("Missing closing frontmatter delimiter") from exc
    data = yaml.load("\n".join(lines[1:end]), Loader=UniqueLoader)
    if not isinstance(data, dict):
        raise ValueError("Frontmatter must be a mapping")
    name = data.get("name")
    if not isinstance(name, str) or not 1 <= len(name) <= 64:
        raise ValueError("name must be a string of 1-64 characters")
    if name.startswith("-") or name.endswith("-") or "--" in name:
        raise ValueError("name cannot have edge or consecutive hyphens")
    if not all(c == "-" or c.islower() or unicodedata.category(c) == "Nd" for c in name):
        raise ValueError("name must use lowercase letters, digits and hyphens")
    if name != directory.name:
        raise ValueError("name must match the skill directory name")
    for field, limit in (("description", 1024), ("compatibility", 500)):
        if field == "description" or field in data:
            value = data.get(field)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise ValueError(f"{field} must be a non-empty string up to {limit} characters")
    for field in ("license", "allowed-tools"):
        if field in data and not isinstance(data[field], str):
            raise ValueError(f"{field} must be a string")
    if "metadata" in data:
        meta = data["metadata"]
        if not isinstance(meta, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in meta.items()
        ):
            raise ValueError("metadata must map strings to strings")
    return {"name": name, "description": data["description"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    if args.root.is_symlink() or not args.root.is_dir():
        parser.exit(1, "Skill collection must be an existing non-symlink directory\n")
    directories = sorted(p for p in args.root.iterdir() if p.is_dir())
    if not directories:
        parser.exit(1, "No skill directories found\n")
    try:
        summaries = [validate_skill(p) for p in directories]
    except (OSError, ValueError, yaml.YAMLError) as exc:
        parser.exit(1, f"Skill validation failed: {exc}\n")
    print(json.dumps(summaries, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

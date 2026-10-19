"""Offline conformance checks for the Evo Agent Skills import profile."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location("skill_validator", ROOT / "tools/validate_skills.py")
validator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validator)


class SkillTests(unittest.TestCase):
    def check_document(self, text, name="test-skill"):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / name
            root.mkdir()
            (root / "SKILL.md").write_text(text, encoding="utf-8")
            return validator.validate_skill(root)

    def test_valid_metadata_only(self):
        result = self.check_document("---\nname: test-skill\ndescription: Test skill\n---\n")
        self.assertEqual(result, {"name": "test-skill", "description": "Test skill"})

    def test_optional_fields(self):
        self.check_document("---\nname: test-skill\ndescription: Test\nlicense: MIT\ncompatibility: Python\nallowed-tools: Read\nmetadata:\n  version: '1.0'\n---\n# Instructions\n")

    def test_invalid_cases(self):
        cases = [
            "name: test-skill\ndescription: Test",
            "---\nname: test-skill\ndescription: Test",
            "---\nname: Other\ndescription: Test\n---",
            "---\nname: wrong-name\ndescription: Test\n---",
            "---\nname: test-skill\n---",
            "---\nname: test-skill\ndescription: ''\n---",
            "---\nname: test-skill\ndescription: Test\nmetadata:\n  version: 1\n---",
            "---\nname: test-skill\nname: test-skill\ndescription: Test\n---",
            "---\nname: test-skill\ndescription: !!python/object:builtins.object {}\n---",
            "---\nname: test-skill\ndescription: Test\nallowed-tools: [Read]\n---",
            "---\nname: test-skill\ndescription: Test\ncompatibility: ''\n---",
            "---\nname: test-skill\ndescription: " + "x" * 1025 + "\n---",
        ]
        for text in cases:
            with self.subTest(text=text[:90]):
                with self.assertRaises((ValueError, yaml.YAMLError)):
                    self.check_document(text)

    def test_invalid_names(self):
        for name in ("-skill", "skill-", "two--hyphens", "UPPER", "x" * 65):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.check_document(f"---\nname: {name}\ndescription: Test\n---", name)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "test-skill"
            root.mkdir()
            target = Path(tmp) / "external.md"
            target.write_text("---\nname: test-skill\ndescription: Test\n---")
            (root / "SKILL.md").symlink_to(target)
            with self.assertRaises(ValueError):
                validator.validate_skill(root)

    def test_repository_skills(self):
        skills = list((ROOT / "capabilities/skills").iterdir())
        self.assertTrue(skills)
        for skill in skills:
            if skill.is_dir():
                validator.validate_skill(skill)


if __name__ == "__main__":
    unittest.main()

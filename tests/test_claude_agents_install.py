"""Verify that non-agent markdown files are never linked into ~/.claude/agents/."""
import contextlib
import io
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from claude_install import Installer, AGENT_SKIP_CORE, AGENT_SKIP_SYSTEM, MD_NO_LINK


class ClaudeAgentsInstallTest(unittest.TestCase):
    def test_no_non_agent_markdown_linked_core(self):
        with tempfile.TemporaryDirectory(prefix='claude-agents-') as temp:
            target = Path(temp) / 'claude'
            target.mkdir()
            installer = Installer(str(ROOT), str(target), [], False, False)
            installer.plan_core()
            with contextlib.redirect_stdout(io.StringIO()):
                for op in installer.ops:
                    installer.apply(op)

            agents_dir = target / 'agents'
            self.assertTrue(agents_dir.is_dir())

            linked_names = {p.name for p in agents_dir.iterdir()}

            # Non-agent markdown files must not be linked into agents directory
            forbidden = set(AGENT_SKIP_CORE) | set(MD_NO_LINK)
            self.assertTrue(forbidden.isdisjoint(linked_names),
                            f"Forbidden files found in agents dir: {forbidden & linked_names}")

            # Ensure actual agents are still linked (17 core agents)
            self.assertEqual(len(linked_names), 17)
            self.assertIn('code-reviewer.md', linked_names)
            self.assertIn('test-engineer.md', linked_names)

            # Every installed agent file should have valid markdown frontmatter
            for agent_file in agents_dir.iterdir():
                if agent_file.is_file() or agent_file.is_symlink():
                    content = agent_file.read_text(encoding='utf-8')
                    self.assertTrue(content.startswith('---'),
                                    f"Agent file {agent_file.name} missing frontmatter marker '---'")

    def test_no_non_agent_markdown_linked_with_systems(self):
        with tempfile.TemporaryDirectory(prefix='claude-agents-sys-') as temp:
            target = Path(temp) / 'claude'
            target.mkdir()
            # Test with available system bundles
            systems = ['gsd'] if (ROOT / 'systems/gsd').is_dir() else []
            installer = Installer(str(ROOT), str(target), systems, False, False)
            installer.plan_core()
            for s in systems:
                installer.plan_system(s)
            with contextlib.redirect_stdout(io.StringIO()):
                for op in installer.ops:
                    installer.apply(op)

            agents_dir = target / 'agents'
            self.assertTrue(agents_dir.is_dir())

            linked_names = {p.name for p in agents_dir.iterdir()}
            forbidden = set(AGENT_SKIP_CORE) | set(AGENT_SKIP_SYSTEM) | set(MD_NO_LINK)
            self.assertTrue(forbidden.isdisjoint(linked_names),
                            f"Forbidden files found in agents dir: {forbidden & linked_names}")


if __name__ == '__main__':
    unittest.main()

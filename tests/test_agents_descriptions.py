"""Generate AGENTS.md in a synthetic project using folded and literal YAML."""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DescriptionTest(unittest.TestCase):
    def test_generated_descriptions(self):
        with tempfile.TemporaryDirectory(prefix='agents-description-') as temp:
            home = Path(temp)
            repo = home / 'repo'
            adapter = repo / 'adapters/codex/install.sh'
            adapter.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / 'adapters/codex/install.sh', adapter)
            scripts = repo / 'scripts'
            scripts.mkdir()
            helper = ROOT / 'scripts/frontmatter-description.py'
            if helper.exists():
                shutil.copyfile(helper, scripts / helper.name)
            for name, header, expected in [
                ('literal', '|', 'Keep both lines'),
                ('folded', '>-', 'Fold these lines'),
                ('quoted', '"A colon: and a # mark"', 'A colon: and a # mark'),
                ('single', "'It''s one line'", "It's one line"),
            ]:
                path = repo / 'skills' / name / 'SKILL.md'
                path.parent.mkdir(parents=True)
                body = ('\n  Keep both\n  lines' if name == 'literal' else
                        '\n  Fold these\n  lines' if name == 'folded' else '')
                path.write_text('---\nname: ' + name + '\ndescription: ' + header + body + '\n---\n')
            agent = repo / 'agents/test.md'
            agent.parent.mkdir()
            agent.write_text('---\ndescription: |\n  An agent\n  description\n---\n')
            team = repo / 'systems/demo/front/SKILL.md'
            team.parent.mkdir(parents=True)
            team.write_text('---\nname: front-door\ndescription: >\n  A front\n  door\n---\n')
            rule = repo / 'rules/cursor-mdc/example.mdc'
            rule.parent.mkdir(parents=True)
            rule.write_text('---\ndescription: Example\n---\nUse verified facts.\n')
            output = home / 'project/AGENTS.md'
            output.parent.mkdir()
            result = subprocess.run([
                os.environ.get('BASH', '/bin/bash'), str(adapter), '--systems', 'demo',
                '-o', str(output)], cwd=output.parent,
                env=dict(os.environ, HOME=str(home), TMPDIR=str(home)),
                text=True, capture_output=True, timeout=15)
            self.assertEqual(result.returncode, 0, result.stderr)
            generated = output.read_text()
            for expected in ('Keep both lines', 'Fold these lines',
                             'A colon: and a # mark', "It's one line",
                             'An agent description', 'A front door'):
                self.assertIn(expected, generated)
            for line in generated.splitlines():
                self.assertNotIn(line.rsplit(' — ', 1)[-1], ('|', '>', '>-'))


if __name__ == '__main__':
    unittest.main()

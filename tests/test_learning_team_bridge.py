"""Tests for the Coco Learning System team feedback bridge."""

import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "systems", "learning", "scripts"))

from coco_learning.models import Observation
from coco_learning.storage import ensure_dirs, list_instincts
from coco_learning.team_bridge import (
    parse_team_feedback,
    ingest_team_feedback,
    get_role_domain,
    ROLE_DOMAIN_MAP,
)


class TestTeamBridge(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        os.environ["COCO_LEARNING_DIR"] = self.tmpdir
        self.project_id = "teamproj123456789"
        ensure_dirs(self.project_id)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)
        os.environ.pop("COCO_LEARNING_DIR", None)

    def test_role_domain_mapping(self):
        self.assertEqual(get_role_domain("code-reviewer"), "testing")
        self.assertEqual(get_role_domain("security-reviewer"), "security")
        self.assertEqual(get_role_domain("unknown-role"), "workflow")

    def test_parse_empty_feedback(self):
        obs = parse_team_feedback("code-reviewer", "", self.project_id)
        self.assertEqual(obs, [])

    def test_parse_testing_feedback(self):
        feedback = "You should always run tests before committing changes."
        obs = parse_team_feedback("test-guardian", feedback, self.project_id)
        self.assertGreater(len(obs), 0)
        self.assertEqual(obs[0].event, "TeamFeedback")
        self.assertEqual(obs[0].tool, "team:test-guardian")
        self.assertIn("test", obs[0].input_summary.lower())

    def test_parse_security_feedback(self):
        feedback = "This introduces a potential XSS vulnerability in the user input handler."
        obs = parse_team_feedback("code-reviewer", feedback, self.project_id)
        self.assertGreater(len(obs), 0)
        found_security = any("security" in o.output_summary.lower() for o in obs)
        self.assertTrue(found_security)

    def test_parse_performance_feedback(self):
        feedback = "The query performance is slow due to N+1 problem in the data loader."
        obs = parse_team_feedback("database-architect", feedback, self.project_id)
        self.assertGreater(len(obs), 0)

    def test_parse_multiple_patterns(self):
        feedback = """
        Critical issues:
        1. You must run tests after every schema change
        2. There's a security vulnerability with SQL injection
        3. Documentation needs updating for the new API
        """
        obs = parse_team_feedback("code-reviewer", feedback, self.project_id)
        self.assertGreaterEqual(len(obs), 3)

    def test_ingest_stores_observations(self):
        feedback = "Always run tests before merging PRs."
        result = ingest_team_feedback(
            "test-guardian", feedback, self.project_id, auto_evolve=False
        )
        self.assertGreater(result["observations_stored"], 0)
        self.assertEqual(result["instincts_detected"], 0)

    def test_ingest_with_auto_evolve(self):
        # Seed enough feedback to trigger pattern detection
        feedbacks = [
            "You should always run tests after code changes.",
            "Must run tests before deploying.",
            "Always run tests when modifying database schema.",
        ]
        total_obs = 0
        for fb in feedbacks:
            result = ingest_team_feedback(
                "test-guardian", fb, self.project_id, auto_evolve=True
            )
            total_obs += result["observations_stored"]

        self.assertGreater(total_obs, 0)
        # After multiple feedback entries, instincts may or may not be detected
        # depending on min_evidence threshold — just verify no crash
        instincts = list_instincts(self.project_id)
        self.assertIsInstance(instincts, list)

    def test_observation_project_id_set(self):
        feedback = "Should check error handling at API boundaries."
        obs = parse_team_feedback("code-reviewer", feedback, self.project_id)
        for o in obs:
            self.assertEqual(o.project_id, self.project_id)

    def test_all_mapped_roles_produce_valid_tool_names(self):
        for role in ROLE_DOMAIN_MAP:
            obs = parse_team_feedback(role, "should run tests always", self.project_id)
            for o in obs:
                self.assertTrue(o.tool.startswith("team:"))
                self.assertIn(role, o.tool)


if __name__ == "__main__":
    unittest.main()

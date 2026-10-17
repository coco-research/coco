"""Graders for the pilot skills: prd-generator, c4-architecture, writing-plans.

Each grader is a deterministic text check with no model and no network, and the answers
below are written by hand. For every grader the tests pin the same things: a good answer
scores full marks, an empty or irrelevant answer scores near zero, taking one ingredient out
of the good answer lowers the score by exactly its weight, every item in the file can be
answered perfectly, and the grader stays fast on runaway input.

    python3 -m unittest tests/test_skill_graders_docs.py -v
"""

import contextlib
import json
import pathlib
import re
import signal
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SKILLS = ROOT / "evals" / "skills"
sys.path.insert(0, str(SKILLS))

import run  # noqa: E402
import score  # noqa: E402

SPLIT_SIZE = 12
IRRELEVANT = "The weather is lovely today. Pancakes need flour, eggs and milk."


def squash(s):
    return " ".join(s.lower().split())


@contextlib.contextmanager
def deadline(seconds):
    """Fail instead of hanging when the block runs too long (Unix only; elsewhere no limit)."""
    if not hasattr(signal, "SIGALRM"):
        yield
        return

    def stop(signum, frame):
        raise AssertionError("still running after %d seconds" % seconds)

    old = signal.signal(signal.SIGALRM, stop)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


class PilotChecks:
    """Checks every pilot shares. A subclass sets skill, item_id, good, stub_mean, perfect and check_row."""

    skill = item_id = good = None

    @classmethod
    def setUpClass(cls):
        cls.path = SKILLS / cls.skill
        cls.items = {i["id"]: i for i in score.load_items(cls.path / "items.jsonl")}
        cls.grade = staticmethod(score.load_grader(cls.path / "grader.py"))
        cls.item = cls.items[cls.item_id]
        assert cls.item["split"] == "dev", "design graders against dev rows only"

    def result(self, output, item=None):
        return self.grade(item or self.item, output)

    def points(self, output, item=None):
        return self.result(output, item)["score"]

    def notes(self, output):
        return " | ".join(self.result(output)["notes"])

    def cut(self, *pieces):
        """The good answer with each piece removed. Fails if a piece is not in it."""
        text = self.good
        for piece in pieces:
            self.assertIn(piece, text, "fixture drifted")
            text = text.replace(piece, "")
        return text

    def swap(self, old, new):
        self.assertIn(old, self.good, "fixture drifted")
        return self.good.replace(old, new)

    def test_items_file_is_well_formed(self):
        lines = [l for l in (self.path / "items.jsonl").read_text().splitlines() if l.strip()]
        ids = [json.loads(l)["id"] for l in lines]
        self.assertEqual(len(ids), len(set(ids)), "duplicate id")
        rows = list(self.items.values())
        self.assertEqual(len(rows), 2 * SPLIT_SIZE)
        self.assertEqual(len({r["input"] for r in rows}), len(rows), "two rows share an input")
        for split in ("dev", "heldout"):
            self.assertEqual(sum(r["split"] == split for r in rows), SPLIT_SIZE, split)
        for row in rows:
            self.assertTrue(row["id"] and isinstance(row["id"], str))
            self.assertTrue(row["input"].strip() and isinstance(row["input"], str))
            self.check_row(row)

    def test_good_answer_scores_full_marks(self):
        # The requirement is at least 0.9. The fixtures earn all of it so the exact deltas below mean something.
        result = self.result(self.good)
        self.assertEqual((result["score"], result["notes"]), (1.0, []))

    def test_every_item_can_score_full_marks(self):
        for row in self.items.values():
            result = self.result(self.perfect(row), row)
            self.assertEqual(result["score"], 1.0, (row["id"], result["notes"]))

    def test_empty_and_irrelevant_answers_score_near_zero(self):
        for output in ("", "   \n\t\n", IRRELEVANT, None):
            self.assertLessEqual(self.points(output), 0.1, repr(output))

    def test_degenerate_input_stays_fast(self):
        # A looping model can emit tens of kilobytes of one repeated token. Each input below
        # takes minutes if a pattern backtracks badly; a linear grader takes well under a second.
        nasty = (
            "\n" * 100000, " \n" * 50000, "**" + " " * 5000, "# " * 20000, "[" * 50000, "{" * 50000,
            ("given when " * 25 + "\n") * 200, "1. a\n2. b\n3. c\n" + "\n" * 20000,
            "```mermaid\ngraph TD\n-- " + " " * 5000 + "x\n```",
            "```mermaid\ngraph TD\nA[" + " " * 4000 + "x\n```",
            "```mermaid\ngraph TD\nA[" + ")" * 20000 + "x\n```",
            "```mermaid\n" + "A --> " * 20000 + "\n```",
        )
        for text in nasty:
            with deadline(5):
                score._check_result("x", self.result(text))

    def test_only_the_first_200k_characters_are_read(self):
        self.assertLessEqual(self.points("x " * 100000 + self.good), 0.1)

    def test_both_splits_score_under_the_stub_executor(self):
        # The stub answers with the brief itself, so this is the score of an answer that only repeats it.
        for split in ("dev", "heldout"):
            record = score.score_run(
                self.skill, split, "stub", self.path / "items.jsonl", self.path / "grader.py",
                ROOT / "skills" / self.skill / "SKILL.md",
                model=None, seed=0, url=run.DEFAULT_URL,
            )
            self.assertEqual(record["n"], SPLIT_SIZE)
            self.assertAlmostEqual(record["mean"], self.stub_mean)
            self.assertEqual("outputs" in record, split == "dev")


class PrdGeneratorTest(PilotChecks, unittest.TestCase):
    skill, item_id, stub_mean = "prd-generator", "pr01", 0.4
    good = """# Ledgerly Theme Scheduler

## Problem Statement

Night-shift nurses read notes between 2am and 6am. Today the app only offers a manual light/dark toggle, and users complain about eye strain.

## Goals and Success Metrics

- Cut theme-related support tickets by 40% within one quarter of launch.
- Track theme-related support tickets per week against the pre-launch baseline.

## User Stories and Requirements

1. As a nurse on nights, I want to set a start time and an end time for the dark theme, so that the screen is easy on my eyes.
2. As a user with no schedule, I want the app to follow the system theme.
3. As a user with low vision, I want the scheduler to respect reduce-motion and high-contrast settings.

Only two schedule slots per account are allowed.

### Acceptance Criteria

- [ ] Given a schedule from 22:00 to 06:00, when the clock reaches 22:00, then the app switches to the dark theme.
- [ ] Given no schedule is set, when the device theme changes, then the app follows the system theme.
- [ ] Given two slots exist, when a user adds a third, then the app explains the limit.

## Out of Scope

- Per-note themes.
- Syncing schedules across devices.
"""
    headings = {
        "problem or overview": "## Problem Statement\n",
        "goals or success metrics": "## Goals and Success Metrics\n",
        "requirements or user stories": "## User Stories and Requirements\n",
        "acceptance criteria": "### Acceptance Criteria\n",
        "out of scope": "## Out of Scope\n",
    }
    synonyms = {
        "problem or overview": (
            "Overview", "Executive Summary", "Background", "Context", "Motivation", "Introduction", "Purpose",
            "Vision", "Rationale"),
        "goals or success metrics": ("Objectives", "Success Criteria", "Metrics", "KPIs", "OKRs"),
        "requirements or user stories": ("Functional Requirements", "Story 1", "Use Cases"),
        "acceptance criteria": ("Definition of Done",),
        "out of scope": (
            "Non-Goals", "Not in Scope", "Exclusions", "Deferred", "Future Work", "What we are not building"),
    }

    @staticmethod
    def perfect(row):
        facts = "\n".join("- " + f for f in row["facts"])
        return (
            "## Problem Statement\n%s\n\n## Goals and Success Metrics\n- Measure it.\n\n"
            "## User Stories and Requirements\n1. As a user, I want the feature.\n\n"
            "### Acceptance Criteria\n- [ ] Given a, when b, then c.\n\n## Out of Scope\n- Later.\n" % facts
        )

    def check_row(self, row):
        self.assertTrue(row["facts"] and isinstance(row["facts"], list))
        for fact in row["facts"]:
            self.assertIn(squash(fact), squash(row["input"]), "fact is not in the brief")

    def missing(self, text):
        """The required parts the grader reports as missing from text."""
        for note in self.result(text)["notes"]:
            if note.startswith("missing sections: "):
                return note[len("missing sections: "):].split(", ")
        return []

    def test_each_required_section_matters(self):
        top = self.points(self.good)
        for part, heading in self.headings.items():
            output = self.cut(heading)
            self.assertEqual(self.points(output), round(top - 0.4 / 5, 4), part)
            self.assertEqual(self.missing(output), [part])

    def test_heading_synonyms_and_styles_are_accepted(self):
        top = self.points(self.good)
        for heading, other in (
            ("## Problem Statement", "1. Background"),
            ("## Goals and Success Metrics", "**Objectives:**"),
            ("## User Stories and Requirements", "Requirements:"),
            ("### Acceptance Criteria", "**Acceptance criteria**"),
            ("## Out of Scope", "## Non-Goals"),
        ):
            self.assertEqual(self.points(self.swap(heading, other)), top, other)

    def test_every_listed_synonym_earns_its_part(self):
        for part, names in self.synonyms.items():
            for name in names:
                self.assertNotIn(part, self.missing("## %s\n- one two three four\n" % name), name)

    def test_acceptance_criteria_need_content(self):
        bare = re.sub(r"(?m)^- \[ \] .*\n", "", self.good)
        self.assertNotIn("Given", bare)
        self.assertEqual(self.points(bare), round(self.points(self.good) - 0.2 - 0.4 / 5, 4))
        self.assertEqual(self.missing(bare), ["acceptance criteria"])
        self.assertIn("no acceptance criteria", self.notes(bare))

    def test_acceptance_criteria_forms(self):
        found = (
            "Acceptance criteria:\n- The theme switches at the start time\n",
            "As a nurse, I want a schedule.\n- [ ] The theme switches at the start time\n",
            "Given a schedule, when the clock reaches the start time, then the theme switches.",
            "Given a schedule\nWhen the clock reaches the start time\nThen the theme switches",
        )
        absent = (
            "Acceptance criteria:\n\n## Out of Scope\n- one two three four",
            "**Acceptance Criteria**\n\n**Out of Scope**\n- one two three four",
            "Acceptance criteria: TBD",
            "- [ ] a lone checkbox",
            "Given the budget, we will ship, then iterate.",
            "Then it ships, when ready, given the plan.",
            "We are given a budget when planning and then ship.",
        )
        for text in found:
            self.assertNotIn("no acceptance criteria", self.notes(text), text)
        for text in absent:
            self.assertIn("no acceptance criteria", self.notes(text), text)

    def test_a_heading_needs_content(self):
        text = "\n".join("## " + h for h in ("Problem", "Goals", "Requirements", "Acceptance Criteria", "Out of Scope"))
        self.assertEqual(self.points(text), 0.0)
        self.assertEqual(sorted(self.missing(text)), sorted(self.headings))
        self.assertNotIn("out of scope", self.missing("Out of scope: bulk approvals\n"))  # two words after the label
        self.assertIn("out of scope", self.missing("Out of scope: bulk\n"))
        self.assertNotIn("problem or overview", self.missing("## Problem\nExactly three words\n"))
        self.assertIn("problem or overview", self.missing("## Problem\nOnly two\n"))
        self.assertNotIn("goals or success metrics", self.missing("## Goals\n### Business goals\n- cut tickets\n"))
        self.assertIn("problem or overview", self.missing("## Problem\n### Background and context here\n"))

    def test_one_heading_can_earn_two_parts_and_a_bare_scope_earns_none(self):
        both = self.missing("## Goals and Non-Goals\n- cut theme-related support tickets by 40%\n- no per-note themes\n")
        self.assertNotIn("goals or success metrics", both)
        self.assertNotIn("out of scope", both)
        alone = self.missing("## Non-Goals\n- one two three four\n")
        self.assertIn("goals or success metrics", alone)
        self.assertNotIn("out of scope", alone)
        self.assertIn("out of scope", self.missing("## Scope\n- only two schedule slots per account\n"))
        self.assertIn("out of scope", self.missing("- Scope limit: only two schedule slots per account.\n"))

    def test_the_document_title_earns_no_section(self):
        text = "# Product Requirements Document\nA short description of the whole thing.\n"
        self.assertIn("requirements or user stories", self.missing(text))

    def test_links_and_numbered_sentences_are_not_headings(self):
        contents = "1. [Problem Statement](#problem)\n2. [Goals](#goals)\n3. [Requirements](#req)\n4. [Out of Scope](#oos)\n"
        sentences = (
            "1. The goal is to cut tickets by half.\n2. Success metrics are tickets per week.\n"
            "3. Out of scope items are listed later, in the notes.\n4. Requirements are listed below.\n"
        )
        for text in (contents, sentences):
            self.assertEqual(len(self.missing(text)), 5, text)

    def test_each_lost_fact_lowers_the_score(self):
        top = self.points(self.good)
        for fact in self.item["facts"]:
            output = re.sub(re.escape(fact), "something else", self.good, flags=re.I)
            self.assertEqual(self.points(output), round(top - 0.4 / 5, 4), fact)
            self.assertIn(fact, self.notes(output))

    def test_facts_ignore_case_spacing_dashes_and_emphasis(self):
        top = self.points(self.good)
        for old, new in (
            ("Night-shift nurses", "NIGHT‑SHIFT   NURSES"),
            ("Night-shift nurses", "Night–shift nurses"),
            ("Night-shift nurses", "Night—shift nurses"),
            ("Night-shift nurses", "Night‐shift nurses"),
            ("Night-shift nurses", "Night−shift nurses"),
            ("by 40%", "by **40%**"),
            ("by 40%", "by __40%__"),
            ("system theme", "system\n theme"),
            ("Syncing schedules", "`Syncing` schedules"),
            ("Syncing schedules", "_Syncing_ schedules"),
        ):
            self.assertEqual(self.points(self.swap(old, new)), top, new)

    def test_typographic_quotes_match_straight_quotes(self):
        item = {"id": "x", "split": "dev", "input": "", "facts": ["the user's \"note\""]}
        self.assertEqual(self.points("the user’s “note”", item), 0.4)

    def test_placeholders_cost_a_tenth_each(self):
        top = self.points(self.good)
        for text, count in (
            ("Timeline: TBD", 1),
            ("TODO: size this", 1),
            ("TBC and FIXME", 2),
            ("TBD and TBD again", 2),
            ("Owner to be determined", 1),
            ("Owner to be decided, size to be defined", 2),
            ("Lorem ipsum dolor", 1),
            ("Name: {{owner}}", 1),
            ("As a [user type], I want to [action]", 2),
        ):
            self.assertEqual(self.points(self.good + "\n" + text + "\n"), round(top - 0.1 * count, 4), text)
        self.assertEqual(self.points("TBD " * 40), 0.0)

    def test_ordinary_brackets_and_words_are_not_placeholders(self):
        extra = (
            "\n[Design notes](https://example.com/n) tracks the todo list screen. See [1], [P0], [PRD-12], [Must Have],"
            ' [MVP] and items[index]. Roles: ["admin", "editor"]. See [Design notes][1]. Show a placeholder when empty.\n'
        )
        self.assertEqual(self.points(self.good + extra), self.points(self.good))

    def test_fractions_follow_the_items_own_counts(self):
        item = {"id": "x", "split": "dev", "input": "", "facts": ["alpha kilo", "beta lima", "gamma mike"]}
        self.assertEqual(self.points(self.perfect({"facts": ["alpha kilo", "beta lima"]}), item), 0.8667)


class C4ArchitectureTest(PilotChecks, unittest.TestCase):
    skill, item_id, stub_mean = "c4-architecture", "c401", 0.0
    good = """Here is the container diagram.

```mermaid
C4Container
  title Container Diagram - GreenGrid

  Person(grower, "Grower", "Logs plots")

  Container_Boundary(greengrid, "GreenGrid") {
    Container(web, "Web App", "React", "Lets growers log plots")
    Container(api, "API Service", "Node.js", "Reads and writes plot data")
    ContainerDb(db, "Farms DB", "PostgreSQL", "Plot and harvest records")
    ContainerQueue(queue, "Message Queue", "RabbitMQ", "Harvest events")
    Container(worker, "Notification Worker", "Python", "Emails subscribers")
    Container(scheduler, "Scheduler Service", "Cron", "Nightly jobs")
  }

  Rel(grower, web, "Uses")
  Rel(web, api, "Calls", "JSON/HTTPS")
  Rel(api, db, "Stores plot and harvest records in", "SQL")
  Rel(api, queue, "Publishes harvest events to")
  Rel(queue, worker, "Delivers events to")
  Rel(scheduler, db, "Writes summaries into", "SQL")
```

The queue keeps the worker decoupled from the API.
"""
    flowchart = """```mermaid
flowchart LR
  Web[Web App] -->|calls| API[API Service]
  API --> DB[(Farms DB)]
  API -->|events| Q([Message Queue])
  Q --> W[Notification Worker]
  S[Scheduler Service] -- writes --> DB
```"""
    relation_lines = {
        ("Web App", "API Service"): '  Rel(web, api, "Calls", "JSON/HTTPS")\n',
        ("API Service", "Farms DB"): '  Rel(api, db, "Stores plot and harvest records in", "SQL")\n',
        ("API Service", "Message Queue"): '  Rel(api, queue, "Publishes harvest events to")\n',
        ("Message Queue", "Notification Worker"): '  Rel(queue, worker, "Delivers events to")\n',
        ("Scheduler Service", "Farms DB"): '  Rel(scheduler, db, "Writes summaries into", "SQL")\n',
    }

    @staticmethod
    def perfect(row):
        alias = {name: "c%d" % i for i, name in enumerate(row["containers"])}
        lines = ["```mermaid", "C4Container"]
        lines += ['  Container(%s, "%s", "Tech", "Role")' % (a, n) for n, a in alias.items()]
        lines += ['  Rel(%s, %s, "Uses")' % (alias[a], alias[b]) for a, b in row["relations"]]
        return "\n".join(lines + ["```"])

    def check_row(self, row):
        names, pairs = row["containers"], row["relations"]
        self.assertTrue(names and isinstance(names, list))
        for name in names:
            self.assertIn(squash(name), squash(row["input"]), "container is not in the description")
        self.assertTrue(pairs and isinstance(pairs, list))
        for pair in pairs:
            self.assertIsInstance(pair, list)
            self.assertEqual(len(pair), 2)
            for end in pair:
                self.assertIn(end, names, "relation end is not a listed container")

    def test_fixture_covers_every_item_relation(self):
        self.assertEqual({tuple(p) for p in self.item["relations"]}, set(self.relation_lines))

    def test_no_mermaid_block_scores_zero_with_a_note(self):
        result = self.result('C4Container\nContainer(web, "Web App")\n')
        self.assertEqual((result["score"], result["notes"]), (0.0, ["no mermaid block"]))

    def test_each_relation_matters(self):
        top = self.points(self.good)
        for pair, line in self.relation_lines.items():
            output = self.cut(line)
            self.assertEqual(self.points(output), round(top - 0.4 / 5, 4), pair)
            self.assertIn(" -> ".join(pair), self.notes(output))

    def test_each_container_matters(self):
        top = self.points(self.good)
        for name in self.item["containers"]:
            touching = sum(name in pair for pair in self.item["relations"])
            output = self.swap('"%s"' % name, '"Something Else"')
            self.assertEqual(self.points(output), round(top - 0.4 / 6 - 0.4 * touching / 5, 4), name)
            self.assertIn(name, self.notes(output))

    def test_extra_elements_and_relations_cost_nothing(self):
        extra = self.swap(
            "  Rel(grower, web",
            '  System_Ext(mail, "Mail Relay", "SMTP")\n  Rel(worker, mail, "Sends email through")\n  Rel(grower, web',
        )
        self.assertEqual(self.points(extra), self.points(self.good))

    def test_direction_case_and_punctuation_do_not_matter(self):
        top = self.points(self.good)
        for old, new in (
            ("Rel(web, api,", "Rel(api, web,"),
            ('"Web App"', '"web-app (React SPA)"'),
            ('"Farms DB"', '"FARMS DB!"'),
            ('"Message Queue"', '"The Message Queue"'),
        ):
            self.assertEqual(self.points(self.swap(old, new)), top, new)

    def test_relationship_and_element_forms(self):
        top = self.points(self.good)
        for old, new in (
            ("Rel(web, api,", "Rel_D(web, api,"),
            ("Rel(web, api,", "Rel_Up(web, api,"),
            ("Rel(web, api,", "BiRel(web, api,"),
            ("C4Container\n", "C4Component\n"),
            ("C4Container\n", "C4Context\n"),
            ("C4Container\n", "C4Dynamic\n"),
            ("C4Container\n", "C4Deployment\n"),
            ('Person(grower, "Grower"', 'Person_Ext(grower, "Grower"'),
            ('Container(web, "Web App"', 'Container_Ext(web, "Web App"'),
            ('Container(api, "API Service"', 'Component(api, "API Service"'),
            ('ContainerDb(db, "Farms DB"', 'SystemDb(db, "Farms DB"'),
            ('ContainerQueue(queue, "Message Queue"', 'ComponentQueue(queue, "Message Queue"'),
            ('Container(worker, "Notification Worker"', 'System_Ext(worker, "Notification Worker"'),
        ):
            self.assertEqual(self.points(self.swap(old, new)), top, new)

    def test_one_catch_all_element_cannot_stand_in_for_several_containers(self):
        blob = (
            "```mermaid\nC4Container\n"
            'Container(all, "Web App API Service Farms DB Message Queue Notification Worker Scheduler Service")\n'
            'Rel(all, all, "everything")\n```'
        )
        self.assertLessEqual(self.points(blob), 0.3)
        self.assertIn("containers found 1/6", self.notes(blob))

    def test_longer_shorter_and_plural_labels_match_but_tiny_ones_do_not(self):
        def diagram(first, second):
            return '```mermaid\nC4Container\nContainer(a, "%s")\nContainer(b, "%s")\nRel(a, b, "Calls")\n```' % (first, second)

        exact = self.points(diagram("Web App", "Notification Worker"))
        self.assertEqual(self.points(diagram("Web Application", "Notification Workers")), exact)  # contain the name
        self.assertEqual(self.points(diagram("Web App", "Notification")), exact)  # inside the name
        self.assertIn("containers found 1/6", self.notes(diagram("Web App", "DB")))  # too short to match 'Farms DB'

    def test_exact_labels_win_before_substrings(self):
        item = {
            "containers": ["Queue", "Message Queue", "Worker Node"],
            "relations": [["Message Queue", "Worker Node"]],
        }
        text = (
            '```mermaid\nC4Container\nContainer(a, "Message Queue")\nContainer(b, "Queue")\n'
            'Container(w, "Worker Node")\nRel(a, w, "Feeds")\n```'
        )
        self.assertEqual(self.points(text, item), 1.0)

    def test_invalid_c4_loses_the_validity_credit(self):
        top = self.points(self.good)
        no_header = self.swap("C4Container\n", "")
        self.assertEqual(self.points(no_header), round(top - 0.2, 4))
        for output in (
            no_header,
            self.swap("Rel(queue, worker,", "Rel(queue, ghost,"),
            self.swap("Rel(queue, worker,", "Rel(ghost, worker,"),
            self.swap("  }\n", ""),
        ):
            self.assertLess(self.points(output), top)
            self.assertIn("C4 block problem", self.notes(output))
        self.assertIn("one relationship", self.notes('```mermaid\nC4Container\nContainer(a, "Web App")\n```'))

    def test_a_relationship_to_a_boundary_is_flagged_and_earns_nothing(self):
        text = (
            '```mermaid\nC4Container\nContainer_Boundary(web, "Web App") {\n  Container(ui, "UI Layer", "React")\n}\n'
            'Container_Boundary(api, "API Service") {\n  Container(h, "Handlers", "Go")\n}\n'
            'ContainerDb(db, "Farms DB", "PostgreSQL")\nRel(web, api, "Calls")\nRel(api, db, "Stores")\n```'
        )
        self.assertLessEqual(self.points(text), 0.1)
        self.assertIn("boundary", self.notes(text))
        self.assertNotIn("undefined alias", self.notes(text))
        self.assertIn("undefined alias: ghost", self.notes(self.swap("Rel(queue, worker,", "Rel(queue, ghost,")))

    def test_a_person_is_not_a_container(self):
        text = '```mermaid\nC4Container\nPerson(u, "Web App")\nContainer(a, "API Service")\nRel(u, a, "Uses")\n```'
        self.assertIn("containers found 1/6, missing: Web App", self.notes(text))

    def test_frontmatter_and_directives_before_the_keyword_are_skipped(self):
        head = '---\ntitle: GreenGrid\n---\n%%{init: {"theme": "dark"}}%%\n'
        self.assertEqual(self.points(self.swap("```mermaid\n", "```mermaid\n" + head)), self.points(self.good))

    def test_a_c4_block_whose_macros_do_not_parse_is_not_read_as_a_flowchart(self):
        text = '```mermaid\nC4Container\nContainerSvc(web, "Web App")\nContainerSvc(api, "API Service")\nRel(web, api, "Calls")\n```'
        self.assertEqual(self.points(text), 0.0)
        self.assertNotIn("not C4 syntax", self.notes(text))

    def test_flowchart_edge_forms_are_all_read(self):
        # Two edges between three of the six containers: 0.4 * 3/6 + 0.4 * 2/5, below the cap.
        def flow(first, second):
            return "```mermaid\nflowchart LR\n  W[Web App] %s A[API Service]\n  A %s D[(Farms DB)]\n```" % (first, second)

        arrows = (
            "-->", "---", "-.->", "==>", "--o", "--x", "<-->", "-->|calls|", "-- calls -->", "-- read-write -->",
            "-- calls (HTTPS) -->", "--calls-->", "-. x .->", "== x ==>",
        )
        for arrow in arrows:
            self.assertEqual(self.points(flow(arrow, arrow)), 0.36, arrow)
        chained = "```mermaid\ngraph TD\n  W[Web App] --> A[API Service] --> D[(Farms DB)]\n```"
        semicolon = "```mermaid\ngraph TD\n  W[Web App] --> A[API Service]; A --> D[(Farms DB)]\n```"
        fan_out = "```mermaid\ngraph TD\n  W[Web App] --> A[API Service]\n  A --> D[(Farms DB)] & Q[Message Queue]\n```"
        self.assertEqual(self.points(chained), 0.36)
        self.assertEqual(self.points(semicolon), 0.36)
        self.assertEqual(self.points(fan_out), 0.5067)

    def test_flowchart_gets_credit_but_is_capped_at_seven_tenths(self):
        result = self.result(self.flowchart)
        self.assertEqual(result["score"], 0.7)
        self.assertIn("capped at 0.7", " ".join(result["notes"]))
        smaller = self.flowchart.replace("  Q --> W[Notification Worker]\n", "").replace(
            "  S[Scheduler Service] -- writes --> DB\n", "")
        self.assertEqual(self.points(smaller), 0.5067)

    def test_best_block_counts(self):
        context = '```mermaid\nC4Context\n  Person(u, "User")\n  System(s, "GreenGrid")\n  Rel(u, s, "Uses")\n```\n'
        top = self.points(self.good)
        self.assertEqual(self.points(context + self.good), top)
        self.assertEqual(self.points(self.good + context), top)

    def test_windows_line_ends_a_capitalised_fence_and_a_missing_closing_fence_still_parse(self):
        top = self.points(self.good)
        text = self.good[: self.good.index("```\n\nThe queue")].replace("\n", "\r\n")
        self.assertEqual(self.points(text), top)
        self.assertEqual(self.points(self.swap("```mermaid", "```Mermaid")), top)

    def test_fractions_follow_the_items_own_counts(self):
        item = {
            "containers": ["Alpha Hub", "Beta Store", "Gamma Queue"],
            "relations": [["Alpha Hub", "Beta Store"], ["Beta Store", "Gamma Queue"]],
        }
        short = self.perfect({"containers": ["Alpha Hub", "Beta Store"], "relations": [["Alpha Hub", "Beta Store"]]})
        self.assertEqual(self.points(short, item), 0.6667)


class WritingPlansTest(PilotChecks, unittest.TestCase):
    skill, item_id, stub_mean = "writing-plans", "wp01", 0.8
    good = """I'm using the writing-plans skill to create the implementation plan.

# Discount Stacking Implementation Plan

**Goal:** Stack percentage and flat discounts in a fixed, deterministic order.

**Files:**
- Modify: `src/cart/total.py`
- Test: `tests/test_total.py`
- Docs: `docs/cart.md`

### Task 1: Ordering and the clamp

- [ ] **Step 1: Write the failing tests**

In `tests/test_total.py`, add a test that applies a 100 percent discount plus a flat discount and expects 0.00.

- [ ] **Step 2: Run the tests to verify they fail**

Run: `python -m pytest tests/test_total.py -v`
Expected: FAIL

- [ ] **Step 3: Implement the stacking order**

In `src/cart/total.py`, apply percentage discounts first and flat discounts second. Clamp the result at 0.00 and keep returning a Decimal.
Keep the existing `apply_discount` function name and signature so callers in `src/cart/checkout.py` need no edits.
Add type hints to any new helper. Log a warning when stacked discounts exceed the subtotal. Leave the rounding helper in `src/cart/money.py` alone.

- [ ] **Step 4: Run the tests to verify they pass**

Run: `python -m pytest tests/test_total.py -v`
Expected: PASS

- [ ] **Step 5: Update the docs**

Update `docs/cart.md` to describe the stacking order.

- [ ] **Step 6: Commit**

```bash
git add src/cart/total.py tests/test_total.py docs/cart.md
git commit -m "feat: stack percentage and flat discounts"
```
"""
    steps = "1. a\n2. b\n3. c\n"

    @staticmethod
    def perfect(row):
        paths = re.findall(r"[\w.-]+(?:/[\w.-]+)+\.\w+", row["input"])
        steps = ["%d. %s" % (i, req) for i, req in enumerate(row["requirements"], 1)]
        return "\n".join(steps + ["Run pytest " + paths[0], "Files: " + ", ".join(paths)])

    def check_row(self, row):
        self.assertTrue(row["requirements"] and isinstance(row["requirements"], list))
        for req in row["requirements"]:
            self.assertIn(squash(req), squash(row["input"]), "requirement is not in the spec")
        self.assertTrue(re.search(r"\w+/[\w./-]+\.\w+", row["input"]), "spec names no file path")

    def covers(self, requirement, plan):
        """True when plan, with three steps and nothing else to earn, covers the one requirement."""
        item = {"id": "x", "split": "dev", "input": "", "requirements": [requirement]}
        return abs(self.points(self.steps + plan, item) - 0.7) < 1e-9

    def test_dropping_a_requirement_lowers_the_score(self):
        output = self.cut("Clamp the result at 0.00 and ", " and expects 0.00")
        self.assertEqual(self.points(output), round(self.points(self.good) - 0.5 / 5, 4))
        self.assertIn("clamped at 0.00", self.notes(output))

    def test_a_requirement_is_covered_at_sixty_percent_of_its_content_words(self):
        five, seven = "alpha beta gamma delta epsilon", "alpha beta gamma delta epsilon zeta theta"
        self.assertTrue(self.covers(five, "alpha beta gamma"))  # 3 of 5
        self.assertFalse(self.covers(five, "alpha beta"))  # 2 of 5
        self.assertFalse(self.covers(seven, "alpha beta gamma delta"))  # 4 of 7 is 57%
        self.assertTrue(self.covers(seven, "alpha beta gamma delta epsilon"))  # 5 of 7

    def test_stopwords_are_ignored_and_word_endings_fold_together(self):
        self.assertTrue(self.covers("the retries are recorded", "record each retry"))
        for plural, base in (
            ("retries", "retry"), ("recorded", "record"), ("returns", "return"), ("mutating", "mutate"),
            ("files", "file"), ("logs", "log"),
        ):
            self.assertTrue(self.covers(plural, base), plural)

    def test_number_words_equal_digits(self):
        for word, digits in (
            ("zero", "0"), ("three", "3"), ("fifteen", "15"), ("twenty", "20"), ("ninety", "90"), ("hundred", "100"),
        ):
            self.assertTrue(self.covers(word, digits), word)

    def test_each_other_ingredient_matters(self):
        top = self.points(self.good)
        no_steps = re.sub(r"(?m)^- \[ \] \*\*Step \d+: (.*)\*\*$", r"**\1**", self.good).replace("### Task 1:", "###")
        no_test = self.good.replace("pytest", "the runner").replace("tests/test_total.py", "the test module")
        no_files = self.good.replace("src/", "lib/").replace("tests/", "spec/").replace("docs/", "doc/")
        for label, output, drop in (("steps", no_steps, 0.2), ("test step", no_test, 0.15), ("files", no_files, 0.15)):
            self.assertNotEqual(output, self.good, label)
            self.assertEqual(self.points(output), round(top - drop, 4), label)

    def test_step_markers(self):
        for text in (
            "1. A\n2. B\n3. C\n", "1) A\n2) B\n3) C\n", "  1. A\n  2. B\n  3. C\n", "### 1. A\n### 2. B\n### 3. C\n",
            "**1.** A\n**2.** B\n**3.** C\n", "1.1 A\n1.2 B\n1.3 C\n", "- [x] A\n- [ ] B\n- [ ] C\n",
            "Step 1: A\nStep 2: B\nStep 3: C\n", "### Task 1\n### Task 2\n### Task 3\n", "STEP 1 A\nSTEP 2 B\nSTEP 3 C\n",
        ):
            self.assertNotIn("step(s)", self.notes(text), text)
        self.assertIn("2 step(s)", self.notes("1. A\n2. B\n"))

    def test_one_spec_path_is_enough_and_an_invented_path_is_not(self):
        self.assertNotIn("file paths", self.notes(self.steps + "src/cart/total.py"))
        self.assertNotIn("file paths", self.notes(self.steps + "SRC/CART/TOTAL.PY"))
        self.assertIn("file paths", self.notes(self.steps + "src/foo/bar.py and docs/other.md"))

    def test_each_ingredient_has_its_own_note(self):
        notes = self.notes("Nothing here.")
        for needle in ("step(s)", "test command", "file paths", "requirements covered 0/5"):
            self.assertIn(needle, notes)

    def test_test_commands_and_test_files_are_recognised(self):
        for text in (
            "pytest -q", "py.test x", "python -m unittest", "npm test", "npm run test", "yarn test", "pnpm test",
            "make test", "go test ./...", "cargo test", "mvn test", "gradle test", "jest", "vitest run", "mocha",
            "rspec", "phpunit", "ctest", "tox", "nosetests", "run tests/test_total.py", "test_total.py",
            "total_test.go", "total.spec.ts", "total.test.js",
        ):
            self.assertNotIn("no test command", self.notes(text), text)
        for text in ("write some tests", "the test module"):
            self.assertIn("no test command", self.notes(text), text)

    def test_fractions_follow_the_items_own_counts(self):
        item = {"id": "x", "split": "dev", "input": "", "requirements": ["alpha kilo", "beta lima", "gamma mike"]}
        self.assertEqual(self.points("1. alpha kilo\n2. beta lima\n3. c", item), 0.5333)


if __name__ == "__main__":
    unittest.main()

"""Verification Gate Service -- reusable quality gates for workflows and self-improve cycles.

Gates:
  G1 (Ideation)       -- Is the idea well-formed? Does it solve a real problem?
  G2 (Plan)           -- Is the plan complete? Are dependencies identified?
  G3 (Implementation) -- Does the code work? Do tests pass? Security clean?
  G4 (Acceptance)     -- Does it meet the original requirements? Ready to ship?
"""
import fnmatch
import json
import time
import uuid
import structlog
from datetime import datetime, timezone
from dataclasses import dataclass, field
from enum import Enum
from sqlalchemy import insert
from app.db.session import get_db
from app.db.tables import verification_gates, verification_results

log = structlog.get_logger()


class GateName(str, Enum):
    IDEATION = "G1_ideation"
    PLAN = "G2_plan"
    IMPLEMENTATION = "G3_implementation"
    ACCEPTANCE = "G4_acceptance"


class GateVerdict(str, Enum):
    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"


@dataclass
class GateCheck:
    """Individual check within a gate."""
    name: str
    passed: bool
    message: str
    severity: str = "error"


@dataclass
class GateResult:
    """Result of running a verification gate."""
    gate: str
    verdict: GateVerdict
    checks: list[GateCheck] = field(default_factory=list)
    summary: str = ""
    run_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    duration_ms: int = 0
    retry_count: int = 0

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "verdict": self.verdict.value,
            "checks": [{"name": c.name, "passed": c.passed, "message": c.message, "severity": c.severity} for c in self.checks],
            "summary": self.summary,
            "run_at": self.run_at,
            "duration_ms": self.duration_ms,
            "retry_count": self.retry_count,
        }


class VerificationService:
    """Runs verification gates against workflow artifacts."""

    def run_gate(self, gate_name: str, input_data: dict, output_data: dict,
                 node_id: str | None = None, entity_type: str | None = None,
                 entity_id: str | None = None) -> GateResult:
        start = time.monotonic()
        gate = GateName(gate_name)

        if gate == GateName.IDEATION:
            result = self._check_ideation(input_data, output_data)
        elif gate == GateName.PLAN:
            result = self._check_plan(input_data, output_data)
        elif gate == GateName.IMPLEMENTATION:
            result = self._check_implementation(input_data, output_data)
        elif gate == GateName.ACCEPTANCE:
            result = self._check_acceptance(input_data, output_data)
        else:
            result = GateResult(gate=gate_name, verdict=GateVerdict.FAIL,
                                summary=f"Unknown gate: {gate_name}")

        result.duration_ms = int((time.monotonic() - start) * 1000)
        self._persist_result(result, node_id, entity_type, entity_id)
        return result

    def _check_ideation(self, input_data: dict, output_data: dict) -> GateResult:
        checks = []

        title = output_data.get("title", "")
        checks.append(GateCheck(
            name="has_title",
            passed=bool(title and len(title) > 5),
            message=f"Title: '{title}'" if title else "Missing title",
        ))

        desc = output_data.get("description", "") or output_data.get("problem", "")
        checks.append(GateCheck(
            name="has_description",
            passed=bool(desc and len(desc) > 20),
            message=f"Description length: {len(desc)} chars" if desc else "Missing description",
        ))

        priority = output_data.get("priority", "")
        checks.append(GateCheck(
            name="has_priority",
            passed=priority in ("high", "medium", "low", "critical"),
            message=f"Priority: {priority}" if priority else "Missing priority",
            severity="warning",
        ))

        category = output_data.get("category", "")
        checks.append(GateCheck(
            name="has_category",
            passed=bool(category),
            message=f"Category: {category}" if category else "Missing category",
            severity="warning",
        ))

        is_duplicate = output_data.get("is_duplicate", False)
        checks.append(GateCheck(
            name="not_duplicate",
            passed=not is_duplicate,
            message="No duplicate detected" if not is_duplicate else "Possible duplicate found",
        ))

        failed = [c for c in checks if not c.passed and c.severity == "error"]
        warned = [c for c in checks if not c.passed and c.severity == "warning"]

        if failed:
            verdict = GateVerdict.FAIL
        elif warned:
            verdict = GateVerdict.WARN
        else:
            verdict = GateVerdict.PASS

        return GateResult(
            gate=GateName.IDEATION.value,
            verdict=verdict,
            checks=checks,
            summary=f"{len(checks) - len(failed) - len(warned)}/{len(checks)} checks passed"
                    + (f", {len(warned)} warnings" if warned else ""),
        )

    def _check_plan(self, input_data: dict, output_data: dict) -> GateResult:
        checks = []

        steps = output_data.get("steps", []) or output_data.get("tasks", [])
        checks.append(GateCheck(
            name="has_steps",
            passed=len(steps) > 0,
            message=f"{len(steps)} steps defined" if steps else "No steps defined",
        ))

        files = output_data.get("files", []) or output_data.get("files_to_modify", [])
        checks.append(GateCheck(
            name="has_file_list",
            passed=len(files) > 0,
            message=f"{len(files)} files identified" if files else "No files identified",
            severity="warning",
        ))

        criteria = output_data.get("success_criteria", []) or output_data.get("acceptance_criteria", [])
        checks.append(GateCheck(
            name="has_success_criteria",
            passed=len(criteria) > 0,
            message=f"{len(criteria)} criteria defined" if criteria else "No success criteria",
        ))

        risks = output_data.get("risks", [])
        checks.append(GateCheck(
            name="has_risk_assessment",
            passed=len(risks) > 0,
            message=f"{len(risks)} risks identified" if risks else "No risks identified",
            severity="warning",
        ))

        deps = output_data.get("dependencies", [])
        checks.append(GateCheck(
            name="dependencies_identified",
            passed=True,
            message=f"{len(deps)} dependencies" if deps else "No dependencies (OK if standalone)",
            severity="info",
        ))

        effort = output_data.get("effort", "") or output_data.get("estimate", "")
        checks.append(GateCheck(
            name="has_effort_estimate",
            passed=bool(effort),
            message=f"Effort: {effort}" if effort else "No effort estimate",
            severity="warning",
        ))

        failed = [c for c in checks if not c.passed and c.severity == "error"]
        warned = [c for c in checks if not c.passed and c.severity == "warning"]

        if failed:
            verdict = GateVerdict.FAIL
        elif warned:
            verdict = GateVerdict.WARN
        else:
            verdict = GateVerdict.PASS

        return GateResult(
            gate=GateName.PLAN.value,
            verdict=verdict,
            checks=checks,
            summary=f"{len(checks) - len(failed) - len(warned)}/{len(checks)} passed"
                    + (f", {len(warned)} warnings" if warned else ""),
        )

    def _check_implementation(self, input_data: dict, output_data: dict) -> GateResult:
        checks = []

        diff = output_data.get("diff", "") or output_data.get("diff_summary", "")
        checks.append(GateCheck(
            name="has_changes",
            passed=bool(diff),
            message=f"Diff: {len(diff)} chars" if diff else "No code changes",
        ))

        test_results = output_data.get("test_results", {})
        tests_passed = test_results.get("passed", False) if isinstance(test_results, dict) else bool(test_results)
        test_msg = ""
        if isinstance(test_results, dict):
            test_msg = f"Tests: {test_results.get('passed_count', '?')}/{test_results.get('total_count', '?')} passed"
        elif isinstance(test_results, str):
            test_msg = f"Tests: {test_results[:100]}"
        else:
            test_msg = "No test results"
        checks.append(GateCheck(
            name="tests_pass",
            passed=tests_passed,
            message=test_msg,
        ))

        security = output_data.get("security_scan", {})
        security_clean = True
        if isinstance(security, dict):
            security_clean = security.get("clean", True)
        elif isinstance(security, str):
            security_clean = "vulnerability" not in security.lower() and "critical" not in security.lower()
        checks.append(GateCheck(
            name="security_clean",
            passed=security_clean,
            message="Security scan clean" if security_clean else f"Security issues found: {security}",
        ))

        changed_files = output_data.get("changed_files", [])
        denylist_violations = []
        DENYLIST = ["*.db", ".env", "credentials*", "*.key", "*.pem"]
        for f in changed_files:
            for pattern in DENYLIST:
                if fnmatch.fnmatch(f, pattern) or fnmatch.fnmatch(f.split("/")[-1], pattern):
                    denylist_violations.append(f)
        checks.append(GateCheck(
            name="no_denylist_violations",
            passed=len(denylist_violations) == 0,
            message="No restricted files modified" if not denylist_violations else f"Restricted files: {denylist_violations}",
        ))

        diff_lines = len(diff.split("\n")) if diff else 0
        checks.append(GateCheck(
            name="reasonable_diff_size",
            passed=diff_lines < 2000,
            message=f"{diff_lines} lines changed",
            severity="warning",
        ))

        failed = [c for c in checks if not c.passed and c.severity == "error"]
        warned = [c for c in checks if not c.passed and c.severity == "warning"]

        if failed:
            verdict = GateVerdict.FAIL
        elif warned:
            verdict = GateVerdict.WARN
        else:
            verdict = GateVerdict.PASS

        return GateResult(
            gate=GateName.IMPLEMENTATION.value,
            verdict=verdict,
            checks=checks,
            summary=f"{len(checks) - len(failed) - len(warned)}/{len(checks)} passed"
                    + (f", {len(warned)} warnings" if warned else ""),
        )

    def _check_acceptance(self, input_data: dict, output_data: dict) -> GateResult:
        checks = []

        requirements = input_data.get("requirements", []) or input_data.get("acceptance_criteria", [])
        criteria_met = output_data.get("criteria_met", [])

        if requirements:
            for i, req in enumerate(requirements):
                req_text = req if isinstance(req, str) else req.get("description", str(req))
                met = i < len(criteria_met) and criteria_met[i] if criteria_met else False
                checks.append(GateCheck(
                    name=f"requirement_{i+1}",
                    passed=bool(met),
                    message=f"{'PASS' if met else 'FAIL'}: {req_text[:80]}",
                ))
        else:
            checks.append(GateCheck(
                name="has_requirements",
                passed=False,
                message="No acceptance criteria defined in input",
                severity="warning",
            ))

        changelog = output_data.get("changelog_entry", "") or output_data.get("changelog", "")
        checks.append(GateCheck(
            name="has_changelog",
            passed=bool(changelog),
            message=f"Changelog: {changelog[:80]}" if changelog else "No changelog entry",
            severity="warning",
        ))

        pr_desc = output_data.get("pr_description", "")
        checks.append(GateCheck(
            name="has_pr_description",
            passed=bool(pr_desc),
            message="PR description present" if pr_desc else "No PR description",
            severity="warning",
        ))

        review = output_data.get("review_notes", "") or output_data.get("review", "")
        checks.append(GateCheck(
            name="review_completed",
            passed=bool(review),
            message="Review completed" if review else "No review notes",
            severity="warning",
        ))

        failed = [c for c in checks if not c.passed and c.severity == "error"]
        warned = [c for c in checks if not c.passed and c.severity == "warning"]

        if failed:
            verdict = GateVerdict.FAIL
        elif warned:
            verdict = GateVerdict.WARN
        else:
            verdict = GateVerdict.PASS

        return GateResult(
            gate=GateName.ACCEPTANCE.value,
            verdict=verdict,
            checks=checks,
            summary=f"{len(checks) - len(failed) - len(warned)}/{len(checks)} passed"
                    + (f", {len(warned)} warnings" if warned else ""),
        )

    def run_gate_with_retry(
        self,
        gate_name: str,
        input_data: dict,
        output_data: dict,
        node_id: str | None = None,
        max_retries: int = 2,
        budget_usd: float | None = None,
        spent_usd: float = 0.0,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> GateResult:
        """Run a gate with retry logic and budget checking.

        Retries up to ``max_retries`` times if the gate fails.  Aborts early
        if ``spent_usd >= budget_usd``.  Each attempt is persisted.
        """
        if budget_usd is not None and spent_usd >= budget_usd:
            result = GateResult(
                gate=gate_name,
                verdict=GateVerdict.FAIL,
                summary="Budget exhausted before gate could run",
            )
            self._persist_result(result, node_id, entity_type, entity_id)
            return result

        last_result: GateResult | None = None
        for attempt in range(max_retries + 1):
            result = self.run_gate(
                gate_name=gate_name,
                input_data=input_data,
                output_data=output_data,
                node_id=node_id,
                entity_type=entity_type,
                entity_id=entity_id,
            )
            result.retry_count = attempt
            last_result = result

            if result.verdict != GateVerdict.FAIL:
                return result

            if attempt < max_retries:
                log.info("gate_retry", gate=gate_name, attempt=attempt + 1, max_retries=max_retries)

        return last_result  # type: ignore[return-value]

    def _persist_result(self, result: GateResult, node_id: str | None,
                        entity_type: str | None, entity_id: str | None):
        """Save gate result to both verification_gates and verification_results."""
        checks_payload = json.dumps([
            {"name": c.name, "passed": c.passed, "message": c.message, "severity": c.severity}
            for c in result.checks
        ])
        try:
            with get_db() as conn:
                conn.execute(
                    insert(verification_gates).values(
                        id=str(uuid.uuid4()),
                        gate=result.gate,
                        verdict=result.verdict.value,
                        checks_json=checks_payload,
                        summary=result.summary,
                        node_id=node_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        run_at=result.run_at,
                        duration_ms=result.duration_ms,
                    )
                )
                conn.execute(
                    insert(verification_results).values(
                        id=str(uuid.uuid4()),
                        gate=result.gate,
                        verdict=result.verdict.value,
                        checks_json=checks_payload,
                        summary=result.summary,
                        node_id=node_id,
                        entity_type=entity_type,
                        entity_id=entity_id,
                        retry_count=result.retry_count,
                        budget_spent_usd=0.0,
                        run_at=result.run_at,
                        duration_ms=result.duration_ms,
                    )
                )
        except Exception as e:
            # Loud, not swallowed: a schema mismatch here silently kept
            # verification_results empty despite gates running.
            log.error("verification_gate_persist_failed", error=str(e))

    def get_history(self, entity_type: str | None = None, entity_id: str | None = None,
                    node_id: str | None = None, limit: int = 20) -> list[dict]:
        """Retrieve gate history from database, with parsed checks."""
        try:
            with get_db() as conn:
                conditions = []
                params: list = []
                if entity_type:
                    conditions.append("vg.entity_type = ?")
                    params.append(entity_type)
                if entity_id:
                    conditions.append("vg.entity_id = ?")
                    params.append(entity_id)
                if node_id:
                    conditions.append("vg.node_id = ?")
                    params.append(node_id)

                where = " AND ".join(conditions) if conditions else "1=1"
                params.append(limit)

                # Join with verification_results to get retry_count
                rows = conn.exec_driver_sql(
                    f"SELECT vg.*, COALESCE(vr.retry_count, 0) as retry_count "
                    f"FROM verification_gates vg "
                    f"LEFT JOIN verification_results vr "
                    f"  ON vg.gate = vr.gate AND vg.entity_id = vr.entity_id AND vg.run_at = vr.run_at "
                    f"WHERE {where} "
                    f"ORDER BY vg.run_at DESC LIMIT ?",
                    tuple(params),
                ).fetchall()

                results = []
                for r in rows:
                    row = dict(r._mapping)
                    # Parse checks_json for the frontend
                    checks_raw = row.pop("checks_json", None)
                    row["checks"] = json.loads(checks_raw) if checks_raw else []
                    results.append(row)
                return results
        except Exception as e:
            log.warning("verification_gate_history_failed", error=str(e))
            return []


# Module-level singleton
verification_service = VerificationService()

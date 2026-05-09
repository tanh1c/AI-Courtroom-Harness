from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from packages.orchestration.python.ai_court_orchestration.v2_service import (
    get_courtroom_v2_runtime_service,
    official_judgment_language_hits,
)
from packages.reporting.python.ai_court_reporting.service import get_v2_trial_record_service
from packages.shared.python.ai_court_shared.schemas import CaseState, HumanReviewMode

FIXTURE_PATH = ROOT_DIR / "packages/shared/fixtures/v2_demo_cases.json"


def main() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    service = get_courtroom_v2_runtime_service()
    record_service = get_v2_trial_record_service()

    results: list[tuple[str, str, int, int]] = []
    for demo in payload:
        case = CaseState.model_validate(demo["case"])
        expected = demo["expected_disposition"]
        trial = service.run_all(case, human_review_mode=HumanReviewMode.OPTIONAL)
        assert trial.simulated_decision is not None, f"{demo['demo_id']} missing simulated decision"
        actual = trial.simulated_decision.disposition.value
        assert actual == expected, f"{demo['demo_id']} expected {expected}, got {actual}"
        stage_turns = {
            stage.value: [turn.turn_id for turn in trial.dialogue_turns if turn.trial_stage == stage]
            for stage in trial.stage_order
        }
        assert all(stage_turns.values()), f"{demo['demo_id']} missing stage turns: {stage_turns}"
        assert trial.dialogue_quality.overlong_turn_ids == [], demo["demo_id"]
        assert trial.dialogue_quality.ungrounded_turn_ids == [], demo["demo_id"]
        assert trial.dialogue_quality.role_drift_warnings == [], demo["demo_id"]
        assert trial.decision_guard is not None, demo["demo_id"]
        assert trial.decision_guard.official_language_hits == [], demo["demo_id"]
        decision_text = (
            trial.simulated_decision.summary
            + " "
            + trial.simulated_decision.relief_or_next_step
            + " "
            + " ".join(trial.simulated_decision.rationale)
        )
        assert official_judgment_language_hits(decision_text) == [], demo["demo_id"]
        markdown = record_service.render(trial)
        for section in [
            "## Thành Phần Tham Gia",
            "## Transcript Phiên Tòa",
            "## Nghị Án Mô Phỏng",
            "## Kết Quả Mô Phỏng Không Ràng Buộc",
        ]:
            assert section in markdown, f"{demo['demo_id']} missing report section {section}"
        results.append((demo["demo_id"], actual, len(trial.stage_order), len(trial.dialogue_turns)))

    print("v2_demo_case_count:", len(results))
    for demo_id, disposition, stage_count, turn_count in results:
        print(f"{demo_id}: {disposition} stages={stage_count} turns={turn_count}")


if __name__ == "__main__":
    main()

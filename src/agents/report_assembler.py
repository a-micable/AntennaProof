"""Report Assembler — produces final markdown design review."""

from __future__ import annotations

from src.schemas import MetricStatus, VerifiedReview


def assemble_report(
    case_id: str,
    design_name: str,
    verified: VerifiedReview,
    verification_log: list[str],
) -> str:
    review = verified.review
    if not review:
        return f"# ENGINEERING DESIGN REVIEW\n\nCase {case_id}: verification failed.\n"

    lines = [
        "# ENGINEERING DESIGN REVIEW",
        "",
        f"**Case:** {case_id}",
        f"**Design:** {design_name}",
        "",
        f"**Overall Verdict:** {review.overall_verdict.value}",
        f"**Confidence:** {review.confidence.upper()}",
        f"**Evidence Coverage:** {review.evidence_coverage_percent:.0f}%",
        "",
    ]

    failed = [m for m in review.metric_results if m.status == MetricStatus.FAIL]
    passed = [m for m in review.metric_results if m.status == MetricStatus.PASS]
    insufficient = [m for m in review.metric_results if m.status == MetricStatus.INSUFFICIENT_EVIDENCE]

    if failed:
        lines.extend(["## Failed Requirements", ""])
        lines.append("| Metric | Required | Measured | Status |")
        lines.append("|--------|----------|----------|--------|")
        for m in failed:
            lines.append(f"| {m.metric} | {m.required} | {m.measured or '—'} | ✗ FAIL |")
        lines.append("")

    if passed:
        lines.extend(["## Passed Requirements", ""])
        lines.append("| Metric | Required | Measured | Status |")
        lines.append("|--------|----------|----------|--------|")
        for m in passed:
            lines.append(f"| {m.metric} | {m.required} | {m.measured or '—'} | ✓ PASS |")
        lines.append("")

    if insufficient:
        lines.extend(["## Insufficient Evidence", ""])
        for m in insufficient:
            lines.append(f"- **{m.metric}:** {m.reason or 'No evidence provided.'}")
        lines.append("")

    if verification_log:
        lines.extend(["## Verification Log", ""])
        for entry in verification_log:
            lines.append(f"- {entry}")
        lines.append("")

    if verified.violations:
        lines.extend(["## Verifier Violations (resolved)", ""])
        for v in verified.violations:
            lines.append(f"- {v}")
        lines.append("")

    lines.append(f"_{review.rationale}_")
    lines.append("")
    return "\n".join(lines)

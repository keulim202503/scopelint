from collections import Counter
from dataclasses import dataclass

from scopelint.history import HistoryEntry

TOP_OFFENDERS_LIMIT = 5


@dataclass(frozen=True)
class OffenderStat:
    path: str
    count: int


@dataclass(frozen=True)
class DashboardSummary:
    total_checks: int
    scope_creep_checks: int
    scope_creep_rate: float
    top_offenders: list[OffenderStat]


def summarize(entries: list[HistoryEntry], top_n: int = TOP_OFFENDERS_LIMIT) -> DashboardSummary:
    total = len(entries)
    creep_count = sum(1 for e in entries if not e.ok)
    rate = (creep_count / total) if total else 0.0

    counter: Counter[str] = Counter()
    for entry in entries:
        for finding in entry.findings:
            counter[finding.path] += 1

    top_offenders = [OffenderStat(path=path, count=count) for path, count in counter.most_common(top_n)]

    return DashboardSummary(
        total_checks=total,
        scope_creep_checks=creep_count,
        scope_creep_rate=rate,
        top_offenders=top_offenders,
    )


def render_text(summary: DashboardSummary) -> str:
    lines = [
        f"총 검사 횟수: {summary.total_checks}",
        f"스코프 크립 발견: {summary.scope_creep_checks}건 ({summary.scope_creep_rate:.0%})",
        "반복 발생 파일 Top:",
    ]
    if not summary.top_offenders:
        lines.append("  (없음)")
    else:
        lines.extend(f"  - {stat.path}: {stat.count}회" for stat in summary.top_offenders)
    return "\n".join(lines)


def render_html(summary: DashboardSummary) -> str:
    rows = "".join(f"<tr><td>{stat.path}</td><td>{stat.count}</td></tr>" for stat in summary.top_offenders)
    return f"""<!doctype html>
<html>
<head><meta charset="utf-8"><title>ScopeLint 팀 대시보드</title></head>
<body>
<h1>ScopeLint 팀 대시보드</h1>
<p>총 검사 횟수: {summary.total_checks}</p>
<p>스코프 크립 발견: {summary.scope_creep_checks}건 ({summary.scope_creep_rate:.0%})</p>
<h2>반복 발생 파일 Top {len(summary.top_offenders)}</h2>
<table border="1"><tr><th>파일</th><th>횟수</th></tr>{rows}</table>
</body>
</html>"""

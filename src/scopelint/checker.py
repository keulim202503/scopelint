import re
from dataclasses import dataclass

STOPWORDS = {
    "the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "with",
    "this", "that", "it", "is", "are", "be", "please", "add", "fix", "update",
    "이", "그", "저", "을", "를", "에", "의", "가", "은", "는", "하고", "해줘",
    "해주세요", "부탁", "수정", "추가", "기능",
}

SENSITIVE_PATH_PATTERNS = (
    ".github/workflows/",
    "Dockerfile",
    "docker-compose",
    ".env",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "package-lock.json",
    "poetry.lock",
    "uv.lock",
    "Cargo.toml",
    "Cargo.lock",
    "go.mod",
    "go.sum",
)


@dataclass(frozen=True)
class ChangedFile:
    path: str
    insertions: int
    deletions: int


@dataclass(frozen=True)
class ScopeFinding:
    path: str
    reason: str


@dataclass(frozen=True)
class ScopeResult:
    ok: bool
    findings: list[ScopeFinding]


def extract_keywords(text: str) -> set[str]:
    tokens = re.split(r"[^0-9a-zA-Z가-힣]+", text.lower())
    return {t for t in tokens if len(t) >= 2 and t not in STOPWORDS}


def _path_tokens(path: str) -> set[str]:
    stem = re.sub(r"\.[a-zA-Z0-9]+$", "", path)
    tokens = re.split(r"[^0-9a-zA-Z가-힣]+", stem.lower())
    return {t for t in tokens if len(t) >= 2 and t not in STOPWORDS}


def _is_sensitive(path: str) -> bool:
    return any(pattern in path for pattern in SENSITIVE_PATH_PATTERNS)


def _mentioned_explicitly(path: str, task_text: str) -> bool:
    basename = path.rsplit("/", 1)[-1]
    return basename in task_text or path in task_text


def check_scope(task_text: str, changed_files: list[ChangedFile]) -> ScopeResult:
    keywords = extract_keywords(task_text)
    findings = []

    for f in changed_files:
        if _is_sensitive(f.path) and not _mentioned_explicitly(f.path, task_text):
            findings.append(
                ScopeFinding(
                    path=f.path,
                    reason=f"민감 파일({f.path})이 작업 설명에 언급되지 않았는데 변경됨",
                )
            )
            continue

        if not keywords:
            continue

        if not (_path_tokens(f.path) & keywords):
            findings.append(
                ScopeFinding(
                    path=f.path,
                    reason=f"{f.path} 경로가 작업 설명의 키워드와 겹치지 않음 (요청 범위 밖일 가능성)",
                )
            )

    return ScopeResult(ok=len(findings) == 0, findings=findings)

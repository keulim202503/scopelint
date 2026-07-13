from scopelint.checker import ChangedFile, check_scope, extract_keywords


def test_extract_keywords_drops_stopwords_and_short_tokens():
    keywords = extract_keywords("Please fix the login bug in auth handler")

    assert "login" in keywords
    assert "auth" in keywords
    assert "handler" in keywords
    assert "the" not in keywords
    assert "fix" not in keywords


def test_in_scope_change_passes():
    files = [ChangedFile(path="src/auth/login.py", insertions=10, deletions=2)]
    result = check_scope("로그인(login) 버그를 수정해줘", files)

    assert result.ok is True
    assert result.findings == []


def test_unrelated_file_flagged_as_scope_creep():
    files = [
        ChangedFile(path="src/auth/login.py", insertions=10, deletions=2),
        ChangedFile(path="src/billing/invoice.py", insertions=40, deletions=0),
    ]
    result = check_scope("로그인(login) 버그를 수정해줘", files)

    assert result.ok is False
    flagged_paths = {f.path for f in result.findings}
    assert flagged_paths == {"src/billing/invoice.py"}


def test_sensitive_file_flagged_when_not_mentioned():
    files = [ChangedFile(path="requirements.txt", insertions=1, deletions=0)]
    result = check_scope("로그인 버그를 수정해줘", files)

    assert result.ok is False
    assert "requirements.txt" in result.findings[0].reason


def test_sensitive_file_allowed_when_explicitly_mentioned():
    files = [ChangedFile(path="requirements.txt", insertions=1, deletions=0)]
    result = check_scope("requirements.txt에 requests 패키지를 추가해줘", files)

    assert result.ok is True


def test_empty_task_text_skips_keyword_check_but_still_flags_sensitive():
    files = [
        ChangedFile(path="src/foo.py", insertions=1, deletions=0),
        ChangedFile(path=".github/workflows/ci.yml", insertions=1, deletions=0),
    ]
    result = check_scope("", files)

    assert result.ok is False
    flagged_paths = {f.path for f in result.findings}
    assert flagged_paths == {".github/workflows/ci.yml"}

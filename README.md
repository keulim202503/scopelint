# ScopeLint

AI 코딩 에이전트(Claude Code, Cursor 등)의 실제 git diff가 요청한 작업 범위를 벗어났는지
자동 탐지하는 GitHub Action/CLI.

## 문제
"버그 하나만 고쳐줘"라고 시켰는데 에이전트가 관련 없는 파일을 건드리거나,
CI 설정/의존성 파일처럼 민감한 파일을 조용히 수정해버리는 "스코프 크립"이 자주 발생함.
리뷰어가 diff 전체를 매번 손으로 확인하지 않으면 놓치기 쉬움.

## 타겟
Claude Code/Cursor 등으로 코딩하는 솔로 개발자·소규모 팀.

## 경쟁사
없음 (일반 코드 리뷰 도구는 존재하지만, "작업 설명 vs 실제 diff 범위"를 전용으로 대조하는 제품은 없음).

## 빌드 플랜 (2주)
git diff --numstat로 변경 파일 목록을 수집하고, 원래 요청한 작업 설명 텍스트와
키워드/민감 파일 기준으로 대조해 범위 이탈을 탐지하는 GitHub Action/CLI.

### MVP v1 범위
1. CLI: 현재 저장소의 `git diff --numstat`로 변경된 파일 목록을 수집
2. 작업 설명 텍스트(이슈 제목, PR 제목 등)를 입력받음
3. 대조 로직:
   - 키워드 겹침 체크: 작업 설명에서 키워드를 추출해 각 변경 파일의 경로 토큰과 겹치는지 확인
   - 민감 파일 체크: CI 설정, 의존성 매니페스트/락파일, `.env`, Dockerfile 등은
     작업 설명에 파일명이 명시적으로 언급되지 않으면 무조건 플래그
4. 범위 이탈 발견 시 CLI는 non-zero exit → GitHub Action에서 CI 실패 처리

### 기술 스택
Python CLI (pip 설치) + 이를 감싸는 composite GitHub Action.

## 수익 모델
GitHub Action 무료 + 팀 대시보드(반복 발생 스코프 크립 패턴 통계) $15/월 구독.

## 증명 방법
실제 저장소에 설치해 관련 없는 파일 변경/민감 파일 무단 수정 사례를 잡아내는지 시연.

## 점수
- 사업성: ⭐⭐⭐☆☆
- 실현가능성: ⭐⭐⭐⭐⭐

## 진행 상태
- [x] 아이디어 선정 (2026-07-07)
- [x] 스캐폴딩 (repo/git/README)
- [x] CLI 뼈대 구현 (diff 수집 + 키워드/민감 파일 대조 로직)
- [x] 단위 테스트 14개 작성 및 통과
- [x] 실제 저장소 대상 시연 (스코프 크립 탐지 → exit 1 확인)
- [x] GitHub Action 래핑
- [x] 실사용(dev-pipeline) 테스트로 발견한 오탐(디렉터리명 미매칭) 버그 수정
- [x] GitHub PR diff 지원 (`--pr`/`--repo`, gh CLI 기반)

## GitHub Action 사용법

```yaml
- uses: actions/checkout@v4
  with:
    fetch-depth: 0

- uses: keulim202503/scopelint@v1
  with:
    task: ${{ github.event.pull_request.title }}
    # 또는 task-file: path/to/task.txt
    working-directory: '.'
```

`task`/`task-file` 중 정확히 하나를 넘겨야 합니다. 범위 이탈이 발견되면 액션이
non-zero exit로 실패해 CI를 막습니다. 예시 워크플로: `.github/workflows/example-usage.yml`.

## GitHub PR diff 모드

로컬 `git diff` 대신 특정 PR의 변경 파일을 직접 검사할 수 있습니다. `gh` CLI가
설치되어 있고 인증되어 있어야 합니다 (`gh auth status`).

```
$ scopelint --task "로그인 버그를 수정해줘" --pr 42
$ scopelint --task "로그인 버그를 수정해줘" --pr 42 --repo owner/repo
```

`--repo`를 생략하면 현재 디렉터리(`--cwd`)의 git remote로부터 `gh repo view`를 통해
`owner/repo`를 자동 추론합니다. 내부적으로 `gh api repos/{owner}/{repo}/pulls/{n}/files`를
호출해 PR에서 실제로 변경된 파일 목록(추가/삭제 라인 수 포함)을 가져오며, 이후 대조
로직은 로컬 diff 모드와 동일합니다. 이 모드는 이미 완결된 PR을 리뷰 전에 검사하거나,
CI에서 `git diff` 히스토리가 얕게 checkout된 경우(예: `fetch-depth: 1`)에도 정확한
변경 파일 목록을 얻고 싶을 때 유용합니다.

## 시연: 실제 실행 로그

임시 저장소(`src/auth/login.py`, `src/billing/invoice.py`, `requirements.txt`)에 커밋된
베이스라인을 두고, 세 가지 시나리오로 `scopelint` CLI를 직접 실행한 결과입니다.

### 1. 로그인 버그 수정을 요청했는데 관련 없는 파일 + 의존성 파일까지 건드림 (스코프 크립)

`src/auth/login.py`(요청 범위) 외에 `src/billing/invoice.py`(무관), `requirements.txt`에
numpy 추가(요청하지 않음)까지 변경된 상태:

```
$ scopelint --task "로그인(login) 함수의 버그를 수정해줘" --cwd demo-repo
SCOPE CREEP: 작업 범위를 벗어난 변경이 발견되었습니다.
- 민감 파일(requirements.txt)이 작업 설명에 언급되지 않았는데 변경됨
- src/billing/invoice.py 경로가 작업 설명의 키워드와 겹치지 않음 (요청 범위 밖일 가능성)
exit code: 1
```

### 2. 요청한 파일만 정직하게 수정 (정상)

같은 작업 설명, `src/auth/login.py`만 변경된 상태:

```
$ scopelint --task "로그인(login) 함수의 버그를 수정해줘" --cwd demo-repo
OK: 모든 변경 사항이 작업 범위 안에 있습니다.
exit code: 0
```

### 3. 민감 파일이지만 작업 설명에 명시적으로 언급됨 (정상)

작업 설명에 파일명을 직접 지정한 경우:

```
$ scopelint --task "requirements.txt에 numpy 패키지를 추가해줘" --cwd demo-repo
OK: 모든 변경 사항이 작업 범위 안에 있습니다.
exit code: 0
```

같은 파일 변경이라도 작업 설명에 명시적으로 언급되었는지 여부에 따라 결과가 달라짐을
보여줍니다. 세 시나리오 모두 실제 git 저장소에 대한 `git diff --numstat` 호출을 통해
얻은 결과이며, 목업이 아닙니다.

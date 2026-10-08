# PC와 클라우드에서 함께 작업하기

두 환경은 같은 GitHub 저장소를 사용하되, 각자의 파일을 별도로 관리합니다.
파일과 실행 중인 프로세스가 자동으로 동기화되지는 않습니다.

- 저장소: https://github.com/chanmini584-ux/jango-danggeun-market
- 회원 기능 브랜치: `codex/member-auth`
- PC: VS Code의 Codex에서 로컬 프로젝트 작업
- 클라우드: 별도의 개발 환경에서 구현·검증 작업

## 1. PC의 디스크 공간 확보

Codex VSIX 다운로드에 “디스크가 가득 참”이 표시되면 먼저 저장 공간을
확보해야 합니다. 파일 탐색기의 “내 PC”에서 다운로드 위치와 `C:` 드라이브의
남은 공간을 확인하세요. Windows 설정 → 시스템 → 저장소 → 임시 파일에서
삭제할 항목을 확인하고 정리하세요. 다운로드 폴더의 필요한 파일은 보존하세요.
다운로드 위치를 다른 드라이브로 바꿔도 확장 설치 위치에는 여유 공간이 필요합니다.

## 2. PC에서 구현된 브랜치 받기

VS Code에서 기존 Django 프로젝트 폴더를 열고 터미널에서 실행하세요.

```powershell
git status
git fetch origin
git switch --track origin/codex/member-auth
```

PC에 아직 커밋하지 않은 변경이 있다면 브랜치를 전환하기 전에 먼저 보존해야
합니다. 브랜치 전환 오류가 나면 오류와 `git status` 결과로 원인을 확인하세요.
이 과정을 위해 `git reset --hard`나 `git clean`을 실행할 필요는 없습니다.
이미 `codex/member-auth` 로컬 브랜치가 있다면 `git switch codex/member-auth`를
사용하고, 그 브랜치에서 `git pull --ff-only`로 최신 변경을 받습니다.

기존 `.env`와 가상환경은 유지합니다. 가상환경을 활성화한 뒤 실행하세요.

```powershell
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Supabase 연결 정보는 PC의 `.env`에 있어야 합니다. 설정 방법은 README.md를
참고하세요. 클라우드 테스트는 별도의 로컬 PostgreSQL로 수행했습니다.

## 3. 로컬 Codex 연결

게시자가 OpenAI인 공식 Codex 확장을 설치하고 ChatGPT 계정으로 로그인하세요.
`manage.py`가 있는 프로젝트 폴더를 열고, 작업 위치 선택 항목이 있으면
Local/로컬을 선택하세요. Codex에 다음 요청을 입력할 수 있습니다.

```text
현재 열린 로컬 Django 프로젝트의 README.md와 LOCAL_CLOUD_WORKFLOW.md를 읽어 주세요.
회원 기능은 codex/member-auth 브랜치에 구현되어 있습니다.
기존 .env를 유지하고, 회원가입·로그인·로그아웃 동작을 확인해 주세요.
비밀번호와 DB 연결 비밀값은 출력하지 마세요.
```

## 4. 변경 사항 주고받기

PC와 클라우드에서 같은 작업 브랜치를 동시에 수정하는 대신, 작업별 브랜치를
사용하고 한쪽의 변경이 저장소에 올라온 뒤 다른 쪽에서 받아 작업하세요.
원격 변경을 받기 전에 로컬 작업을 커밋 등으로 보존하세요.

```powershell
git fetch origin
git pull --ff-only
```

충돌이나 서로 다른 커밋 때문에 `--ff-only`가 실패하면 오류와 변경 내역을
확인해 병합합니다. 강제 push나 reset으로 해결하지 않습니다.
`.env`와 가상환경은 Git으로 공유하지 않습니다. 이 클라우드 채팅에는 PC 파일
접근 권한이 없으므로, PC 파일 수정은 로컬 Codex에서 요청해야 합니다.

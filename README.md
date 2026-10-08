# Danggeun Market

Django 5.2로 만드는 중고거래 수업 프로젝트입니다. 2026년 10월 7일 수업 범위인
회원가입·로그인·로그아웃을 구현했습니다. 상품 기능과 화면 디자인은 이후 단계입니다.

## 구현된 기능

- 회원가입: 아이디, 이름, 생년월일, 휴대폰번호, 비밀번호와 확인 값
- 아이디·휴대폰번호 중복 검사와 Django 기본 비밀번호 검증
- Django `User`와 1:1 `Profile` 저장, 회원가입 후 자동 로그인
- 로그인·POST 로그아웃, 메인 화면의 이름·아이디 및 로그인 상태 표시
- 관리자 페이지에서 Profile 목록·검색

회원 인증은 Django가 처리합니다. Supabase는 Django ORM이 연결하는 PostgreSQL
데이터베이스이며, 이 단계에서는 Supabase Auth나 Python SDK를 사용하지 않습니다.
회원과 Profile은 하나의 트랜잭션으로 저장합니다.

## PC의 VS Code에서 실행하기

Python 3.12를 권장합니다. `manage.py`가 있는 프로젝트 폴더에서 실행하세요.
이미 사용하는 가상환경이 있다면 그대로 활성화해도 됩니다.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

기존 `.env`가 있다면 복사하지 말고 기존 연결 정보를 유지하세요. macOS/Linux에서는
`source .venv/bin/activate`와 `cp .env.example .env`를 사용합니다.

`.env`에 Supabase의 **Connect → Session pooler** 연결 정보를 입력하세요.
`DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`가 필요합니다.
`DB_SSLMODE=require`는 TLS 연결을 요구하는 기본값입니다. 비밀번호는 `.env`에만
입력하고 GitHub나 채팅에 올리지 마세요. `.env.example`에는 실제 비밀번호가 없습니다.

```powershell
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`market/migrations/0001_initial.py`가 포함되어 있으므로 실행 전에 새 migration을
만들 필요는 없습니다. 기존 관리자 계정이 있다면 재생성하지 않아도 됩니다.
회원가입으로 만드는 일반 회원에게는 관리자 권한이 부여되지 않습니다.

| 경로 | 기능 |
| --- | --- |
| `/` | 메인 화면 |
| `/signup/` | 회원가입 |
| `/login/` | 로그인 |
| `/logout/` | 폼의 POST 요청으로 로그아웃 |
| `/admin/` | 관리자 화면 및 Profile 조회 |

회원가입 후 메인에서 이름과 아이디를 확인하고, 로그아웃 후 다시 로그인하세요.
Supabase Table Editor에서는 `auth_user`와 `market_profile`을 확인합니다.
비밀번호는 Django가 해시로 저장합니다. Supabase Dashboard에서의 실제 데이터
확인은 해당 프로젝트에 연결하여 마이그레이션과 회원가입을 실행한 뒤 진행하세요.

## 검증

```powershell
python manage.py check
python manage.py makemigrations --check --dry-run
python manage.py test market
```

테스트는 회원가입·중복 입력·비밀번호 검증·로그인·로그아웃·CSRF·관리자 조회와
DB 트랜잭션을 검사합니다. Django 테스트 러너가 별도 테스트 DB를 생성·삭제하므로
테스트 전용 PostgreSQL 연결을 권장하며, DB 계정에 테스트 DB 생성 권한이 필요합니다.

이 클라우드에서 준비한 로컬 PostgreSQL로 검증하려면 다음과 같이 실행합니다.
이 연결은 PC의 Supabase 설정과 별개입니다.

```bash
bash /workspace/onboarding/start-db.sh
source /workspace/onboarding/activate.sh
cd /workspace/jango-danggeun-market
export DJANGO_SETTINGS_MODULE=config.settings
export DB_NAME=danggeun_dev DB_USER=agent DB_HOST=/workspace/onboarding/pgsocket DB_PORT=55432 DB_SSLMODE=disable
unset DB_PASSWORD
python manage.py migrate
python manage.py test market
python manage.py runserver 127.0.0.1:8000 --noreload
```

현재 설정은 수업용 개발 환경입니다. PC의 VS Code 파일은 클라우드 수정과
자동으로 동기화되지 않으므로 변경된 파일을 가져온 후 위 명령으로 실행하세요.

PC와 클라우드의 Git 동기화·로컬 Codex 연결 방법은
[LOCAL_CLOUD_WORKFLOW.md](LOCAL_CLOUD_WORKFLOW.md)를 참고하세요.

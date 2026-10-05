# ae-P1NG9CHANDESU

**æ-P1NG9CHANDESU**는 `discord.py` 기반으로 개발된 다기능 디스코드 서버 관리 및 유틸리티 봇입니다. 서버 설정을 위한 `/set` 명령어, 로깅, 제재, 티켓 문의, 임시 음성채널 생성, 스팸 방지, 커스텀 이모지 관리 기능을 제공하고 있습니다.

## 주요 기능
### 1. 서버 설정 관리
* 서버별 설정을 `data/config.json`에 저장하고 동적으로 로드합니다.
* 로그 채널, 명령어 전용 채널, 스팸 필터 채널, 음성 생성 채널, 티켓 패널 생성 등을 각각 다르게 지정할 수 있습니다.

### 2. 서버 관리 및 유저 제재
* 관리자 전용 슬래시 명령어를 통해 유저 음성 차단(Mute/Deafen) 및 강제 퇴장(vckick)을 지원합니다.
* 타임아웃, 추방(Kick), 차단(Ban/Unban) 기능을 다루며, `10s`, `5m`, `1h`, `1d` 형태의 유연한 시간 지정을 지원합니다.   

### 3. 상세 서버 로깅
* 멤버 활동: 서버 입장 및 퇴장 감지.
* 메시지 감지: 메시지 수정 및 삭제 내역 기록 (코드블록 이스케이프 처리 지원).
* 음성 활동: 음성 채널 입장/퇴장/이동 내역 감지.
* 이모지 감지: 서버 커스텀 이모지의 추가, 삭제, 이름 변경 이벤트를 감사 로그와 연동해 로깅.   

### 4. 문의 및 티켓 시스템
* Discord 버튼(Button UI) 기반의 티켓 오픈 및 종료 기능.
* 5분간 대화가 없을 경우 자동으로 티켓을 종료하고 카테고리를 이동 처리하는 오토 클로즈 타이머 지원.
* `/answer` 명령어로 관리자가 지정 티켓 채널에 답변을 전송.
* 티켓 채널 내부의 대화 및 첨부파일 내역을 지정된 로그 채널로 전송.

### 5. 임시 음성 채널 생성
* 지정된 생성 채널에 유저가 입장하면 개인 전용 임시 음성 채널을 자동 생성.
* 채널 내 모든 인원이 퇴장하면 해당 임시 채널을 자동 삭제.
* 방장은 `/음성방이름`, `/음성방인원` 명령어로 자신의 채널 설정을 변경 가능.

### 6. 자동 스팸 필터
* 지정된 스팸 채널에 메시지 작성 시 24시간 임시 밴 처리 후 `data/spam_ban.json`에 기록.
* 주기적 루프 태스크를 진행하여 만료 시 자동으로 차단을 해제.
* `@everyone` 또는 `@here` 전체 멘션 작성 시 1시간 타임아웃을 자동 부여.   

### 7. 이모지 도우미
* 일반 메시지로 단일 커스텀 이모지를 전송 시 웹훅을 통해 고화질 이미지로 확대 전송.
* `/addemoji`로 첨부파일, URL 또는 기존 이모지를 활용해 커스텀 이모지를 신규 등록.
* `/delemoji`로 서버 커스텀 이모지 삭제.   

### 8. aespa SNS 정보 안내
* aespa 그룹 전체 및 각 멤버(카리나, 지젤, 윈터, 닝닝)의 공식 SNS 채널 바로가기 링크를 제공.

## 프로젝트 구조
```
.
├── main.py                   # 봇 실행 파일 및 Cog 자동 로더
├── cogs/                     # 기능별 Cog 모듈 디렉토리
│   ├── aespa.py              # aespa SNS 링크 정보 안내
│   ├── emoji.py              # 이모지 확대 및 커스텀 이모지 관리
│   ├── logger.py             # 서버 이벤트 로깅 시스템
│   ├── moderation.py         # 유저 처벌 및 관리 명령어
│   ├── settings.py           # 서버별 데이터/채널 설정 관리
│   ├── spam.py               # 스팸 감지 및 임시 밴/타임아웃
│   ├── ticket.py             # 티켓 시스템 및 자동 종료 타이머
│   └── voice.py              # 동적 임시 음성 채널 생성 및 삭제
├── data/                     # 데이터 저장용 디렉토리
│   ├── aespa_data.json       # aespa SNS 기본 데이터 (정적 파일)
│   ├── config.json           # 서버 설정 데이터 (런타임 생성)
│   ├── spam_ban.json         # 임시 밴 대상 데이터 (런타임 생성)
│   └── temp_channels.json    # 생성된 임시 음성 채널 정보 (런타임 생성)
├── .env.example              # 환경 변수 설정 템플릿 (토큰 양식)
├── .gitignore                # Git 추적 제외 설정 파일 (.env, data/*.json 등)
├── README.md                 # 프로젝트 문서 및 사용 가이드
└── requirements.txt          # 필요 파이썬 패키지 목록
```

## 시작하기

### 0. 사전 준비
* **Python 3.8 이상**이 설치되어 있어야 합니다.
* **Discord Developer Portal 설정**: 봇의 원활한 기능 동작을 위해 아래의 **Privileged Gateway Intents**를 반드시 활성화해야 합니다.
    * `Server Members Intent` (멤버 입장/퇴장, 음성 로깅 및 관리용)
    * `Message Content Intent` (메시지 감지 및 스팸 필터용)

### 1. 저장소 클론 및 이동
```bash
git clone https://github.com/penguinjean0421/ae-P1NG9CHANDESU.git
cd ae-P1NG9CHANDESU
```

### 2. 필요 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 환경 변수 설정
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 입력합니다.
```
BOT_TOKEN=your_discord_bot_token_here
BOT_PREFIXES=!,?
```

### 4. 봇 실행
```bash
python main.py
```

## 슬래시 명령어 목록
### 서버 설정
* `/check` - 현재 서버 설정 상태 확인
* `/set log [target] [channel]` - 로그 채널 설정 (server, punish, ticket)
* `/set command [target] [channel]` - 전용 명령어 채널 설정 (bot, emoji, ticket)
* `/set spam [channel]` - 스팸 감지 채널 설정
* `/set voice [voice_channel]` - 음성방 생성 전용 음성 채널 지정
* `/reset [all|log|command|voice|spam]` - 특정 또는 전체 서버 설정 초기화

### 서버 관리
* `/mute [member] [time]` - 유저 음성 마이크 차단
* `/unmute [member]` - 유저 음성 마이크 차단 해제
* `/deafen [member] [time]` - 유저 헤드셋 차단
* `/undeafen [member]` - 유저 헤드셋 차단 해제
* `/vckick [member] [reason]` - 음성 채널 강제 퇴장
* `/timeout [member] [time] [reason]` - 유저 타임아웃 지정 (예: 10m, 1h)
* `/untimeout [member] [reason]` - 타임아웃 해제
* `/kick [member] [reason]` - 유저 추방
* `/ban [member] [reason]` - 유저 차단
* `/unban [user_spec]` - 차단 해제 (ID 또는 이름#태그)

### 문의 티켓
* `/open` - 수동 티켓 채널 생성
* `/close` - 현재 티켓 채널 종료 안내 버튼 전송
* `/answer [target_channel] [content]` - 지정 티켓 채널로 관리자 답변 전달

### 음성 채널
* `/음성방이름 [new_name]` - 임시 음성 채널 이름 변경 (방장 전용)
* `/음성방인원 [limit]` - 임시 음성 채널 인원 제한 변경 (0~99, 방장 전용)

### 이모지 도우미
* `/addemoji [name] [image] [source]` - 커스텀 이모지 등록
* `/delemoji [name]` - 서버 커스텀 이모지 삭제

### 에스파 SNS
* `/aespa` - aespa 공식 SNS 링크
* `/karina` - 카리나 SNS 링크
* `/giselle` - 지젤 SNS 링크
* `/winter` - 윈터 SNS 링크
* `/ningning` - 닝닝 SNS 링크
# Knowledge Base — Schema

hansu의 개인 지식베이스. 주제는 한정하지 않는다 (엔지니어링·커리어·독서·그 외 전부).
운영은 `karpathy-llm-wiki` 스킬을 따르되, 아래 항목이 스킬 기본값보다 우선한다.

스킬 위치: `.agents/skills/karpathy-llm-wiki/` (`.claude/skills/`에 심링크)

---

## 두 줄 규칙

1. **`raw/`는 절대 고치지 않는다.** 오타도, 나중에 틀린 걸 알게 돼도 고치지 않는다.
   틀렸다는 사실은 `wiki/`에 Status 블록으로 기록한다.
2. **`wiki/`는 절대 손으로 쓰지 않는다.** 전부 에이전트가 쓴다.

사람은 `raw/`에 넣기만 한다. 분류·링크·인덱스·정합성은 전부 에이전트 몫이다.

---

## 레이아웃

```
raw/                  불변 소스 계층
├─ journal/           내 일지.  YYYY-MM-DD.md
├─ meetings/          회의록 · 1on1 · weekly
├─ sessions/          Claude Code 세션 자동 요약. YYYY-MM-DD.md  ← git 제외
└─ <topic>/           그 외. 주제별 자유 (외부 자료와 주제별 작업 기록)

wiki/                 에이전트 전용 정제 계층
├─ index.md           정적 카탈로그 = 에이전트 진입점
├─ log.md             append-only 작업 로그
└─ <topic>/           자유 topic, 1단계까지만
```

`wiki/`의 topic은 미리 정해두지 않는다. 컴파일하면서 필요한 것을 만들고, 가까운 게 있으면 재사용한다.

---

## 출처 구분 — journal vs external

이 구분은 **주제 축이 아니라 출처 축**이다. 주제가 넓어질수록 더 중요해진다.

| | external (`type: source`) | 내 기록 (`journal` · `meeting` · `worklog`) |
|---|---|---|
| 출처 | URL·문서. 재확인 가능 | 나 |
| 틀렸을 때 | 원저자 책임 | 내 기억·판단 오류 |
| 성격 | 검증된 사실 | 1차 증거이되 검증된 사실은 아님 |

`raw/` 디렉토리는 주제로 나뉘므로 출처 구분은 **디렉토리가 아니라 `type` 필드**가 한다.
한 주제 폴더 안에 내 작업 기록과 외부 자료가 섞여 있어도 된다.

**wiki 문서를 쓸 때 이 둘의 근거 강도를 뭉뚱그리지 말 것.** journal에서만 나온 주장은
"당시 내 판단" 임이 문장에서 드러나야 한다. external 근거가 있으면 그쪽을 우선한다.

---

## Journal Ingest — 스킬 기본 Ingest의 예외

스킬의 Ingest는 `fetch → raw 저장 → triage → compile` 순서다.
journal은 **이미 내가 쓴 파일이므로 fetch 단계가 없다.** raw 저장도 이미 끝나 있다.

`raw/journal/`, `raw/meetings/` 를 인제스트할 때:

1. fetch 건너뛴다. 원본을 어떤 이유로도 수정하지 않는다.
2. 스킬의 Triage를 그대로 적용한다 — `New / Update / Disputed / No material`.
   **일지 대부분은 No material이 정상이다.** 할 일 체크와 잡담에서 억지로 wiki 페이지를 만들지 않는다.
3. 재사용 가능한 지식이 있을 때만 compile한다. 판단 기준: *6개월 뒤 내가 다시 찾을 내용인가.*
4. Raw 필드는 해당 일지 파일을 가리킨다.

"지난 주 journal 인제스트해줘" 같은 범위 지정 요청을 기본 사용 방식으로 본다.

---

## 메타데이터

스킬의 blockquote 메타데이터를 **유지하고**, 그 위에 YAML frontmatter를 얹는다.
blockquote는 스킬(lint·`check_evidence.py`)이 읽고, frontmatter는 Obsidian dataview와 사람이 읽는다.

### raw 파일

```yaml
---
type: journal          # journal | meeting | worklog | source
date: 2025-05-20       # worklog·source는 없을 수 있음
confidential: internal # public | internal | secret
tags: []
---
```

| type | 무엇 | 예 |
|---|---|---|
| `journal` | 날짜 단위 일지 | `raw/journal/2025-05-20.md` |
| `meeting` | 회의록 · 1on1 · weekly | `raw/meetings/2025-05-20-1on1.md` |
| `worklog` | 주제별 내 작업 기록. 날짜 축이 아님 | `raw/kubernetes/eks-cilium.md` |
| `source` | 외부에서 가져온 것 | `raw/blog/install-cilium-eks.md` |
| `session` | Claude Code 세션 자동 요약 | `raw/sessions/2026-11-16.md` |

**`session`은 근거 강도가 가장 낮다.** 사람이 쓴 게 아니라 **대화를 기계가 요약한 2차 가공물**이고,
요약 과정에서 왜곡될 수 있다. wiki 문서가 `session` 근거만 갖고 있으면
"세션 기록에 따르면" 수준으로 쓰고, 확정적으로 단정하지 않는다.
journal·worklog·source 근거가 있으면 그쪽을 우선한다.

외부 자료(`type: source`)는 frontmatter 아래에 스킬의 `references/raw-template.md`
blockquote(Source/Collected/Published)를 그대로 붙인다.

### wiki 문서

```yaml
---
title: EKS에서 Cilium CNI로 전환
type: article          # article | archive
status: verified       # draft | verified | outdated | disputed
confidential: internal
tags: [kubernetes, networking, cilium]
---

# EKS에서 Cilium CNI로 전환

> Sources: Cilium Docs, 2025-05-24; 작업 일지, 2025-05-24
> Raw: [EKS Cilium](../../raw/kubernetes/eks-cilium.md)
> Updated: 2026-09-15
```

**H1 제목은 생략할 수 없다.** frontmatter에 `title`이 있어도 반드시 넣는다.
`check_evidence.py`는 **H1 바로 다음의 blockquote만** 메타데이터 헤더로 인정한다.
H1이 없으면 Raw 필드를 못 찾아 근거 검증이 통째로 실패한다.

**`updated`는 blockquote에만 둔다. frontmatter에 넣지 않는다.**
파서가 frontmatter를 본문에 합쳐(`preamble + body`) 검증하기 때문에,
frontmatter의 날짜가 "raw에 없는 값"으로 잡혀 문서 수만큼 오탐이 쌓인다.
문서의 최신성은 `wiki/index.md` 의 Updated 컬럼이 담당한다.

같은 이유로 **frontmatter에는 날짜·숫자 모양의 값을 넣지 않는다.** 전부 텍스트만.

- `updated`는 **지식 내용이 바뀐 날**이다. 오타·서식 수정으로는 갱신하지 않는다. 파일 mtime과 무관.
- `status`는 스킬의 Status 블록과 대응한다. 본문에 `Status: Outdated` / `Status: Disputed`
  블록이 생기면 frontmatter `status`도 함께 바꾼다.

### confidential

| 값 | 의미 |
|---|---|
| `public` | 공개해도 무방 |
| `internal` | 사내 정보. 회사 밖으로 나가면 안 됨 |
| `secret` | 인사·평가·타인 실명이 얽힌 것 |

**누락 시 `secret`으로 간주한다.** 새 파일을 만들 때 반드시 채운다.

---

## 언어

- 노트 본문: 한국어. 기술 용어는 원어 그대로 (Pod, Ingress, partition …).
- 파일명: 영문 kebab-case. 한글 파일명은 링크·git·CLI에서 계속 문제를 만든다.
- `title` frontmatter에 한국어 제목을 둔다. 파일명이 아니라 이게 진짜 이름이다.
- 파일명은 **생성 후 바꾸지 않는다.** 제목이 바뀌면 `title`만 고친다.

---

## Blog Post — 세 번째 출력

wiki는 **나를 위한** 지식이고, 블로그 포스트는 **남을 위한** 글이다. 별도 저장소에 있다.

```
~/Side/comstering.github.io/posts/<slug>.md
```

### 🔒 발행 전 필수 확인

**`confidential: internal` 또는 `secret` 인 내용은 포스트로 나가지 않는다.**
블로그는 공개된다. 다음은 포스트에 절대 쓰지 않는다.

- 사내 호스트명·엔드포인트 (`*.oliveyoung.com`, `*.svc.cluster.local` 내부 주소)
- 실제 리소스명·realm·계정 식별자
- 동료 실명, 1on1·인사 관련 내용
- 사업 수치 (사용자 비중, 매출, 내부 규모)

**일반화해서 쓴다.** 구체 값은 `{placeholder}` 나 예시 값으로 바꾼다.
기존 포스트들이 `10.0.0.0/16`, `{cluster name}` 처럼 처리한 방식을 따른다.

### 포스트 frontmatter

```yaml
---
title: "EKS에 Cilium CNI 설치하기 (with CNI Chaining AWS VPC CNI Plugin)"
description: "Cilium CNI Chaining을 통해서 VPC CNI와 Cilium CNI를 함께 사용해보자"
date: "2025-09-01"
categories: [infra]
tags: [infra, kubernetes, k8s, eks, cilium, cni, vpc, taint, helm]
thumbnail: "eks-cilium.png"
---
```

- 값은 **큰따옴표**로 감싼다 (wiki frontmatter와 다르다)
- `categories` — `infra` · `project` · `backend` · `frontend` · `note` 중에서
- 파일명 = slug = URL id
- `thumbnail` → `public/images/posts/thumbnails/<name>`
- 본문 이미지 → `/images/posts/contents/<slug>/<name>.png`

### wiki와 글투가 다르다

| | wiki | post |
|---|---|---|
| 독자 | 나 | 처음 보는 사람 |
| 전제 | 내 맥락을 안다 | 맥락을 모른다 |
| 문체 | 축약. 판단과 근거만 | **왜 이 문제를 만났는지부터** 서술 |
| 결론 | `Status:` 블록으로 미결 표시 | 미결은 빼거나 "다음 포스팅에서" 로 |

포스트는 **문제 → 원인 → 해결 → 결과** 흐름으로 쓴다. 기존 포스트들의 구조다.

### 지금은 흐름이 반대다

정방향은 `raw/ → wiki/ → post`. 그런데 **블로그가 wiki보다 앞서 있다.**
`install-cilium-eks`(2025-09-01)가 `raw/kubernetes/eks-cilium.md`(2025-05)보다 훨씬 완성도가 높다.

그래서 기존 포스트는 `raw/blog/` 에 **발행 시점 스냅샷**으로 편입해 소스로 쓴다.
블로그 원본이 갱신돼도 스냅샷은 따라가지 않는다 — 갱신됐으면 다시 인제스트한다.

---

## Lint

스킬의 3등급(자동수정 / 기계보고 / 판단보고)을 그대로 따른다. 추가 점검 항목:

- `confidential` 필드 누락
- H1 제목 누락 (근거 검증이 조용히 실패한다)
- frontmatter에 날짜·숫자 모양 값 (fidelity 오탐을 만든다)
- frontmatter `status` 와 본문 Status 블록 불일치
- `wiki/index.md` 의 Updated 와 문서 blockquote `Updated:` 불일치
- 본문에서 편집자 주석을 `>` blockquote로 작성 (스크립트가 인용문으로 보고 근거를 요구한다)
- 한글 파일명

`python3 .agents/skills/karpathy-llm-wiki/scripts/check_evidence.py .` — 읽기 전용, 근거 검증용.

---

## Session Digest — 하루치 대화 자동 요약

추출 스크립트: `python3 .claude/scripts/session-digest.py [YYYY-MM-DD]`
→ 그날 세션들의 제목·repo·브랜치·턴수·사용자 프롬프트를 JSON으로 뱉는다.
**스크립트는 요약하지 않는다.** 기계가 할 수 있는 추출까지만 하고, 요약은 에이전트가 한다.

출력: `raw/sessions/YYYY-MM-DD.md`

### 규칙

- 이 vault 자신의 세션은 제외한다 (재귀 방지). 스크립트에 하드코딩되어 있다
- resume로 갈라진 jsonl은 `(project, title)` 로 합친다
- 세션마다 **무엇을 하려 했나 / 무엇이 나왔나 / 남은 것** 을 적는다
- 각 세션에 **KB 후보 여부와 이유**를 판정해 붙인다. 이게 다음 인제스트의 입력이 된다
- 턴이 0이거나 내용이 없는 세션은 개수만 세고 본문에서 뺀다
- `confidential: secret` 고정. 사내 repo 작업이 그대로 들어온다

### 🔒 git 제외

`raw/sessions/` 는 `.gitignore` 에 있다. 이 저장소는 공개 remote로 자동 백업되는데
세션 요약에는 사내 repo·티켓·엔드포인트가 그대로 들어오기 때문이다.
**이 디렉토리를 커밋 대상으로 되돌리려면 공개 repo 건을 먼저 정리해야 한다.**

세션 요약을 근거로 wiki 문서를 쓸 때도 사내 식별자를 그대로 옮기지 않는다.

---

## 범위 밖

`Private/` 는 이 파이프라인 대상이 아니다. 인제스트하지 않고, wiki에 올리지 않는다.

# Information Retrieval(IR) 프로젝트 — 마스터 프롬프트 v2

> **사용법:** 아래 `---`로 감싼 블록 전체를 Cursor·Claude 등 **새 채팅의 첫 메시지**로 붙여넣으세요. `[...]` 플레이스홀더만 채우면 됩니다.
>
> **이 레포(`ir-openclaw`):** Phase 1(BM25 CLI)은 완료. Phase 2·eval·벡터는 이 프롬프트로 이어서 구현합니다.

---

# Information Retrieval(IR) 프로젝트 — 마스터 프롬프트

## 역할 및 목표

당신은 **Information Retrieval(IR) 시스템을 설계·구현·평가하는 시니어 엔지니어**입니다.

**목표:** 사용자가 정의한 도메인·코퍼스·쿼리에 대해, **재현 가능하고 측정 가능한** 검색·검색증강(RAG) 파이프라인을 구축합니다.

**행동 원칙:**

- 요구사항이 불명확하면 **가정을 명시**하고, 최소 질문으로 범위를 확정한 뒤 구현합니다.
- MVP는 **동작하는 end-to-end 경로**(수집 → 인덱싱 → 검색 → 평가)를 먼저 완성하고, 이후에 정교화합니다.
- 기존 코드베이스가 있으면 **구조·네이밍·테스트 방식을 따르고**, 불필요한 대규모 리팩터는 하지 않습니다.
- 모든 변경은 **검증 가능**해야 합니다(테스트, 평가 스크립트, 샘플 쿼리).

**프로젝트 컨텍스트 (사용자가 채움):**

- 경로: `[예: /path/to/ir-project]`
- 목적: `[예: 사내 문서 검색, 논문 RAG, 고객 FAQ]`
- 언어/로케일: `[예: ko+en 혼합]`
- 기존 자산: `[없음 / ir-openclaw 스타터 / 벡터 DB만 / UI만 등]`

---

## 프로젝트 범위 (선택 및 우선순위)

구현 전에 아래 모듈 중 **이번 스프린트에 포함할 항목**을 체크하고, 나머지는 “다음 단계”로 문서화하세요.

| 모듈 | 설명 | MVP 권장 |
|------|------|----------|
| **문서 수집(Ingestion)** | 파일/API/크롤링, 메타데이터 추출 | ✅ |
| **전처리·청킹** | 정규화, 토큰화, 긴 문서 분할 | ✅ (단순 청킹) |
| **역색인(BM25/키워드)** | inverted index, BM25/TF-IDF | ✅ |
| **임베딩·벡터 검색** | dense retrieval, ANN | △ (2단계) |
| **하이브리드 검색** | sparse + dense fusion (RRF 등) | △ |
| **재순위(Re-ranking)** | cross-encoder, LLM rerank | 선택 |
| **RAG** | retrieve → context → generate | 선택 |
| **필터·메타데이터** | 날짜, 태그, ACL | 선택 |
| **평가(Eval)** | labeled qrels, 지표, 회귀 테스트 | ✅ |
| **API / CLI / UI** | 소비자 인터페이스 | ✅ CLI 최소 |
| **관측(Observability)** | 로그, 쿼리 로그, latency | △ |
| **에이전트 연동** | OpenClaw/MCP/봇 | 선택 (Optional) |

**명시적 비범위(Out of scope)** 도 함께 적으세요. 예: “프로덕션 멀티테넌트”, “실시간 크롤링”, “파인튜닝”.

---

## 기술 스택 가이드

**패키지 매니저**

- 프로젝트에 이미 `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock` 등이 있으면 **그 매니저를 따릅니다**.
- **락파일·매니저가 없으면 `bun`을 사용**합니다.

**런타임·언어 (택1 또는 조합, 사용자 지정 우선)**

- **경량 IR 코어 (권장 패턴):** Node.js **≥22.16**, ESM, **TypeScript** (`src/*.ts`) — BM25/CLI/배치 평가
- **대안:** Python (`src/*.py`) — 동일 모듈 경계 유지
- **API·서비스:** Hono, FastAPI, Express 등
- **프론트:** React/Next.js — 검색 UI·데모

**테스트**

- **순수 Node IR 코어 (이 레포 포함):** **`node --test`**, `test/*.test.ts`
- **React/Next.js UI 추가 시:** **Vitest**, 테스트는 `test/` 디렉터리
- **Python:** pytest
- TypeScript 사용 시: `tsc --noEmit` 또는 `bun run typecheck`로 타입 검사

**검색·저장 (요구에 맞게 선택)**

- **MVP:** 메모리/파일 기반 inverted index (JSON/디스크 스냅샷)
- **확장:** SQLite FTS5, Elasticsearch/OpenSearch, Meilisearch, Typesense
- **벡터:** sqlite-vec, LanceDB, Chroma, Qdrant, pgvector 등

**임베딩**

- 로컬(sentence-transformers, Ollama) vs API(OpenAI, Voyage 등) — **비용·지연·오프라인** 기준으로 선택

### ir-openclaw 스타터 (현재 레포, 2026-05 기준)

| 항목 | 값 |
|------|-----|
| 패키지명 | `ir-openclaw` |
| Node | `>=22.16.0` |
| 소스 | `src/tokenize.ts`, `indexer.ts`, `cli.ts` |
| 코퍼스 | `data/corpus/*.md`, `*.txt` (하위 폴더 재귀) |
| CLI | `bun run ir search "<query>"` (**`search`만** — `index`/`eval` 미구현) |
| 테스트 | `bun run test` → `node --test` |
| 타입 검사 | `bun run typecheck` |
| OpenClaw | `scripts/run-openclaw.mjs`, 포트 **19809**, `openclaw/openclaw.json` |

**완료:** BM25, NFKC 토큰화(한·영 stopwords), 스니펫, 기본 테스트 2건.

**미완:** `index`/`eval` CLI, `data/eval/`, 인덱스 디스크 스냅샷, 메타·청킹, 벡터, RAG.  
**알려진 제약:** `search` 호출마다 코퍼스 전체를 재로드·재인덱싱함 → Phase 2에서 `index` + 스냅샷 우선.

---

## 디렉터리·모듈 구조 제안

기존 구조가 있으면 **확장**하고, 없으면 아래를 기본 템플릿으로 제안·생성합니다.

```
project-root/
├── data/
│   ├── corpus/           # 원문 (.md, .txt, jsonl 등)
│   ├── eval/             # queries.jsonl, qrels (선택)
│   └── indexes/          # 빌드된 인덱스 스냅샷 (gitignore 권장)
├── src/
│   ├── ingest/           # 로더, 메타데이터, 청킹 (선택)
│   ├── tokenize.ts       # 정규화, stopwords, 다국어
│   ├── indexer.ts        # inverted index, BM25
│   ├── embed/            # (선택) 임베딩, 벡터 저장
│   ├── search.ts         # (선택) sparse/dense/hybrid 통합
│   ├── rag/              # (선택) 컨텍스트 조립
│   └── cli.ts            # index, search, eval 명령
├── test/
│   └── indexer.test.ts   # node:test
├── scripts/              # OpenClaw 래퍼, eval 배치 등
├── openclaw/             # (선택) openclaw.json, .example
├── docs/                 # (선택) 이 마스터 프롬프트 등
├── .openclaw-state/      # OpenClaw 상태 (gitignore)
├── .env.example
├── README.md
├── tsconfig.json         # TS 사용 시
└── package.json
```

**모듈 경계:** `ingest` → `indexer` → `search`/`cli` → `eval` — 단방향 의존, 순환 import 금지.

---

## 단계별 구현 체크리스트

### Phase 0 — 정렬 (반나절)

- [ ] 코퍼스 출처·포맷·갱신 주기 확정
- [ ] 쿼리 유형 정의 (키워드, 자연어, 필터 조합)
- [ ] 성공 기준: 예) “top-5에 정답 문서 80% 이상 (개발용 golden set)”
- [ ] `.env.example` 작성, 시크릿은 `.env`만 (커밋 금지)

### Phase 1 — MVP (키워드 검색)

- [ ] `data/corpus/` 샘플 + 실제 문서 1종 이상 연결
- [ ] 토큰화 (다국어: Unicode `\p{L}\p{N}`, NFKC, stopwords)
- [ ] inverted index + **BM25** 랭킹
- [ ] `cli search "<query>"` — id, score, snippet 출력
- [ ] 단위 테스트: 토큰화, 랭킹 순서, 빈 쿼리
- [ ] README: 설치, 검색 예시

> **ir-openclaw:** 위 항목은 대부분 완료. 신규 프로젝트만 Phase 1부터 진행.

### Phase 2 — 품질 (메타·청킹·스냅샷)

- [ ] 문서 메타: title, source, date, author, tags
- [ ] 긴 문서 **청킹** + chunk id
- [ ] **`cli index`** — 인덱스 빌드·`data/indexes/` 저장·재로드
- [ ] `search`는 스냅샷 로드만 (매 요청 전체 재인덱싱 제거)
- [ ] 스니펫 하이라이트·title 필드 부스팅

> **ir-openclaw 다음 우선 작업:** `index` 서브커맨드 + 디스크 스냅샷.

### Phase 3 — 벡터·하이브리드 (선택)

- [ ] 임베딩 파이프라인 + 벡터 저장소
- [ ] hybrid: BM25 + dense, **RRF** 또는 가중 합
- [ ] (선택) cross-encoder / LLM rerank

### Phase 4 — RAG (선택)

- [ ] retrieve → top-k 청크 → context budget → LLM
- [ ] 인용(citation): chunk id / source
- [ ] 근거 없으면 “모른다” 정책

### Phase 5 — 제품화

- [ ] HTTP API (`POST /search`, `POST /ask`)
- [ ] (선택) 웹 UI
- [ ] CI: 테스트 + eval 회귀

### Phase 6 — 운영 (선택)

- [ ] 쿼리 로그, latency p95, 인덱스 버전 관리
- [ ] 증분 인덱싱, ACL, rate limit

---

## 데이터·인덱스·벡터 DB 설계 질문

구현 전 아래에 답을 적거나 사용자에게 질문하세요.

**코퍼스**

1. 문서 단위는 무엇인가? (파일, URL, DB row, 메시지)
2. 갱신 빈도·최종 일관성 요구는?
3. 중복·버전 문서 처리 정책은?
4. 다국어 비율·도메인 용어 사전이 필요한가?

**청킹**

5. 청크 크기·오버랩은?
6. 구조 보존(제목, 코드, 표)이 필요한가?

**인덱스**

7. sparse만으로 충분한가, semantic이 필수인가?
8. 인덱스 크기·메모리 상한은?
9. 필터 가능 메타데이터 필드는?
10. 삭제·ACL 반영 방식은?

**벡터 DB (해당 시)**

11. 예상 벡터 수·차원·QPS는?
12. 메타데이터 필터 + ANN 동시 지원이 필요한가?
13. 임베딩 모델 변경 시 재인덱싱 전략은?

**평가 데이터**

14. golden queries / qrels 라벨링 주체·방법은?
15. train vs holdout 분리가 필요한가?

---

## 평가 지표 및 테스트 전략

### 검색 품질 지표 (문서 단위 qrels 기준)

| 지표 | 의미 | 사용 시점 |
|------|------|-----------|
| **Precision@k** | top-k 중 relevant 비율 | sanity |
| **Recall@k** | relevant 중 top-k 포착 | recall 중시 |
| **MRR** | 첫 정답 순위의 역수 평균 | 단일 정답 |
| **nDCG@k** | 순위 가중 관련도 | 다중 relevant |
| **MAP** | 평균 정밀도 | 전통 IR 벤치 |

**RAG (선택):** context precision/recall, faithfulness, citation accuracy

### 테스트 전략

1. **단위 테스트:** tokenize, index build, BM25, empty corpus (`node --test`)
2. **골든 테스트:** `data/eval/queries.jsonl` + qrels — **`cli eval`** 또는 스크립트
3. **회귀 게이트:** MRR@5 / nDCG@10 baseline 대비 하락 시 CI 실패
4. **스모크:** 샘플 쿼리 3~5개

**eval 데이터 형식 예시 (JSONL):**

```json
{"query_id":"q1","query":"retrieval augmented generation","relevant":["doc-a.md","doc-b.md"]}
```

---

## 산출물 정의

| 산출물 | 내용 |
|--------|------|
| **README.md** | 목표, 아키텍처, 설치, 사용법, 한계 |
| **`.env.example`** | API 키·경로 (값 없음) |
| **CLI** | `index`, `search`, `eval` (또는 동등) |
| **API (선택)** | OpenAPI 또는 엔드포인트 문서 |
| **테스트** | `test/` 자동 테스트 |
| **eval 리포트** | 지표 표 + baseline 대비 |
| **데모 (선택)** | 웹 UI 또는 notebook |

---

## 제약 및 품질 기준

**보안·비밀**

- API 키·`openclaw.json` 내 시크릿을 **저장소에 커밋하지 않음**
- 예시만 `openclaw.json.example`, `.env.example` 커밋
- `.openclaw-state/` — 로컬 상태, gitignore

**Git·협업**

- **git commit / push는 사용자가 명시적으로 요청할 때만**
- 시크릿·`.env`·토큰 파일 제외

**코드 품질**

- 요청 범위만 수정 — 무관한 리팩터·마크다운 남발 금지
- 기존 스타일·`node --test`·TS import 관례 준수
- 새 의존성은 필요 최소

**다국어**

- 한·영 혼합: NFKC, stopwords, 조사 처리 정책을 README에 문서화

---

## [Optional] OpenClaw / 에이전트 연동

**해당할 때만** 진행합니다.

**이 레포(ir-openclaw) 패턴:**

- `scripts/run-openclaw.mjs` — `.env`의 `OPENCLAW_*`로 config/state 고정
- `openclaw/openclaw.json.example` — gateway `loopback:19809`, token auth, Telegram(선택)
- `OPENCLAW_LAUNCHD_LABEL=ai.openclaw.ir-project` — 다른 OpenClaw 인스턴스와 분리
- 스크립트: `bun run gateway`, `doctor`, `mcp`
- **`agents.defaults.workspace`는 현재 `".."`** (상위 `projects/`) — IR만 보려면 `ir/`로 좁힐 것
- IR 코어(`src/`)와 게이트웨이 설정(`openclaw/`) **분리**
- 에이전트 검색: MCP 도구 또는 SKILL로 `search(query)` 래핑
- `skills-lock.json`이 있으면 스킬 해시·커밋 정책 준수

**체크리스트:**

- [ ] `.env`에 `TELEGRAM_BOT_TOKEN` 등, 예시는 `.env.example`
- [ ] 게이트웨이 포트·바인딩 충돌 확인
- [ ] 에이전트 프롬프트에 “검색 결과 인용 필수”

**비해당 시:** 이 섹션 생략, CLI만 제공.

---

## 작업 방식 (에이전트에게)

1. **탐색:** README, `package.json`, `src/`, `data/`, `test/` 읽고 현재 Phase 판별
2. **계획:** 이번 스프린트 Scope 5줄 이내 → 확인 또는 가정 명시 후 진행
3. **구현:** 체크리스트 순서, 테스트·eval 동반
4. **검증:** `bun run test`, `bun run typecheck`, eval 스크립트 결과 보고
5. **문서:** README “Next steps”를 실제 상태로 갱신

**응답 언어:** 사용자가 한국어를 요청하면 **한국어**로 설명, 코드·CLI는 영문 관례 유지.

**첫 응답에 포함:**

- 현재 상태 요약 (ir-openclaw면 Phase 1 완료 여부 명시)
- 이번 Scope (포함/제외)
- 바로 실행할 3~5개 작업
- 미답변 설계 질문 3개 (필요 시)

---

## 시작 명령 (사용자가 붙일 수 있음)

```
위 마스터 프롬프트에 따라 [프로젝트 경로]의 IR 시스템을 구축/확장해 주세요.

이번 목표: [예: ir/ Phase 2 — cli index + data/indexes 스냅샷 + eval 골든셋 10쿼리]
스택 선호: [없음 / Node 22+ TS+bun / Python / Next.js UI]
OpenClaw 연동: [필요 / 불필요]
```

---

**끝 — 이 프롬프트 블록을 복사해 새 세션에 붙여넣으세요.**

---

## 부록: ir-openclaw와의 관계

로컬 `ir/`는 **Phase 1 완료** 스타터입니다. 이 문서(v2)는 재검증(2026-05)을 반영했으며, 다음 단계는 Phase 2(`index` CLI·스냅샷)·`data/eval/`·벡터·RAG 순으로 같은 `src/` 구조 위에 확장하면 됩니다.

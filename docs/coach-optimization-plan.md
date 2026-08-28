# AI Coach Core — Full Optimization Plan (Remaining 10 items)

> Cơ sở: `apps/api/app/domains/coach/coach_service.py:35`, `context_resolver.py:18`, `prompt_builder.py:61`, `tool_registry.py:18`, `tools_impl.py:134`, `proactive_engine.py:15`, `apps/web/features/coach/*:1`, `app/speaking/page.tsx:114`, `app-shell.tsx:38`, `domains/ai/router.py:91`

## 1. Mục tiêu
Tối ưu còn lại tập trung: **latency cảm nhận + chi phí LLM + độ chính xác evidence + độ bền UX** cho Speaking, giữ nguyên behavior cross-cutting.

## 2. Ma trận ưu tiên

| # | Hạng mục | File chính | Effort | Impact | Rủi ro |
|---|----------|------------|--------|--------|--------|
| 1 | Streaming CoachPanel (SSE) | `api/v1/coach.py:24`, `coach_service.py:96`, `features/coach/components/CoachPanel.tsx:8` | 3h | Latency 2.5s→0.3s | Thấp |
| 2 | Cache Progress/Learning summary (TTL 5′) | `app/progress/page.tsx:20`, `app/learning/page.tsx:25`, `coach/context_resolver.py:18` | 1h | -1 LLM call/view | Thấp |
| 3 | Floating collision mobile | `CoachFloatingButton.tsx:10`, `app/speaking/page.tsx:282` | 0.5h | UX | Thấp |
| 4 | N+1 resolver gộp query | `context_resolver.py:148-170` | 2h | -2 roundtrips | Thấp |
| 5 | Metric prefix map chuẩn | `domains/analytics/domain/metric_definitions.py:1`, `tools_impl.py:134` | 1h | Chính xác | Thấp |
| 6 | Proactive persist + dedup thực | `proactive_engine.py:15`, `insight_deduper.py:7`, `analytics/models.py:120` | 2h | Anti-spam thực | Trung |
| 7 | A11y (aria, role, keyboard) | `CoachPanel.tsx`, `CoachQuickActions.tsx:8` | 1h | WCAG | Thấp |
| 8 | Token whitelist theo mode | `prompt_builder.py:61`, `coach/context_resolver.py:18` | 2h | -600 tok/turn | Thấp |
| 9 | Mastery write batch | `learning/mastery_engine.py:33`, `learning/exercise_session_service.py` | 3h | -WAL pressure | Trung |
| 10 | Audit logs + observability | `analytics/models.py:154`, `coach_service.py:169` | 2h | Debug | Thấp |

## 3. Chi tiết từng hạng mục

### 1) Streaming
- **Hiện trạng:** `CoachPanel` chờ `AIRouter.generate()` full JSON (§50) rồi render block. `router.py:401` đã có `stream()` với `AIStreamEventType.TEXT_DELTA`.
- **Plan:**
  - Thêm `POST /coach/chat/stream` (SSE) trong `api/v1/coach.py:24` — gọi `AIRouter.stream(task=ai_task, request=req)` yield `text/event-stream`.
  - Frontend: `services/coachCoreApi.ts:14` thêm `chatStream(): AsyncGenerator`, `CoachPanel.tsx:8` giữ buffer, render incremental `response`, cuối cùng parse JSON `evidence/recommendations/next_action` khi `COMPLETED`.
  - Fallback non-stream nếu provider không hỗ trợ.
- **Verify:** manual streaming visible <500ms, `pytest` still pass, `npm run build` typecheck.

### 2) Cache summary
- **Hiện trạng:** `progress/page.tsx:20` + `learning/page.tsx:25` gọi `coachCoreApi.chat()` mỗi mount, không SWR.
- **Plan:**
  - Backend: `context_resolver.py:18` đã có `_CONTEXT_CACHE 60s`; thêm `coach_summary_cache` (Redis `redis_manager` hoặc in-memory 5′) key=`user_id:route:hash`.
  - Frontend: `useSWR` hoặc `useEffect` + `sessionStorage` TTL 5′, hiển thị cached + `isValidating` spinner.
  - Invalidate khi `ExerciseAttempt` completed hoặc `LearnerMemory` updated (hook `learner_memory_worker`).
- **Verify:** refresh progress không gọi thêm LLM trong 5′ (check network).

### 3) Floating collision
- Đã fix `CoachFloatingButton.tsx:10` calc, nhưng `app/speaking/page.tsx:282` còn nút `Hỏi Coach` `bottom-24 right-4` tách rời. Gộp logic: nếu `app-shell` đã mount global button, speaking chỉ hiện quickActions bar, không render thêm FAB. Dùng `shouldShowCoach` flag theo pathname.

### 4) N+1 resolver
- **Hiện:** 3 query riêng cho `TurnAnalysis`, `PronunciationAttempt`, `SessionAnalysis` mỗi resolve.
- **Plan:** Gộp 1 `selectinload` cho `ConversationSession.turns` đã có, nhưng tách riêng  `select(TurnAnalysis).where(session_id.in_(ids))` OK; chỉ cần thêm `joinedload` cho `Attempt.metrics_json` và dùng `asyncio.gather()` cho 3 query song song thay vì tuần tự.
- **File:** `context_resolver.py:148` wrap 3 `await` bằng `await asyncio.gather(*coros)`.

### 5) Metric prefix
- **Hiện:** `tools_impl.py:134` `_get_filtered_metrics` dùng `k.startswith(prefix)` với prefix `reflex/keigo/pitch` — `keigo_register_accuracy` OK nhưng `pitch_mora_accuracy` key là `pitch_mora_accuracy` (prefix pitch) OK, nhưng `mora_timing` là pronunciation — cần map chuẩn.
- **Plan:** Tạo `MODE_METRIC_KEYS: dict[CoachMode, set[MetricKey]]` trong `analytics/domain/metric_definitions.py:1`, dùng `key in set` thay vì `startswith`.

### 6) Proactive persist
- **Hiện:** `proactive_engine.py:15` `return insights` không ghi DB; `insight_deduper` check `InsightRecord` nên luôn miss.
- **Plan:** Sau `evaluate_for_user()`, loop insights → tạo `InsightRecord` (type=insight_type, metric_key, lifecycle=new, expires_at=+7d) và `CoachInsightDeduper` check trước khi insert. Thêm `POST /coach/proactive/dismiss` cập nhật `lifecycle=seen`.
- **Verify:** refresh 2 lần trong 48h không show lại insight đã dismiss.

### 7) A11y
- `CoachPanel.tsx` input thiếu `aria-label="Hỏi Coach"`, `CoachQuickActions.tsx:8` buttons cần `role="list"` + `aria-label`. Thêm `Esc` đóng panel, `TrapFocus`.

### 8) Token whitelist
- **Hiện:** `metrics_summary` dump toàn bộ 15 metrics (~800 chars) dù intent PITCH chỉ cần 2.
- **Plan:** `prompt_builder.py:61` thêm `MODE_METRIC_WHITELIST = {PITCH: {pitch_accuracy, mora_timing}, REFLEX: {reflex_accuracy, ...}}`. Trước khi build `trend_block`, lọc `overview.metrics` theo whitelist + `bottleneck` vẫn giữ.
- **Saving:** ~500-700 tokens cho pitch/keigo turn, test với `PromptBudgetGuard.estimate_tokens()` log.

### 9) Mastery batch
- **Hiện:** mỗi `submit` gọi `MasteryEngine.calculate_mastery_delta()` + `db.commit()` ngay, WAL lớn khi reflex `autoNext` 20/min.
- **Plan:** Thêm `LearningItem` update queue trong `ExerciseSessionService` — `asyncio.Queue` + flush 3s hoặc 5 items, dùng `UPDATE ... WHERE` batch. Hoặc đơn giản: `review_interval` không cần immediate commit, dùng `add + flush` và commit 1 lần cuối session.
- **Risk:** cần test regression `test_phase12_optimization.py`.

### 10) Audit logs
- Thêm `coach_tool_calls` table (Alembic) hoặc ít nhất log `evidence_refs_json` enrichment: trong `coach_service.py:169` `_persist()` thêm `tool_calls_json` và `latency_ms` breakdown per tool. Thêm `/coach/tools` log view.

## 4. Thứ tự thực thi đề xuất

**Đợt 1 (Quick wins, 4.5h):** 1,2,3 → giảm latency + bill ngay.
**Đợt 2 (Medium, 6h):** 4,5,6,7 → chính xác + anti-spam.
**Đợt 3 (Deep, 7h):** 8,9,10 → tối ưu token sâu + bền vững.

Dependencies: 1 không phụ thuộc; 2 cần 4 xong càng tốt; 6 cần 5; 8 cần 4; 9 independent.

## 5. Tiêu chí chấp nhận mỗi đợt

- Đợt1: streaming visible <500ms, cache hit rate >70% trên progress, không còn double FAB mobile.
- Đợt2: proactive sau dismiss không hiện lại 48h, metric whitelist test pass, a11y axe 0 error.
- Đợt3: token avg giảm ≥500/turn (log), mastery batch không break existing tests.

## 6. Câu hỏi chốt trước khi code đợt1

1. Bạn muốn stream dạng **SSE `text/event-stream`** (Next.js native) hay **WebSocket**? SSE đơn giản hơn cho Vercel.
2. Cache summary bạn muốn **Redis 5′** (đã có `redis_manager`) hay **in-memory + sessionStorage** đủ? Redis bền hơn khi scale.

# User Prompts Log (`prompts.md`)

This file maintains a chronological log of all prompts, instructions, and specifications provided by the user throughout the development of the English Learning Agent project.

---

## Prompt 1: Initial Schema Specifications & Planning Request
* **Date:** 2026-09-16 10:35:40 (Local Time)
* **Category:** Architecture & Data Modeling

### Prompt:
```text
Even if you rely on a single model family (e.g., GPT-4o or Claude 3.5), keep the model tracking fields. APIs undergo silent updates and explicit version deprecations (e.g., `gpt-4o-2024-05-13` shifting to a newer date). Tracking the exact version hash, alongside token counts and latency, is the only way to catch when an upstream provider update suddenly degrades your response quality, slows down your app, or spikes your bill.

Here is the updated schema incorporating all the scalability, concurrency, and normalization improvements.

### 1. BaseTimeModel

Abstract model — does not create a separate database table.

* created_at (Indexed for time-based partitioning)
* updated_at

### 2. Language

* id (BigAutoField)
* code (e.g., 'en-US')
* name
* is_active
* created_at
* updated_at

### 3. TopicTag

Normalized table for analytics (e.g., "Travel", "Business").

* id (BigAutoField)
* name
* created_at
* updated_at

### 4. WeaknessTag

Normalized table for analytics (e.g., "Past Tense", "Prepositions").

* id (BigAutoField)
* name
* language — Foreign Key to Language
* created_at
* updated_at

### 5. User

* id (BigAutoField)
* username, email, password, etc.
* is_active — (Use this for soft deletes instead of hard CASCADE deletion)

### 6. UserLanguage

* id (BigAutoField)
* user — Foreign Key to User
* language — Foreign Key to Language
* current_cefr_level
* target_goal
* is_native
* is_learning
* is_primary
* total_practice_seconds — (Must be updated via DB atomic `F()` expressions)
* total_sessions_completed — (Must be updated via DB atomic `F()` expressions)
* created_at
* updated_at
* **Constraints:**
* Unique (user, language)
* Unique (user) WHERE is_primary = True



### 7. Exercise

* id (BigAutoField)
* language — Foreign Key to Language
* title
* prompt_text
* skill_focus
* cefr_level
* created_at
* updated_at
* **Relationships:** Many-to-Many with `TopicTag`

### 8. ConversationSession

* id — UUID
* user_language — Foreign Key to UserLanguage
* exercise — Foreign Key to Exercise (on_delete=SET_NULL)
* session_title
* is_active
* conversation_summary
* turn_counter — Integer, default 0 (Incremented under a row lock before creating a turn to prevent race conditions)
* snapshot_prompt_text — Text (Snapshots the Exercise prompt so historical sessions remain intact if the Exercise is edited later)
* created_at
* updated_at

### 9. ConversationTurn

* id (BigAutoField - plan for partitioning)
* session — Foreign Key to ConversationSession
* role — User or Agent
* turn_sequence — Integer
* text_content
* llm_model_version — String (Null for user turns)
* latency_ms — Integer (Null for user turns)
* input_tokens — Integer (Null for user turns)
* output_tokens — Integer (Null for user turns)
* created_at
* updated_at
* **Constraints:** Unique (session, turn_sequence)

### 10. Recording

* id (BigAutoField - plan for partitioning)
* turn — One-to-One relationship with ConversationTurn
* audio_file — String/URL (Pointer to S3/Cloud Storage, not raw bytes)
* mime_type
* duration_seconds
* file_size_bytes
* status — Uploaded, Processing, Analyzed, Failed (Indexed for queue polling)
* error_message
* created_at
* updated_at

### 11. AnalysisResult

* id (BigAutoField - plan for partitioning)
* recording — **Foreign Key to Recording** (Many-to-One, allows re-running analysis)
* is_current — Boolean (Flags the active result)
* estimated_cefr
* grammar_feedback — JSON
* vocabulary_feedback — JSON
* fluency_metrics — JSON
* word_timestamps — JSON
* asr_model_version
* llm_model_version
* prompt_version
* latency_asr_ms
* latency_llm_ms
* input_tokens
* output_tokens
* raw_llm_response
* created_at
* updated_at
* **Relationships:** Many-to-Many with `WeaknessTag`
* **Constraints:** Unique (recording) WHERE is_current = True
i have to make these changes to models, make implementation plan
```

---

## Prompt 3: Core Model Refactor & Language Deletion Protection
* **Date:** 2026-09-21 09:14:35 (Local Time)
* **Category:** Domain Modeling & Architecture Refactoring

### Prompt:
```text
Move CEFRLevel out of User into a shared choices module.
Change UserLanguage.language from CASCADE to PROTECT.
Eventually stop treating user.cefr_level and user.target_goal as actual User fields; use the UserLanguage relationship explicitly.
make these changes
```

### Outcome & Summary:
- Created centralized `core.choices.CEFRLevel(models.TextChoices)` and decoupled choices from `User`.
- Updated `Exercise.cefr_level`, `AnalysisResult.estimated_cefr`, and `UserLanguage.current_cefr_level` to use the shared choice module.
- Changed `UserLanguage.language` ForeignKey deletion rule from `CASCADE` to `models.PROTECT` and generated migration `0002_alter_userlanguage_language.py`.
- Deprecated virtual properties `User.cefr_level`, `User.target_goal`, and `User.native_language`.
- Refactored `NextExerciseView`, `ProgressMetricsView`, `UserSerializer`, `RegisterSerializer`, and test fixtures to query `user.primary_user_language` and `user.user_languages` explicitly.
- Added test verifying `django.db.models.ProtectedError` on deleting an enrolled `Language`.

---

## Prompt 4: End-to-End Multi-Language Learning Support
* **Date:** 2026-09-21 09:29:33 (Local Time)
* **Category:** Feature Enhancement & Multi-Language Architecture

### Prompt:
```text
what if user is learning more than 1 language
[User approved implementation plan: "yes"]
```

### Outcome & Summary:
- Added dedicated language management endpoints under `apps.authentication`:
  - `GET /api/auth/languages/`: List all languages the learner is studying with isolated metrics.
  - `POST /api/auth/languages/`: Enroll in an additional language (preventing duplicate enrollments).
  - `GET/PATCH/DELETE /api/auth/languages/<id>/`: View, update CEFR/goal, or unenroll from a language.
  - `POST /api/auth/languages/<id>/set-primary/`: Atomically switch active primary language in a transaction.
- Scoped `NextExerciseView` (`/api/exercises/next/?language=<code>`):
  - Added `?language=` query filter for language-specific recommendations and weakness tracking.
- Isolated `ProgressMetricsView` (`/api/recordings/progress/?language=<code>`):
  - Added `?language=` query filter so speaking speed (WPM) and pause metrics are isolated per language.
- Enhanced `RecordingUploadSerializer`:
  - Audio uploads now auto-match the exercise's target language and associate turns with the appropriate `UserLanguage`.
- Expanded test suite to **24 automated tests** (all passing).

---

## Prompt 5: Centralization of Model Choices into `core.choices`
* **Date:** 2026-09-21 10:06:08 (Local Time)
* **Category:** Code Architecture & Refactoring

### Prompt:
```text
there are choices in the recordings app model and exercises app model , shouldnt they all be in choices.py
yes
```

### Outcome & Summary:
- Centralized all domain choices and state machines into `backend/core/choices.py`:
  - `CEFRLevel`: Language proficiency levels (`A1` to `C2`).
  - `SkillFocus`: Pedagogical focus areas (`grammar`, `vocabulary`, `fluency`, `pronunciation`, `mixed`).
  - `ExerciseSourceType`: Content origins (`static`, `generated`).
  - `ConversationRole`: Dialogue turn roles (`user`, `agent`).
  - `RecordingStatus`: Audio pipeline states (`uploaded`, `processing`, `analyzed`, `failed`).
- Maintained class-level aliases on models (`Exercise.SkillFocus`, `Exercise.SourceType`, `ConversationTurn.Role`, `Recording.Status`) for backward compatibility with zero breaking changes.
- Refactored `exercises.views` (`weakness_map`) to use `SkillFocus` directly.
- Validated with `makemigrations --check` (no schema drift detected).
- Verified test suite: all **24 automated tests** pass cleanly.

---

## Prompt 6: Pre-Configured API Tests in Postman Suite
* **Date:** 2026-09-21 10:10:25 (Local Time)
* **Category:** Testing, Developer Experience & Postman Automation

### Prompt:
```text
now add pre-configured api tests for all apis in the postman folder
```

### Outcome & Summary:
- Created complete Postman v2.1 test suite in `postman/`:
  - `postman/collections/EnglishLearningAgent.postman_collection.json`: 20 requests organized across 4 modules (Authentication, Multi-Language Management, Exercises, Recordings & Progress) with automated test assertions and dynamic environment variable chaining (`accessToken`, `enrolledLanguageId`, `exerciseId`, `recordingId`).
  - `postman/environments/EnglishLearningAgent.local.postman_environment.json`: Local development environment variables (`baseUrl: http://127.0.0.1:8000`).
  - `postman/sample_audio.webm`: Test fixture for audio upload verification.
  - `postman/README.md`: Step-by-step execution guide for VS Code Postman extension and Postman Desktop.
- Validated all 20 API request contracts and schemas against the live Django development server.
- Maintained all **24/24 unit tests** passing.

---

## Prompt 7: Phase 4 Implementation — Frontend Core Practice Loop & Audio Recording
* **Date:** 2026-09-21 14:15:10 (Local Time)
* **Category:** Frontend Architecture & Interactive Audio Practice

### Prompt:
```text
is implementation plan for phase 4 good?
```

### Outcome & Summary:
- Validated and executed the Phase 4 Implementation Plan for the React Single Page Application (SPA).
- **Core Frontend Infrastructure**:
  - Initialized Vite + React 19 application with pure Vanilla CSS and the Zesty Lemon design system (`#FFFF66`, `#FFE566`, `#D6D58B`, `#B3B347` on `#FAFAF7`).
  - Configured state management with Zustand (`authStore.js`, `uiStore.js`) and persistent JWT storage.
  - Implemented Axios API client layer (`client.js`, `auth.js`, `exercises.js`, `recordings.js`) with automatic silent token refresh via HTTP-only cookies.
- **Audio Recording & Processing Engine**:
  - Implemented `useAudioRecorder.js` hook managing `MediaRecorder` lifecycle (`inactive`, `recording`, `paused`, `recorded`).
  - Implemented `AudioVisualizer.jsx` with real-time Web Audio API frequency analysis and dynamic bar visualization.
  - Built `AudioRecorderCard.jsx` with live status, recording timer, audio playback preview, and submission handler.
- **Practice Workspace & Instant Feedback**:
  - Created `PracticeSessionModal.jsx` displaying adaptive speaking prompts, vocabulary hints, recording engine, analyzing state, and instant feedback.
  - Built `AnalysisFeedbackCard.jsx` displaying CEFR assessment score, fluency metrics grid (WPM, pause count, filler words), grammar correction diffs, advanced vocabulary recognition, and targeted weakness tags.
  - Built `PracticePage.jsx` and `RecordingsPage.jsx`.

---

## Prompt 8: Authentication Navigation & Session Sync Resolution
* **Date:** 2026-09-21 15:02:40 (Local Time)
* **Category:** Authentication, Routing & Bug Fix

### Prompt:
```text
the problem is that im not getting past the login page even after putting valid credentials, it says login successful but i dont get to next page
```

### Outcome & Summary:
- Diagnosed asynchronous state race condition between `useAuthStore` token storage and React Router's `ProtectedRoute` redirect evaluation.
- Refactored `LoginPage.jsx` to await user profile population before executing `navigate('/', { replace: true })`.
- Updated `ProtectedRoute.jsx` to prevent premature redirects during active session rehydration.
- Verified login flow: successfully authenticated with test credentials and transitioned directly to the learner dashboard.

---

## Prompt 9: Phase 5 Implementation — Analytics Dashboard & Multi-Language Settings
* **Date:** 2026-09-21 16:30:15 (Local Time)
* **Category:** Data Visualization, Analytics & User Settings

### Prompt:
```text
onto next phase
```

### Outcome & Summary:
- Implemented Phase 5 frontend analytics and multi-language configuration layer:
- **Speech Metrics Visualizations**:
  - Built responsive pure SVG Words-Per-Minute (WPM) trendline with an Ideal Flow Zone band (110–150 WPM) and interactive data point tooltips.
  - Built `WeaknessDistributionCard.jsx` categorizing grammatical and phonetic weakness tag frequencies.
  - Added multi-window analytics filtering (`7d`, `30d`, `90d`, `all`) and language scoping.
- **Multi-Language Profile Management**:
  - Created `SettingsPage.jsx` supporting language track catalog browsing, enrollment, CEFR target level updating, and atomic primary language switching.
  - Implemented learner account settings and preferences.

---

## Prompt 10: Phase 6 Implementation — Conversational AI Coach, Speech Synthesis & Roleplay Scenarios
* **Date:** 2026-09-21 17:45:22 (Local Time)
* **Category:** Conversational AI, Roleplay Dialogues & Speech Synthesis

### Prompt:
```text
onto next phase
```

### Outcome & Summary:
- Implemented full multi-turn conversational AI dialogue partner system:
- **Backend Conversational Engine & Endpoints**:
  - Created `backend/apps/recordings/conversations.py` featuring realistic roleplay scenarios (Software Developer Job Interview `B2`, Urban Café `A2`, Border Customs `B1`, AI Ethics Debate `C1`).
  - Added REST endpoints: `GET /api/recordings/scenarios/`, `GET /api/recordings/sessions/`, `POST /api/recordings/sessions/`, `GET /api/recordings/sessions/<id>/`, `POST /api/recordings/sessions/<id>/turn/`, and `POST /api/recordings/sessions/<id>/conclude/`.
  - Enforced turn counter database row-locking and unique sequence constraints to prevent race conditions during concurrent voice replies.
- **Frontend Speech Synthesis Engine**:
  - Implemented `useSpeechSynthesis.js` utilizing the browser Web Speech API with natural voice selection, speech rate toggles (0.85x, 1.0x, 1.15x), and fallback protection.
  - Built `AudioPromptPlayer.jsx` featuring animated audio soundwave bars and speech pace control.
- **Conversational Workspaces**:
  - Built `ConversationsPage.jsx` with scenario discovery cards and dialogue session history.
  - Built `ConversationRoomPage.jsx` with real-time conversational timeline, Coach audio auto-play, inline recording dock, and expandable linguistic feedback drawer.
- **Automated Tests**:
  - Added 5 integration tests in `backend/tests/test_conversations.py` (total backend test suite expanded to **29 tests**, all passing).

---

## Prompt 11: Backend Port Conflict & Routing Disambiguation
* **Date:** 2026-09-21 19:10:05 (Local Time)
* **Category:** Infrastructure, Networking & Environment Debugging

### Prompt:
```text
Page not found (404)
Request Method:	GET
Request URL:	http://127.0.0.1:8000/?login
Using the URLconf defined in core.urls, Django tried these URL patterns, in this order:

admin/
api/auth/
api/exercises/
api/recordings/
^media/(?P<path>.*)$
The empty path didn’t match any of these.

You’re seeing this error because you have DEBUG = True in your Django settings file. Change that to False, and Django will display a standard 404 page.
why am i getting this
```

### Outcome & Summary:
- Diagnosed that user navigated directly to the Django REST API backend root URL (`http://127.0.0.1:8000/?login`) instead of the Vite frontend development server (`http://localhost:5173/login`).
- Resolved port 5173 collision, ensured Vite dev server was running cleanly with API proxy configured to forward `/api` requests to Django on port 8000.
- Provided clear developer explanation of the decoupled frontend SPA vs backend REST API architecture.

---

## Prompt 12: Project Status Audit & Milestone Review
* **Date:** 2026-09-22 10:20:18 (Local Time)
* **Category:** Project Management & Roadmap Planning

### Prompt:
```text
whats left now???
```

### Outcome & Summary:
- Conducted exhaustive architectural and functional audit across all 6 development phases:
  - Phase 1: Normalized Database Models & Concurrency Locking ✅
  - Phase 2: REST APIs & JWT Authentication ✅
  - Phase 3: Postman Test Suite Automation ✅
  - Phase 4: Audio Recording Engine & Practice Loop ✅
  - Phase 5: Progress Analytics & Multi-Language Settings ✅
  - Phase 6: Interactive AI Roleplay Dialogues & Speech Synthesis ✅
- Identified final refinement targets: UI decluttering on information-dense pages, component polish, and user acceptance testing.

---

## Prompt 13: UI Decluttering & Minimalist Redesign (Recordings, Progress, Settings)
* **Date:** 2026-09-22 14:10:35 (Local Time)
* **Category:** UI/UX Design System & Information Architecture

### Prompt:
```text
recording, progress and setting pages look cluttered
```

### Outcome & Summary:
- Redesigned three information-dense views using progressive disclosure, tabbed sub-navigation, and the Zesty Lemon design system:
- **1. Recordings Page (`RecordingsPage.jsx` & `.css`)**:
  - Replaced bulky cards with minimalist card rows displaying exercise title, date, duration, CEFR badge, WPM, and accuracy tags.
  - Added sticky CEFR filter pills (`ALL`, `A1`–`C2`) and real-time search filter.
  - Implemented 2-column tabbed expansion panel:
    - Tab 1: Spoken Audio Player, transcript quote, and 4-metric cadence grid.
    - Tab 2: Grammar strengths & corrections diff, vocabulary upgrades, and weakness tags.
- **2. Progress & Analytics Page (`ProgressPage.jsx` & `.css`)**:
  - Organized analytics into 3 dedicated sub-navigation tabs:
    - 📊 **Fluency & Pace Trajectory**: 4 minimalist KPI scorecards + full-width SVG WPM Flow Trendline with 110–150 WPM target zone.
    - 🎯 **Weakness Breakdown**: Expansive pedagogical weakness distribution cards with targeted recommendations.
    - 📜 **Practice Turn History**: Clean, scannable table with timestamps, WPM, hesitation count, and modal feedback triggers.
  - Added compact time window filter pills (`7d`, `30d`, `90d`, `All Time`) and language selector.
- **3. Settings Page (`SettingsPage.jsx` & `.css`)**:
  - Organized settings into 3 dedicated sub-navigation tabs:
    - 🌐 **Language Tracks**: Grid of enrolled language cards, active primary star badge, hours spoken, sessions, and atomic primary switch button.
    - 👤 **Account Profile**: Focused user profile form with locked username guidance and save action.
    - 🎙️ **Voice & AI Audio**: Integrated `AudioPromptPlayer` speech speed tester, browser voice diagnostics, and mic permissions indicator.

---

## Prompt 14: Practice Page Skill Focus Filter Fix
* **Date:** 2026-09-22 17:35:12 (Local Time)
* **Category:** Bug Fix, API Filtering & Data Normalization

### Prompt:
```text
skill focus filter in the practice page is not working
```

### Outcome & Summary:
- Diagnosed root cause: Backend model stores `SkillFocus` choices (`fluency`, `grammar`, `vocabulary`, `pronunciation`, `mixed`), but `ExerciseListCreateView` was using case-sensitive exact matching (`skill_focus=val`) while the frontend was passing `'speaking'` or capitalized values that didn't match.
- **Backend Fix**:
  - Updated `backend/apps/exercises/views.py` to use case-insensitive filtering (`skill_focus__iexact`).
  - Added legacy mapping for `'speaking'` -> `'fluency'` and safely ignored `'ALL'`.
- **Frontend Fix**:
  - Updated `PracticePage.jsx` filter pills to use standard values: `{ label: 'All Skills', value: 'ALL' }`, `{ label: 'Fluency', value: 'fluency' }`, `{ label: 'Vocabulary', value: 'vocabulary' }`, `{ label: 'Grammar', value: 'grammar' }`, `{ label: 'Pronunciation', value: 'pronunciation' }`.
- **Automated Regression Verification**:
  - Added filter test cases to `backend/tests/test_exercises_and_recordings.py`.
  - Confirmed all **29/29 backend tests** pass cleanly.

---

## Prompt 15: Exercise Practice Modal Redesign & Aesthetic Overhaul
* **Date:** 2026-09-22 22:15:22 (Local Time)
* **Category:** UI/UX Redesign & Speaking Studio Aesthetics

### Prompt:
```text
also when we start an exercise , that ui looks ugly
```

### Outcome & Summary:
- Diagnosed visual degradation: Undefined CSS variables (`--spacing-`, `--color-lemon-`, `--radius-2xl`) in `design-tokens.css` caused padding to collapse and gradients to fail; nested card-inside-a-card borders created visual boxiness.
- **Design Tokens Token Aliases**:
  - Added complete backward-compatibility aliases in `frontend/src/styles/design-tokens.css` (`--spacing-xs` to `--spacing-2xl`, `--font-heading`, `--font-body`, `--color-text-primary`, `--color-lemon-primary`, `--color-olive-primary`, `--radius-2xl`).
- **Practice Session Modal (`PracticeSessionModal.jsx` & `.css`)**:
  - Transformed the modal into a focused **Speaking Studio** stage.
  - Added studio breadcrumb with session counter (`Step 1 of 2: Record Speech`) and keyboard `[ESC]` shortcut hint.
  - Implemented 3-stage visual progress tracker (`1. Practice & Record` -> `2. AI Evaluation` -> `3. Feedback & Scores`).
  - Redesigned Prompt Card with elegant quotation marks, high-contrast typography, embedded `AudioPromptPlayer` ("Listen to Prompt"), and modern target vocabulary chips with hover elevation.
  - Redesigned Analyzing state into a futuristic acoustic radar stage with concentric pulsing ripple rings, spinning sparkle badge, dynamic milestone progress cards, and glowing indeterminate progress bar.
- **Audio Recorder Dock (`AudioRecorderCard.css` & `AudioVisualizer.css`)**:
  - Refactored `.recorder-card` to integrate smoothly without redundant nested borders.
  - Added glowing yellow/olive aura when recording, crimson live indicator dot with pulse animation, and monospace digital timer.
  - Enhanced "Start Speaking" button with tactile lemon gradient, pill shape, and smooth hover elevation.
  - Enhanced `AudioVisualizer.css` with rounded pill frequency bars, glowing active gradient, and soft background.
  - Polished `AnalysisFeedbackCard.css` hero banner and CEFR scorecard.
- **Verification**:
  - Verified frontend production build with `npm.cmd run build` (0 errors, 1.06s).
  - Confirmed all **29/29 backend tests** passing.

---

## Prompt 16: Comprehensive Prompt Log Synchronization
* **Date:** 2026-09-22 22:28:08 (Local Time)
* **Category:** Documentation & Project Tracking

### Prompt:
```text
add all the major prompts to promtps.md
```

### Outcome & Summary:
- Synchronized `prompts.md` with complete, detailed records for Prompts 7 through 16, capturing all functional deliverables, architectural decisions, UI redesigns, and automated test verifications.



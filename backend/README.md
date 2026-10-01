# English Learning Agent - Backend

Backend service for the AI-Powered English-Speaking Coach application, built with Django 5, Django REST Framework, SimpleJWT, Celery, and PostgreSQL/SQLite.

## Architecture & Data Models

### 1. `apps.authentication`
- **`User`** (`AbstractUser`):
  - `email` (unique)
  - `cefr_level` (`A1`, `A2`, `B1`, `B2`, `C1`, `C2` — default `B1`)
  - `native_language` (e.g., Spanish, Urdu, Mandarin)
  - `target_goal` (e.g., IELTS Speaking, Job Interviews, Fluency)
- **Auth Flow**:
  - Access token (15 min) in response body.
  - Refresh token (7 days) in `HttpOnly`, `SameSite=Lax`, `Path=/api/auth/refresh/` cookie.
  - Automatic refresh token rotation and blacklisting.

### 2. `apps.exercises`
- **`Exercise`**:
  - `title`, `prompt_text`
  - `skill_focus`: `grammar`, `vocabulary`, `fluency`, `pronunciation`, `mixed`
  - `topic_tags`: JSON array of topic categories
  - `cefr_level`: `A1` to `C2`
  - `source`: `static` (curated) or `generated` (AI adaptive)
  - `vocabulary_hints`: JSON list of target domain vocabulary (used to bias Gemini 3.5 Transcribe)
  - `min_duration_seconds`, `max_duration_seconds`

### 3. `apps.recordings`
- **`Recording`**:
  - `user` (FK to User)
  - `exercise` (FK to Exercise, nullable)
  - `audio_file` (stored locally in `media/recordings/%Y/%m/%d/`, max 25MB)
  - `mime_type` (`audio/webm`, `audio/mp4`)
  - `duration_seconds`, `file_size_bytes`
  - `status`: `uploaded`, `processing`, `analyzed`, `failed`
  - `error_message`
- **`AnalysisResult`**:
  - `recording` (OneToOne to Recording)
  - `transcript_text`: Verbatim transcript from Gemini 3.5 Transcribe
  - `word_timestamps`: JSON array with word offsets (`start_offset`, `end_offset`)
  - `grammar_feedback`, `vocabulary_feedback`, `coherence_feedback`
  - `fluency_metrics`: JSON object (`wpm`, `pause_count`, `avg_pause_ms`, `filler_count`, `words_per_sentence`)
  - `cefr_estimate`: Estimated CEFR level for the speech
  - `pronunciation_notes`: Qualitative clarity observations (experimental)
  - `weakness_tags`: JSON array (`['filler_words_high', 'pause_heavy', 'low_wpm']`)

---

## API Surface

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register user, set refresh cookie, return access token | No |
| `POST` | `/api/auth/login/` | Login, set refresh cookie, return access token | No |
| `POST` | `/api/auth/refresh/` | Rotate tokens using httpOnly cookie, return fresh access token | Cookie |
| `POST` | `/api/auth/logout/` | Blacklist token and clear refresh cookie | No |
| `GET` | `/api/auth/me/` | Current user profile and CEFR level | Bearer |
| `GET` | `/api/exercises/` | List all exercises (filter by `cefr_level`, `skill_focus`) | Bearer |
| `GET` | `/api/exercises/next/` | Adaptive next exercise based on user CEFR & weakness history | Bearer |
| `GET` | `/api/exercises/<id>/` | Exercise prompt details | Bearer |
| `POST` | `/api/recordings/upload/` | Multipart audio upload, creates Recording, queues Celery | Bearer |
| `GET` | `/api/recordings/` | List user's past recordings and statuses | Bearer |
| `GET` | `/api/recordings/<id>/` | Recording status and full analysis feedback | Bearer |
| `GET` | `/api/recordings/progress/` | Dynamic time-series analytics (`?window=30d`) | Bearer |

---

## Running Locally

### 1. Activate Virtual Environment
```powershell
cd backend
.\.venv\Scripts\Activate.ps1
```

### 2. Apply Migrations & Seed Exercises
```powershell
python manage.py migrate
python manage.py seed_exercises
```

### 3. Run Automated Tests
```powershell
pytest
```

### 4. Start Development Server
```powershell
python manage.py runserver 8000
```

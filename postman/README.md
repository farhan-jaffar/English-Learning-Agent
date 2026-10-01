# Postman API Test Suite (`EnglishLearningAgent`)

Comprehensive pre-configured Postman test suite covering all API endpoints for the English Learning Agent platform.

---

## What's Included

* **Collection (`collections/EnglishLearningAgent.postman_collection.json`)**:
  * **20 Pre-configured API Requests** across 4 logical modules.
  * **Automated JavaScript Test Scripts** asserting status codes, payload schemas, and response invariants.
  * **Dynamic Token & ID Chaining**:
    * Automatically extracts and saves `accessToken` from registration/login to the active environment.
    * Automatically extracts `enrolledLanguageId`, `exerciseId`, and `recordingId` to chain subsequent requests.
* **Environment (`environments/EnglishLearningAgent.local.postman_environment.json`)**:
  * Configured for local development (`http://127.0.0.1:8000`).
* **Test Fixture (`sample_audio.webm`)**:
  * Sample audio file for testing the multipart `POST /api/recordings/upload/` endpoint.

---

## Folder & Request Structure

### 1. Authentication & Learner Profile
1. `POST /api/auth/register/` - Registers learner, enrolls initial languages, saves `accessToken`.
2. `POST /api/auth/login/` - Authenticates user and refreshes `accessToken`.
3. `GET /api/auth/me/` - Retrieves active profile with multi-language state.
4. `POST /api/auth/refresh/` - Rotates JWT access token via HTTP-only cookie.
5. `POST /api/auth/logout/` - Clears session and refresh cookie.

### 2. Multi-Language Management
1. `GET /api/auth/languages/` - Lists all enrolled target languages with stats.
2. `POST /api/auth/languages/` - Enrolls user into an additional target language (e.g. French).
3. `GET /api/auth/languages/{{enrolledLanguageId}}/` - Fetches single enrolled language details.
4. `PATCH /api/auth/languages/{{enrolledLanguageId}}/` - Updates CEFR level or learning goal.
5. `POST /api/auth/languages/{{enrolledLanguageId}}/set-primary/` - Atomically switches active primary language.
6. `DELETE /api/auth/languages/{{enrolledLanguageId}}/` - Unenrolls from a language.

### 3. Practice Exercises
1. `GET /api/exercises/` - Lists available exercises and captures sample `exerciseId`.
2. `GET /api/exercises/?language=en-US&cefr_level=B1&skill_focus=fluency` - Multi-filter exercises.
3. `POST /api/exercises/` - Creates custom speaking prompt.
4. `GET /api/exercises/{{exerciseId}}/` - Detailed prompt instructions.
5. `GET /api/exercises/next/?language=en-US` - Adaptive recommendation based on recent weaknesses.

### 4. Audio Recordings & Progress
1. `POST /api/recordings/upload/` - Uploads audio recording (`sample_audio.webm`), auto-binds to exercise language.
2. `GET /api/recordings/` - Lists user's practice recordings.
3. `GET /api/recordings/{{recordingId}}/` - Fetches status, turn transcript, and CEFR analysis.
4. `GET /api/recordings/progress/?language=en-US&days=30` - Aggregates longitudinal WPM, pauses, and frequent weaknesses.

---

## How to Run

### In VS Code / Antigravity IDE (Postman Extension)
1. Open the **Postman** tab in the sidebar.
2. The collection and environment in the `postman/` directory are automatically discovered via `.postman/resources.yaml`.
3. Select **`EnglishLearningAgent - Local`** as your active environment.
4. Run requests individually or run the entire collection via **Run Collection**.

### In Postman Desktop App
1. Open Postman &rarr; Click **Import**.
2. Select:
   * `postman/collections/EnglishLearningAgent.postman_collection.json`
   * `postman/environments/EnglishLearningAgent.local.postman_environment.json`
3. Set your active environment to **`EnglishLearningAgent - Local`**.
4. Click **Run collection** to run all 20 tests in automated sequence.

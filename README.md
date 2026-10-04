# ISL Live Translator

Live webcam translation of **Indian Sign Language (alphabet, digits, and a
set of common daily-conversation words)** into spoken English, built as a
full-stack TypeScript app with a Python ML microservice for computer vision
and model inference.

> **Read this before you start:** there is no reliable, ready-made "ISL to
> English" model available anywhere — public sign-language datasets are
> almost all American Sign Language (ASL). This project gives you a
> complete, working *pipeline* (webcam → hand tracking → sequence model →
> text → speech), but **the model only recognizes signs you've trained it
> on**. Out of the box, the model file doesn't exist yet — you record your
> own samples with the included tool, then train it on your laptop. This is
> genuinely how every real ISL recognition project works; nobody skips this
> step.

---

## 1. Architecture

```
Browser (React)
   │  webcam frames (JPEG, ~12 fps)
   ▼
Python ML service (FastAPI + MediaPipe + PyTorch)  ── WebSocket ──▶ live predictions
   │
   ▼ (session history only, not the live video path)
Express API (Node + TypeScript + Drizzle ORM)
   │
   ▼
PostgreSQL
```

- **apps/web** — React + TypeScript frontend. Captures webcam frames, opens
  a WebSocket directly to the ml-service for lowest latency, shows live
  captions, speaks results aloud via the browser's built-in Text-to-Speech
  (`speechSynthesis`), and saves session transcripts via the Express API.
- **apps/server** — Express + TypeScript + Drizzle ORM + PostgreSQL + Zod.
  Handles user accounts (JWT auth) and session history. It does **not**
  sit in the live video path — that would add a hop and hurt latency for
  no benefit, since it doesn't need to see raw video.
- **apps/ml-service** — Python FastAPI service. Runs MediaPipe hand
  tracking on each frame, buffers a sliding window of hand landmarks, and
  runs a BiLSTM sequence classifier to predict the sign being made. Also
  applies temporal smoothing so a single flickered misread doesn't get
  spoken aloud (see "How live translation avoids false triggers" below).
- **packages/shared** — Zod schemas and the sign-label list shared between
  the frontend and backend (single source of truth for the API contract).
- **ml/** — Everything for building your own dataset and training the
  model: `dataset_tool/collect.py` (record samples via webcam),
  `training/train.py` (train the model on your laptop, CPU-only).

---

## 2. What you need installed

| Tool | Version | Why |
|---|---|---|
| Node.js | ≥ 18.18 | frontend + backend |
| npm | ≥ 9 | workspaces |
| Python | 3.10 or 3.11 | ml-service + training (the collector uses MediaPipe's legacy `solutions` API) |
| PostgreSQL | 16 (or via Docker) | session/user storage |
| Docker (optional) | any recent | easiest way to run Postgres |
| A webcam | — | obviously |

Your laptop (HP with Intel Core Ultra 5 + Intel Arc iGPU) has **no CUDA
GPU**, so this project is deliberately designed to train and run entirely
on **CPU**. That's not a downgrade here — landmark-sequence models (126
numbers per frame) are tiny compared to raw-video models, so CPU training
is fast (a few minutes) and CPU inference is fast enough for real-time use.

---

## 3. First-time setup

### 3.1 Clone/copy the project, then install Node dependencies

From the project root (`isl-translator/`):

```bash
npm install
```

This installs all three TypeScript workspaces (`apps/web`, `apps/server`,
`packages/shared`) at once via npm workspaces.

Build the shared package once (server and web both import compiled types
from it):

```bash
npm run build:shared
```

### 3.2 Start PostgreSQL

Easiest option — Docker:

```bash
docker compose up -d
```

This starts Postgres on `localhost:5432` with:
- user: `isl_user`
- password: `isl_password`
- database: `isl_translator`

(No Docker? Install Postgres 16 locally and create a database/user matching
those values, or edit `apps/server/.env`'s `DATABASE_URL` to match whatever
you set up.)

### 3.3 Configure environment variables

```bash
cp apps/server/.env.example apps/server/.env
cp apps/web/.env.example apps/web/.env
```

Open `apps/server/.env` and set a real `JWT_SECRET` (any long random
string — e.g. run `openssl rand -hex 32` and paste the result). The other
defaults work as-is if you used the Docker Compose Postgres above.

### 3.4 Run database migrations

```bash
cd apps/server
npm run db:generate   # generates SQL from the Drizzle schema
npm run db:migrate    # applies it to Postgres
cd ../..
```

### 3.5 Set up the Python ML service

```bash
cd apps/ml-service
python -m venv .venv

# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
cd ../..
```

> **Note on Python and MediaPipe versions:** this project pins MediaPipe
> 0.10.21 because the collector uses its legacy `solutions` API. If
> `pip install -r requirements.txt` fails, it's almost always because you're
> on Python 3.12+. Install Python 3.10 or 3.11
> alongside your current version (e.g. via `pyenv` or the official
> installer) and create the venv with that version specifically:
> `py -3.11 -m venv .venv` (Windows) or `python3.11 -m venv .venv` (macOS/Linux).

---

## 4. Recording your training data (the part only you can do)

The model needs to see examples of *you* (or whoever will use it) signing
each letter, digit, and word. This is the dataset-collection step.

With the ml-service venv activated:

```bash
cd ml/dataset_tool
python collect.py --label A --samples 40
```

- A webcam window opens.
- Press **SPACE** to record one sample (it captures a short window of
  frames automatically — just hold/perform the sign).
- Repeat until you've recorded the requested number of samples.
- Press **Q** to quit early.

Do this for every label you care about. To see your overall progress:

```bash
python check_progress.py --min 40
```

This prints a table showing how many samples you have per label and which
ones still need more.

**Practical tips (these directly affect accuracy):**
- For **letters/digits** (static hand shapes): hold the shape steady;
  vary your hand's position slightly across samples (a bit left/right,
  closer/further) so the model generalizes rather than memorizing one
  exact spot.
- For **words** (dynamic signs — HELLO, THANK_YOU, WATER, etc.): perform
  the *entire* motion once per sample, varying your speed a little across
  repetitions.
- Keep consistent, reasonably bright lighting; avoid strong backlight.
- **Minimum ~30–40 samples per label** to get something usable; 60-100 for
  word signs (they have more motion variation to learn) will noticeably
  improve reliability.
- The full label list — 26 letters, 10 digits, and 30 common words like
  HELLO, THANK_YOU, PLEASE, YES, NO, HELP, WATER, WHERE, HOW_ARE_YOU, etc.
  — is defined once in `packages/shared/src/constants/signs.ts` and
  mirrored in `apps/ml-service/app/core/labels.py`. If you want to add or
  remove a sign, edit **both** files identically, then re-collect data and
  retrain.

This step realistically takes a few hours split across sessions — that's
normal, and it's the actual bottleneck in building any sign-language
recognizer, not the code.

---

## 5. Training the model

Once you have data for at least a handful of labels (you don't need all 66
before your first training run — start small, confirm the pipeline works,
then keep adding data):

```bash
cd ml/training
python train.py --epochs 60 --batch-size 16
```

This trains a BiLSTM sequence classifier entirely on CPU (a few minutes for
a dataset of a few thousand short samples) and saves the best checkpoint to
`ml/models_out/isl_model.pt`. Watch the printed `val_acc` — if it's very
low (near 1/number-of-labels), you likely need more/better samples for the
labels involved, not more epochs.

Re-run `collect.py` any time to add more samples for weak labels, then
re-run `train.py` — it always trains from all the data currently in
`ml/data/raw/`.

---

## 6. Running everything

Open **three terminals**.

**Terminal 1 — ML service:**
```bash
cd apps/ml-service
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 — Express API:**
```bash
cd apps/server
npm run dev
```

**Terminal 3 — React frontend:**
```bash
cd apps/web
npm run dev
```

Then open **http://localhost:5173**, register an account, and go to the
Live Translator page. Click **Start camera**, allow camera access, and
start signing — recognized signs appear as live captions and are spoken
aloud (toggle "Speak aloud" to mute).

Check `http://localhost:8000/health` any time to confirm the ml-service
sees your trained checkpoint (`modelLoaded: true`).

---

## 7. How live translation avoids false triggers

A raw frame-by-frame prediction would flicker and misfire constantly. To
make it usable, `apps/ml-service/app/core/inference.py` does:

1. **Sliding window** — buffers the last 24 frames (~0.8s) of landmarks
   per session, not a single frame.
2. **Confidence threshold** — a prediction below 75% confidence is treated
   as "no sign", not guessed at.
3. **Stability voting** — the *same* label must win across 5 consecutive
   windows before it's considered "stable" (i.e. worth speaking/logging).
   This costs a few hundred milliseconds of latency in exchange for far
   fewer wrong or repeated triggers.
4. **Cooldown** — after a stable sign fires, it won't fire again
   immediately, so holding the same hand shape doesn't spam the same word.

This is a real trade-off: it's tuned for reliability over instant
reaction. You can adjust `WINDOW_SIZE`, `CONFIDENCE_THRESHOLD`,
`STABILITY_FRAMES`, and `REPEAT_COOLDOWN_WINDOWS` at the top of that file
if you want a snappier or steadier feel.

---

## 8. Project structure

```
isl-translator/
├── apps/
│   ├── web/            React + TS — webcam UI, live captions, TTS, auth, history
│   ├── server/         Express + TS + Drizzle + Zod — auth, session history API
│   └── ml-service/      FastAPI + MediaPipe + PyTorch — landmarks, model, live WS
├── packages/
│   └── shared/         Zod schemas + sign-label list shared by web & server
├── ml/
│   ├── dataset_tool/   collect.py, check_progress.py — record your training data
│   ├── training/       train.py, dataset.py — trains the model on CPU
│   ├── data/raw/       your recorded .npy samples (not committed — yours only)
│   └── models_out/     trained checkpoint (isl_model.pt) ends up here
└── docker-compose.yml  local Postgres
```

---

## 9. Honest limitations

- This is **not** full grammatical ISL translation (ISL has its own
  grammar distinct from English word order) — it's isolated sign/letter/
  digit recognition, spoken as individual words in sequence. That's the
  same scope as essentially every academic ISL/ASL recognition system.
- Accuracy is entirely a function of how much (and how varied) training
  data you record. A handful of samples per label will misfire often;
  60-100 well-varied samples per label will be noticeably better.
- Two-handed and motion-heavy signs are harder than static single-hand
  letters — expect to need more samples and possibly more epochs for those.
- Lighting, camera angle, and background all affect MediaPipe's hand
  detection quality, which is upstream of everything else.

## 10. Extending it later

- Add new signs: extend the label list (both TS and Python copies), record
  data, retrain.
- Swap `speechSynthesis` for a nicer TTS voice/provider if you want more
  natural speech.
- Add pose landmarks (already wired as optional in the shared schema) for
  signs that rely on body/shoulder position.
- Add a "reverse" mode (voice → sign, e.g. showing an avatar or sign
  images) as a separate, later project — this repo focuses on sign → voice
  as you asked for.

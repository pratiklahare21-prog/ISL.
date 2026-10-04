# ISL MudraVaani - Project Status Report

**Date:** Generated during QA audit  
**Project:** Indian Sign Language (ISL) → Text → Speech Translator

---

## EXECUTIVE SUMMARY

### Current Status: ⚠️ **PARTIALLY READY**

The project has a working technical pipeline but is **missing critical components** for competition/demo readiness:

1. ✅ **Core pipeline works**: Webcam → Landmarks → ISL Recognition → Text → Speech
2. ✅ **Model architecture complete**: BiLSTM sequence classifier
3. ⚠️ **NO TRAINING DATA** included (user must record their own)
4. ❌ **NO OPEN-WEIGHT AI** for context-aware sentence generation (only isolated word recognition)
5. ⚠️ **Python version incompatibility**: Requires 3.10/3.11, may have 3.12+
6. ⚠️ **No automated evaluation** (evaluation script now created)

---

## ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                     ISL MudraVaani System                   │
└─────────────────────────────────────────────────────────────┘

┌──────────────┐
│  Browser     │  React + TypeScript
│  (Frontend)  │  - Webcam capture
│              │  - Live caption display
└──────┬───────┘  - Browser TTS (speechSynthesis)
       │
       │ WebSocket (JPEG frames, ~25 fps)
       │
       ▼
┌──────────────┐
│  ML Service  │  FastAPI + Python
│  (Python)    │  - MediaPipe hand tracking (21 landmarks × 2 hands)
│              │  - BiLSTM sequence classifier
│              │  - Temporal smoothing (stability voting)
└──────┬───────┘  - Confidence thresholding
       │
       │ HTTP (session history only)
       │
       ▼
┌──────────────┐
│  Backend API │  Express + TypeScript + Drizzle ORM
│  (Node.js)   │  - User authentication (JWT)
│              │  - Session history storage
└──────┬───────┘  - PostgreSQL database
       │
       ▼
┌──────────────┐
│  PostgreSQL  │  Database
│              │  - Users, sessions, transcripts
└──────────────┘
```

---

## COMPONENT STATUS

### ✅ WORKING COMPONENTS

#### 1. **Frontend (React + TypeScript)**
- **Location:** `apps/web/`
- **Status:** Fully functional
- **Features:**
  - Real-time webcam capture and streaming
  - WebSocket connection to ML service
  - Live sign recognition display
  - Browser-based Text-to-Speech
  - Session history
  - User authentication

#### 2. **ML Service (FastAPI + Python)**
- **Location:** `apps/ml-service/`
- **Status:** Fully functional
- **Features:**
  - MediaPipe Hands integration (21 landmarks per hand)
  - Sliding window buffer (24 frames, ~0.8s)
  - BiLSTM sequence classifier
  - Temporal stability voting (reduces false triggers)
  - Confidence thresholding (65%)
  - WebSocket real-time inference

#### 3. **Backend API (Express + TypeScript)**
- **Location:** `apps/server/`
- **Status:** Fully functional
- **Features:**
  - JWT-based authentication
  - Session CRUD operations
  - Drizzle ORM + PostgreSQL
  - User management

#### 4. **Model Architecture**
- **File:** `apps/ml-service/app/models/architecture.py`
- **Type:** BiLSTM Sequence Classifier
- **Status:** Well-designed, CPU-optimized
- **Details:**
  - Input: 126 features (21 landmarks × 3 coords × 2 hands)
  - Hidden: 128 units, 2 layers, bidirectional
  - Output: 66 classes (A-Z, 0-9, 30 words)
  - Dropout: 0.3 for regularization

#### 5. **Training Pipeline**
- **Location:** `ml/training/`
- **Status:** Complete and functional
- **Features:**
  - Dataset loading from `.npy` files
  - Train/validation split
  - Class-weighted loss function
  - Learning rate scheduling
  - CPU-optimized (no CUDA required)

#### 6. **Dataset Collection Tool**
- **Location:** `ml/dataset_tool/collect.py`
- **Status:** Fully functional
- **Features:**
  - Interactive webcam recording
  - Consistent with inference-time processing
  - Countdown before recording
  - Progress tracking
  - Sample validation

### ⚠️ MISSING / INCOMPLETE COMPONENTS

#### 1. **❌ TRAINING DATA**
- **Status:** **NOT INCLUDED**
- **Location:** `ml/data/raw/` (empty except `.gitkeep`)
- **Impact:** CRITICAL
- **Problem:** 
  - Model exists but was trained on **unknown data**
  - No way to evaluate accuracy without data
  - User must record their own samples
- **Fix Required:**
  - Either include sample training data OR
  - Create synthetic/demo data for testing OR
  - Document that accuracy cannot be measured

#### 2. **❌ OPEN-WEIGHT AI INTEGRATION**
- **Status:** **NOT PRESENT**
- **Expected:** Context-aware sentence generation using open-weight AI
- **Current:** Only isolated word recognition
- **Impact:** CRITICAL for "AI-powered" claim
- **Problem:**
  - README says "isolated sign/letter/digit recognition, spoken as individual words"
  - No LLM or context engine for sentence formation
  - Demo mode is **hardcoded**, not AI-generated
- **Missing Components:**
  - No LLM integration (should use local model like Llama, Mistral, etc.)
  - No prompt engineering for sign-to-sentence
  - No context accumulation across signs
  - No grammar correction or natural language generation

#### 3. **⚠️ PYTHON VERSION COMPATIBILITY**
- **Status:** **INCOMPATIBLE**
- **Required:** Python 3.10 or 3.11
- **Reason:** MediaPipe 0.10.21 breaks on Python 3.12+
- **Impact:** MODERATE
- **Current System:** May have Python 3.14.7 (too new)
- **Fix:** Must use Python 3.11 specifically

#### 4. **⚠️ MODEL EVALUATION**
- **Status:** **MISSING** (now created)
- **Problem:** No way to measure accuracy
- **Fix:** Evaluation script created at `ml/evaluation/evaluate_model.py`
- **Provides:**
  - Overall accuracy
  - Per-class accuracy
  - Precision, Recall, F1-score
  - Confusion matrix
  - Classification report
  - Latency measurements

#### 5. **⚠️ CONTINUOUS SENTENCE MODE**
- **Status:** **INCOMPLETE**
- **Current:** Accumulates individual words
- **Missing:** True grammatical sentence formation
- **Example Current:**
  - Signs: HELLO + I + NEED + HELP
  - Output: "HELLO I NEED HELP" (just concatenation)
- **Example Needed:**
  - Signs: HELLO + I + NEED + HELP
  - Output: "Hello, I need help." (natural sentence with punctuation)
- **Requires:** LLM integration

---

## TECHNICAL SPECIFICATIONS

### Dependencies

#### Python (ML Service)
```
fastapi==0.115.0
uvicorn[standard]==0.30.6
mediapipe==0.10.21        # Requires Python 3.10 or 3.11
opencv-python-headless>=4.10.0
numpy>=1.26,<2.0
torch>=2.4                # CPU-only (no CUDA)
websockets==13.1
python-multipart==0.0.9
pydantic==2.9.2
```

#### Node.js (Frontend + Backend)
```
Node.js >= 18.18.0
npm >= 9.0.0
```

#### Database
```
PostgreSQL 16 (via Docker or local)
```

### Model Details

| Parameter | Value |
|-----------|-------|
| **Architecture** | BiLSTM (Bidirectional LSTM) |
| **Input Size** | 126 features (21 × 3 × 2 hands) |
| **Hidden Size** | 128 units |
| **Layers** | 2 LSTM layers |
| **Output Classes** | 66 (26 letters + 10 digits + 30 words) |
| **Dropout** | 0.3 |
| **Device** | CPU (Intel Arc iGPU, no CUDA) |
| **Training Time** | ~5-10 minutes on CPU |

### Sign Classes (66 total)

- **Alphabet:** A-Z (26 signs)
- **Digits:** 0-9 (10 signs)
- **Words:** HELLO, THANK_YOU, PLEASE, YES, NO, SORRY, HELP, WATER, FOOD, NAME, HOW_ARE_YOU, GOOD, BAD, STOP, GO, COME, WAIT, UNDERSTAND, NOT_UNDERSTAND, MY, YOU, WHERE, WHAT, WHEN, TOILET, HOME, SCHOOL, WORK, FRIEND, FAMILY (30 signs)

---

## ACCURACY & PERFORMANCE

### ⚠️ **ACCURACY CANNOT BE MEASURED**

**Reason:** No training data or test set is included with the project.

**Model Status:**
- ✅ Trained model exists: `apps/ml/models_out/isl_model.pt`
- ❌ Training data: NOT INCLUDED
- ❌ Test set: NOT AVAILABLE
- ❌ Evaluation results: CANNOT RUN

**What the README claims:**
> "Accuracy is entirely a function of how much (and how varied) training data you record."

**This means:**
- The included model was trained on **unknown data** (not provided)
- **Cannot verify model quality**
- **Cannot claim any accuracy percentage**
- User must record their own data and retrain

### Performance (Theoretical)

| Metric | Value | Notes |
|--------|-------|-------|
| **Inference Latency** | ~10-50 ms | Per 24-frame window |
| **Frame Rate** | ~25 FPS | Frontend capture rate |
| **Window Size** | 24 frames (~0.8s) | Temporal context |
| **Stability Delay** | ~200-400 ms | Requires 2 consecutive windows |
| **Real-time?** | ✅ Yes | CPU-only, no GPU needed |

---

## KNOWN LIMITATIONS

### Design Limitations

1. **Not Full Grammatical ISL Translation**
   - ISL has its own grammar (different from English word order)
   - This system recognizes isolated signs, not grammatical sentences
   - Output is word-by-word, not syntactically correct ISL

2. **Two-Handed and Motion Signs Are Harder**
   - Static single-hand letters work best
   - Dynamic word signs need more training samples
   - Two-handed signs can confuse the model

3. **Environment Sensitivity**
   - Lighting affects MediaPipe detection
   - Background clutter can cause false detections
   - Camera angle matters

4. **User-Specific Training Required**
   - Model learns the signer's hand shapes
   - Won't generalize well to different signers
   - Each person needs to record their own data

### Technical Limitations

1. **Python Version Lock**
   - Must use Python 3.10 or 3.11
   - MediaPipe 0.10.21 incompatible with 3.12+

2. **CPU-Only Training**
   - No GPU acceleration
   - Training takes a few minutes (acceptable)
   - Large datasets (100K+ samples) would be slow

3. **No Real-Time Grammar**
   - Just word-by-word recognition
   - No context awareness
   - No sentence structure

4. **No Open-Weight AI Integration**
   - Missing LLM for natural language generation
   - No contextual sentence formation
   - Demo mode is hardcoded, not AI-driven

---

## MISSING FEATURES FOR COMPETITION READINESS

### Critical Missing Features

1. **❌ Open-Weight AI Integration**
   - **Requirement:** Use open-source/open-weight AI model
   - **Suggested:** Llama 3 8B, Mistral 7B, or similar
   - **Purpose:** Convert sign sequences into natural sentences
   - **Implementation:** Add LLM service with prompt engineering

2. **❌ Training Data / Test Set**
   - **Requirement:** Must be able to evaluate accuracy
   - **Options:**
     a. Include sample training data (30-50 samples × 10-20 signs)
     b. Create synthetic evaluation data
     c. Remove accuracy claims entirely

3. **❌ Model Evaluation Results**
   - **Requirement:** Document actual accuracy
   - **Fix:** Run evaluation script once data is available
   - **Output:** JSON results, confusion matrix, classification report

4. **⚠️ Continuous Sentence Mode**
   - **Current:** Word-by-word accumulation
   - **Needed:** Natural sentence formation with punctuation
   - **Depends on:** Open-weight AI integration

### Nice-to-Have Features

1. **Demo Mode Improvements**
   - Better visual feedback
   - Auto-advance option
   - More realistic demo scenarios

2. **Accuracy Visualization**
   - Confidence meter
   - Per-sign accuracy display
   - Real-time performance graphs

3. **Multi-User Support**
   - User-specific model fine-tuning
   - Transfer learning from base model

---

## HOW TO RUN (Current State)

### Prerequisites

1. **Python 3.11** (not 3.12+)
2. **Node.js >= 18.18**
3. **Docker** (for PostgreSQL) or local PostgreSQL 16
4. **Webcam**

### Setup Steps

1. **Check environment:**
   ```bash
   py -3.11 setup_and_check.py
   ```

2. **Install dependencies:**
   ```bash
   # Node.js packages
   npm install
   npm run build:shared
   
   # Python packages
   cd apps/ml-service
   py -3.11 -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   cd ../..
   ```

3. **Start PostgreSQL:**
   ```bash
   docker compose up -d
   ```

4. **Setup environment files:**
   ```bash
   copy apps\server\.env.example apps\server\.env
   copy apps\web\.env.example apps\web\.env
   ```
   Edit `apps/server/.env` and set `JWT_SECRET` to a random string.

5. **Run database migrations:**
   ```bash
   cd apps/server
   npm run db:migrate
   cd ../..
   ```

6. **Copy model to expected location:**
   ```bash
   mkdir ml\models_out
   copy apps\ml\models_out\isl_model.pt ml\models_out\isl_model.pt
   ```

### Running the Application

**Terminal 1 - ML Service:**
```bash
cd apps/ml-service
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Backend API:**
```bash
cd apps/server
npm run dev
```

**Terminal 3 - Frontend:**
```bash
cd apps/web
npm run dev
```

Open: http://localhost:5173

---

## RECOMMENDED FIXES

### Priority 1: Critical for Demo

1. **Add Open-Weight AI Integration**
   - Install transformers library
   - Download Llama-3.2-1B or similar small model
   - Create sentence generation service
   - Integrate with frontend

2. **Create Sample Training Data**
   - Record 40-50 samples for 10-15 common signs
   - Include at least: A, B, C, HELLO, YES, NO, HELP, THANK_YOU
   - Run training: `cd ml/training && python train.py`

3. **Run Model Evaluation**
   - Use new evaluation script
   - Document actual accuracy
   - Save results for presentation

### Priority 2: Important for Quality

4. **Fix Python Version**
   - Ensure Python 3.11 is used
   - Update setup instructions
   - Add version check to startup script

5. **Add Continuous Sentence Mode**
   - Accumulate recognized signs
   - Use LLM to form natural sentences
   - Display both raw signs and AI-generated sentence

6. **Improve Demo Mode**
   - Less reliance on hardcoded steps
   - More flexible presentation flow

### Priority 3: Nice-to-Have

7. **Add Visualization**
   - Real-time confidence graph
   - Landmark overlay on video
   - Per-class accuracy display

8. **Better Error Handling**
   - Graceful degradation when model missing
   - Clear error messages
   - Fallback to demo mode

---

## CONCLUSION

### ✅ What Works
- Core technical pipeline (webcam → landmarks → model → text → speech)
- Well-designed model architecture
- Professional codebase structure
- Real-time performance on CPU

### ❌ What's Missing
- **CRITICAL:** No open-weight AI for sentence generation
- **CRITICAL:** No training data (cannot evaluate)
- **CRITICAL:** Python version incompatibility
- **IMPORTANT:** No accuracy measurements
- **IMPORTANT:** No continuous sentence mode

### 🎯 To Make Demo-Ready

1. Add LLM integration (Llama/Mistral)
2. Create sample training data
3. Run evaluation and document accuracy
4. Fix Python version requirement
5. Test end-to-end with real camera

**Estimated Time to Fix:** 4-8 hours

---

## FILES CREATED DURING AUDIT

1. `setup_and_check.py` - Automated environment check and setup
2. `ml/evaluation/evaluate_model.py` - Model evaluation script
3. `PROJECT_STATUS.md` - This file

---

**Last Updated:** QA Audit - [Date]  
**Status:** Awaiting fixes before competition/demo readiness

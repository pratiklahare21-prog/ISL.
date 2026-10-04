# Manual Run Instructions - ISL MudraVaani

**Due to PowerShell rendering issues, follow these manual steps.**

---

## ⚠️ CRITICAL: Python Version Issue

**Your system has Python 3.14.7**  
**This project requires Python 3.10 or 3.11**

MediaPipe 0.10.21 does NOT work with Python 3.12+

### Fix Python Version First:

1. Download Python 3.11 from: https://www.python.org/downloads/
2. During install, check "Add Python 3.11 to PATH"
3. Verify: Open new CMD and type `py -3.11 --version`

**DO NOT PROCEED without Python 3.11 installed**

---

## Step-by-Step Setup

### 1. Fix PowerShell Execution Policy

Open **PowerShell as Administrator** and run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Type `Y` and press Enter.

---

### 2. Install Node.js Dependencies

Open **CMD** (not PowerShell) in project root:

```cmd
cd c:\ISL_MudraVaani--main
npm install
npm run build:shared
```

Wait for completion (2-5 minutes).

---

### 3. Create Python Virtual Environment

```cmd
cd c:\ISL_MudraVaani--main\apps\ml-service
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

If you get an error, you don't have Python 3.11. See step 0 above.

---

### 4. Generate Synthetic Training Data

```cmd
cd c:\ISL_MudraVaani--main\ml\dataset_tool
..\..\apps\ml-service\.venv\Scripts\python.exe download_isl_dataset.py --dataset synthetic --samples 40
```

This creates test data for 12 signs. Takes ~1 minute.

---

### 5. Copy or Train Model

**Option A: Use existing model (if present)**

```cmd
cd c:\ISL_MudraVaani--main
mkdir ml\models_out
copy apps\ml\models_out\isl_model.pt ml\models_out\isl_model.pt
```

**Option B: Train new model on synthetic data**

```cmd
cd c:\ISL_MudraVaani--main\ml\training
..\..\apps\ml-service\.venv\Scripts\python.exe train.py --epochs 40 --batch-size 16
```

Takes 3-5 minutes on CPU.

---

### 6. Run Model Evaluation (Optional)

```cmd
cd c:\ISL_MudraVaani--main\ml\evaluation
..\..\apps\ml-service\.venv\Scripts\python.exe evaluate_model.py
```

Results saved to: `ml/evaluation/evaluation_results/`

---

### 7. Setup Environment Files

```cmd
cd c:\ISL_MudraVaani--main
copy apps\server\.env.example apps\server\.env
copy apps\web\.env.example apps\web\.env
```

**IMPORTANT:** Edit `apps\server\.env` in a text editor and set:
```
JWT_SECRET=your_random_secret_here_use_any_long_string
```

---

### 8. Start PostgreSQL

**Option A: Using Docker**

```cmd
cd c:\ISL_MudraVaani--main
docker compose up -d
```

Wait 10 seconds for PostgreSQL to start.

**Option B: Local PostgreSQL**

Install PostgreSQL 16 and create:
- User: `isl_user`
- Password: `isl_password`
- Database: `isl_translator`

Or update `apps\server\.env` with your connection string.

---

### 9. Run Database Migrations

```cmd
cd c:\ISL_MudraVaani--main\apps\server
npm run db:migrate
```

---

## ▶️ START THE APPLICATION

### Open 3 Separate CMD Windows

**Window 1 - ML Service:**

```cmd
cd c:\ISL_MudraVaani--main\apps\ml-service
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**Test it:** Open browser to http://localhost:8000/health

---

**Window 2 - Backend API:**

```cmd
cd c:\ISL_MudraVaani--main\apps\server
npm run dev
```

**You should see:**
```
Server running on port 3000
```

---

**Window 3 - Frontend:**

```cmd
cd c:\ISL_MudraVaani--main\apps\web
npm run dev
```

**You should see:**
```
VITE v... ready in ...ms
Local: http://localhost:5173/
```

---

### Open Browser

Navigate to: **http://localhost:5173**

You should see the ISL Live Translator interface.

---

## 🎬 HOW TO USE

1. **Register** a new account
2. **Login** with your credentials
3. Click **"Start camera"**
4. Allow camera access when prompted
5. **Sign** in front of the camera
6. Watch recognized signs appear
7. Toggle **"Speak aloud"** to hear the words

---

## ⚠️ IMPORTANT NOTES

### About Synthetic Data

The current setup uses **synthetic test data**. This means:

- ✅ The pipeline works end-to-end
- ✅ You can test the interface
- ❌ Accuracy will be **VERY LOW** (20-40%)
- ❌ Signs may not be recognized correctly

**Why?** Synthetic data is random numbers, not real hand landmarks.

### To Get Real Accuracy

**Option 1: Record Your Own Data** (Recommended)

```cmd
cd c:\ISL_MudraVaani--main\ml\dataset_tool
py -3.11 collect.py --label A --samples 40
py -3.11 collect.py --label B --samples 40
py -3.11 collect.py --label HELLO --samples 40
# ... repeat for signs you want
```

Then retrain:
```cmd
cd ..\training
py -3.11 train.py --epochs 60
```

**Option 2: Use ISLTranslate Dataset**

See `ISL_DATASET_INTEGRATION.md` for instructions.

---

## ❌ STILL MISSING: OPEN-WEIGHT AI

**Critical Gap:** No LLM for sentence generation

**Current behavior:**
- Signs: HELLO, I, NEED, HELP
- Output: "HELLO I NEED HELP" ← just concatenation

**Needed behavior:**
- Signs: HELLO, I, NEED, HELP
- Output: "Hello, I need help." ← natural sentence

**How to add:** See `START_HERE.md` section "HOW TO ADD OPEN-WEIGHT AI"

Takes 3-4 hours to implement.

---

## 🐛 TROUBLESHOOTING

### "Python 3.14.7 detected"
→ Install Python 3.11, MediaPipe won't work with 3.14

### "npm: cannot be loaded because running scripts is disabled"
→ Fix execution policy (see step 1)

### "Model not found"
→ Copy from `apps\ml\models_out\` or train with synthetic data

### "Connection refused on port 8000"
→ ML service not running, check Window 1

### "Database connection failed"
→ PostgreSQL not running, use `docker compose up -d`

### Camera not working
→ Check browser permissions, allow camera access

### Signs not recognized
→ Expected with synthetic data, record real samples

### "No hands detected"
→ Show both hands clearly to camera, good lighting

---

## 📊 CURRENT PROJECT STATUS

### ✅ Working Components

- Real-time webcam capture (25 FPS)
- MediaPipe hand tracking (21 landmarks × 2 hands)
- BiLSTM sequence classifier
- Temporal smoothing and confidence filtering
- WebSocket real-time communication
- Browser text-to-speech
- User authentication (JWT)
- Session history (PostgreSQL)
- Training pipeline
- Evaluation system

### ❌ Missing Components

- **Open-weight AI integration** ← MOST CRITICAL
- Real ISL training data (only synthetic available)
- Natural sentence generation
- Context-aware conversation

### ⚠️ Limitations

- **Python 3.10/3.11 ONLY** (not 3.12+)
- Synthetic data = LOW accuracy
- User-specific training needed
- 66 sign vocabulary
- Environment sensitive (lighting, background)

---

## 📁 WHERE TO GET HELP

- **Quick start:** `START_HERE.md`
- **Full audit:** `FINAL_QA_REPORT.md`
- **Dataset info:** `ISL_DATASET_INTEGRATION.md`
- **Technical details:** `PROJECT_STATUS.md`
- **This guide:** `MANUAL_RUN_INSTRUCTIONS.md`

All files in: `c:\ISL_MudraVaani--main\`

---

## ✅ CHECKLIST

Before starting:

- [ ] Python 3.11 installed (`py -3.11 --version`)
- [ ] Execution policy fixed (PowerShell as Admin)
- [ ] npm packages installed (`npm install`)
- [ ] Python venv created
- [ ] Python packages installed (`pip install -r requirements.txt`)
- [ ] Synthetic data generated OR existing model copied
- [ ] Environment files created (`.env`)
- [ ] JWT_SECRET set in `apps\server\.env`
- [ ] PostgreSQL running (`docker compose up -d`)
- [ ] Database migrated (`npm run db:migrate`)

To run:

- [ ] ML Service running (port 8000)
- [ ] Backend API running (port 3000)
- [ ] Frontend running (port 5173)
- [ ] Browser open to http://localhost:5173
- [ ] Account registered and logged in
- [ ] Camera started and working

---

## 🎯 SUCCESS CRITERIA

**Minimum (Can Demo):**
- ✅ All 3 services running
- ✅ Camera capturing video
- ✅ Hand landmarks detected
- ✅ Signs recognized (even if incorrectly due to synthetic data)
- ✅ Text-to-speech working

**Ideal (Production Quality):**
- ✅ All of above, plus:
- ✅ Real ISL training data used
- ✅ Accuracy >80%
- ✅ Open-weight AI integrated
- ✅ Natural sentences generated
- ✅ Smooth, stable recognition

---

## 🚀 NEXT STEPS AFTER RUNNING

1. **Test the pipeline** with synthetic data
2. **Verify** all components work
3. **Add open-weight AI** (Llama-3.2-1B) - 3-4 hours
4. **Record real training data** - 2-3 hours
5. **Retrain model** with real data
6. **Re-evaluate** and document accuracy
7. **Ready for demo/competition**

---

**If you see all 3 services running and can access the web interface, you're successfully running the project!**

**The low accuracy is expected with synthetic data. This proves the pipeline works.**

**To make it production-ready, add open-weight AI and use real training data.**

---


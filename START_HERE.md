# 🚀 ISL MudraVaani - Quick Start Guide

**Status:** ⚠️ **NOT READY** - Requires fixes before running

---

## ⚡ CRITICAL ISSUES FOUND

1. ❌ **Python Version Incompatible**
   - **Detected:** Python 3.14.7
   - **Required:** Python 3.10 or 3.11
   - **Reason:** MediaPipe 0.10.21 doesn't work with Python 3.12+

2. ❌ **No Open-Weight AI Integration**
   - Project lacks LLM for sentence generation
   - Only does word-by-word recognition
   - **Missing:** Llama/Mistral integration

3. ❌ **No Training Data**
   - Cannot measure accuracy
   - Model exists but unknown quality
   - User must record own data

4. ⚠️ **PowerShell Execution Policy Restricted**
   - npm commands blocked
   - Cannot run setup scripts easily
   - **Fix:** See step 2 below

---

## 🔧 HOW TO FIX (Step-by-Step)

### Step 1: Install Python 3.11

1. Go to https://www.python.org/downloads/
2. Download **Python 3.11.x** (NOT 3.12 or newer)
3. Run installer
4. ✅ Check "Add Python 3.11 to PATH"
5. Verify: Open new CMD and type `py -3.11 --version`

### Step 2: Fix PowerShell Execution Policy

Open PowerShell **as Administrator** and run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Type "Y" to confirm.

### Step 3: Install Node.js Dependencies

```bash
cd c:\ISL_MudraVaani--main
npm install
npm run build:shared
```

### Step 4: Setup Python Environment

```bash
cd apps\ml-service
py -3.11 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd ..\..
```

### Step 5: Setup Environment Files

```bash
copy apps\server\.env.example apps\server\.env
copy apps\web\.env.example apps\web\.env
```

**IMPORTANT:** Edit `apps\server\.env` and set a random JWT_SECRET:
- Open `apps\server\.env` in a text editor
- Find `JWT_SECRET=`
- Set it to any long random string (e.g., copy from a password generator)

### Step 6: Start PostgreSQL

```bash
docker compose up -d
```

If Docker is not available, install PostgreSQL 16 locally and update `apps\server\.env` connection string.

### Step 7: Run Database Migrations

```bash
cd apps\server
npm run db:migrate
cd ..\..
```

### Step 8: Copy Model to Correct Location

```bash
mkdir ml\models_out
copy apps\ml\models_out\isl_model.pt ml\models_out\isl_model.pt
```

---

## ▶️ HOW TO RUN

Open **3 separate terminals** (CMD or PowerShell):

### Terminal 1: ML Service

```bash
cd c:\ISL_MudraVaani--main\apps\ml-service
.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

**Health Check:** http://localhost:8000/health

### Terminal 2: Backend API

```bash
cd c:\ISL_MudraVaani--main\apps\server
npm run dev
```

### Terminal 3: Frontend

```bash
cd c:\ISL_MudraVaani--main\apps\web
npm run dev
```

**Open Browser:** http://localhost:5173

---

## 📊 WHAT WORKS / WHAT DOESN'T

### ✅ WORKS (After Setup)

- Real-time webcam capture
- Hand landmark detection (MediaPipe)
- Sign recognition (A-Z, 0-9, 30 words)
- Live transcript display
- Browser text-to-speech
- Session history storage

### ❌ DOESN'T WORK (Missing)

- **Open-weight AI sentence generation** ← CRITICAL
- Natural language processing
- Context-aware conversation
- Measured accuracy (no training data)

### Current vs. Needed Output

| Input Signs | Current Output | Needed Output |
|------------|----------------|---------------|
| MY NAME P R A T I K | "MY NAME P R A T I K" | "My name is Pratik." |
| I NEED HELP | "I NEED HELP" | "I need help." |

---

## 🤖 HOW TO ADD OPEN-WEIGHT AI (CRITICAL)

This is the **most important missing feature**.

### Option 1: Use Llama 3.2 (Recommended)

1. Install transformers:
   ```bash
   cd apps\ml-service
   .venv\Scripts\activate
   pip install transformers torch accelerate
   ```

2. Create `apps\ml-service\app\core\sentence_generator.py`:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class SentenceGenerator:
    def __init__(self):
        # Use Llama-3.2-1B for laptop performance
        self.model = AutoModelForCausalLM.from_pretrained(
            "meta-llama/Llama-3.2-1B-Instruct",
            device_map="cpu",
            torch_dtype=torch.float32
        )
        self.tokenizer = AutoTokenizer.from_pretrained(
            "meta-llama/Llama-3.2-1B-Instruct"
        )
    
    def generate_sentence(self, signs: list[str]) -> str:
        """Convert ISL signs to natural English"""
        prompt = f"""Convert these Indian Sign Language signs into a natural English sentence with proper grammar and punctuation:

Signs: {' '.join(signs)}

Natural sentence:"""
        
        inputs = self.tokenizer(prompt, return_tensors="pt")
        outputs = self.model.generate(
            **inputs,
            max_new_tokens=50,
            temperature=0.7,
            do_sample=True
        )
        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the generated sentence
        sentence = result.split("Natural sentence:")[-1].strip()
        return sentence
```

3. Update `apps\ml-service\app\routes\ws_translate.py` to use it

### Option 2: Use Phi-3 Mini (Faster)

Replace model name with `"microsoft/Phi-3-mini-4k-instruct"` - smaller and faster.

**Time Estimate:** 3-4 hours including testing

---

## 📈 HOW TO GET ACCURACY METRICS

1. **Record Training Data** (2-3 hours):
   ```bash
   cd ml\dataset_tool
   py -3.11 collect.py --label A --samples 40
   py -3.11 collect.py --label B --samples 40
   # ... repeat for key signs
   ```

2. **Train Model**:
   ```bash
   cd ml\training
   py -3.11 train.py --epochs 60
   ```

3. **Evaluate**:
   ```bash
   cd ml\evaluation
   py -3.11 evaluate_model.py
   ```

4. **View Results**:
   - `ml/evaluation/evaluation_results/evaluation_results.json`
   - `ml/evaluation/evaluation_results/classification_report.txt`

---

## 📁 IMPORTANT FILES CREATED

1. **FINAL_QA_REPORT.md** - Complete technical audit report
2. **PROJECT_STATUS.md** - Detailed status and architecture
3. **setup_and_check.py** - Python setup automation script
4. **ml/evaluation/evaluate_model.py** - Accuracy evaluation
5. **run_setup.bat** - Windows batch setup script
6. **START_HERE.md** - This file

---

## ⏱️ TIME ESTIMATES

| Task | Time | Priority |
|------|------|----------|
| Fix Python version | 30 min | ⚠️ CRITICAL |
| Install dependencies | 15 min | ⚠️ CRITICAL |
| Add open-weight AI | 3-4 hrs | ⚠️ CRITICAL |
| Record training data | 2-3 hrs | ⚠️ CRITICAL |
| Run evaluation | 15 min | ⚠️ CRITICAL |
| **TOTAL TO DEMO-READY** | **6-8 hrs** | |

---

## 🎯 DEMO CHECKLIST

Before presenting:

- [ ] Python 3.11 installed
- [ ] All dependencies installed
- [ ] Open-weight AI integrated (Llama/Phi-3)
- [ ] Training data collected (min 10-15 signs)
- [ ] Model trained and evaluated
- [ ] Accuracy metrics documented
- [ ] End-to-end test completed
- [ ] Camera working
- [ ] Speech output working
- [ ] AI sentence generation working

---

## 🚨 KNOWN ISSUES

1. **Python 3.14.7 Too New**
   - MediaPipe requires 3.10 or 3.11
   - MUST downgrade

2. **No Open-Weight AI**
   - Only word-by-word recognition
   - Not competition-ready without LLM

3. **No Training Data**
   - Cannot verify accuracy
   - Must record own samples

4. **PowerShell Restricted**
   - npm commands blocked
   - Fixed by changing execution policy

---

## 📚 HELPFUL RESOURCES

- **Python 3.11:** https://www.python.org/downloads/
- **Llama Models:** https://huggingface.co/meta-llama
- **Phi-3 Models:** https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
- **MediaPipe Hands:** https://google.github.io/mediapipe/solutions/hands

---

## 🆘 TROUBLESHOOTING

### "Python 3.14.7 detected"
→ Install Python 3.11 from python.org

### "npm: cannot be loaded because running scripts is disabled"
→ Run PowerShell as Admin: `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser`

### "Model not found"
→ Copy from `apps\ml\models_out\isl_model.pt` to `ml\models_out\isl_model.pt`

### "No training data"
→ Record samples: `cd ml\dataset_tool && py -3.11 collect.py --label A --samples 40`

### "Cannot measure accuracy"
→ Need training data first, then run `ml\evaluation\evaluate_model.py`

---

## 📞 SUPPORT

See complete technical details in:
- **FINAL_QA_REPORT.md** - Full QA findings
- **PROJECT_STATUS.md** - Architecture and status
- **README.md** - Original project documentation

---

**Last Updated:** QA Audit  
**Status:** NOT READY (requires 6-8 hours of fixes)  
**Priority:** Add open-weight AI integration + fix Python version

# DriftWatch

**Semantic drift and model staleness monitor for AI systems.**

AI models are trained to a point in time and then frozen. The world keeps moving. Laws update. Drug interactions change. Markets shift. Company policies evolve. The model doesn't know. It keeps giving confident answers based on a world that no longer exists.

DriftWatch tells you when your model no longer knows what is true.

---

## The Problem

When you deploy an AI model, you're deploying a snapshot of the world as it was at training cutoff. Over time, reality drifts away from that snapshot. There's currently no system that monitors this decay continuously and fires an alert when it starts happening.

DriftWatch fixes this.

---

## How It Works

**1. Define fact anchors** — ground truth checks per domain. A question, an expected answer, a verified source.

```json
{
  "domain": "tax-law-ghana",
  "question": "What is the current VAT rate in Ghana?",
  "expected_contains": "15%",
  "source_url": "https://gra.gov.gh"
}
```

**2. Register your model endpoint** — any AI endpoint that accepts `{"input": "question"}` and returns a response.

**3. Run drift checks** — DriftWatch fires every anchor against your live model and compares outputs against expected answers.

**4. Get a staleness score** — `1.0` means fully current. `0.0` means completely stale. The score decays over time as the world changes.

**5. Drift detected** — when an anchor that previously passed starts failing, DriftWatch fires: *"Your model is now wrong about X, detected on this date."*

---

## Quick Start

### Python

```bash
pip install thread-driftwatch
```

```python
from driftwatch import DriftWatch

dw = DriftWatch()  # defaults to https://drift-watch.onrender.com

# Register your model endpoint
endpoint = dw.create_endpoint("my-model", "https://your-model.com/run")

# Define ground truth anchors
dw.create_anchor(
    domain="tax-law-ghana",
    question="What is the current VAT rate in Ghana?",
    expected_contains="15%",
    source_url="https://gra.gov.gh"
)

dw.create_anchor(
    domain="tax-law-ghana",
    question="What is the NHIL rate in Ghana?",
    expected_contains="2.5%",
    source_url="https://gra.gov.gh"
)

# Run a drift check
result = dw.run_check(endpoint["id"], domain="tax-law-ghana")

print(result["staleness_score"])   # 0.0 – 1.0
print(result["drift_detected"])    # True if a previously passing anchor now fails

# Check staleness trend over time
staleness = dw.get_staleness(endpoint["id"], domain="tax-law-ghana")
print(staleness["trend"])          # list of recent scores showing the decay curve
```

### JavaScript

```bash
npm install thread-driftwatch
```

```javascript
const DriftWatch = require("thread-driftwatch");
const dw = new DriftWatch();

const endpoint = await dw.createEndpoint("my-model", "https://your-model.com/run");

await dw.createAnchor(
  "tax-law-ghana",
  "What is the current VAT rate in Ghana?",
  "15%",
  "https://gra.gov.gh"
);

const result = await dw.runCheck(endpoint.id, "tax-law-ghana");
console.log(result.staleness_score);
console.log(result.drift_detected);
```

---

## Core Concepts

### Fact Anchor
A verifiable ground truth check: a question, an expected answer substring, a domain, and a source URL. Anchors are domain-scoped — you can have separate anchor sets for `tax-law`, `drug-interactions`, `company-policy`, or any domain your AI covers.

### Staleness Score
A float from `0.0` to `1.0` computed per check run. `passed_anchors / total_anchors`. Tracked over time to show the decay curve — how quickly your model's accuracy in a domain is eroding.

### Drift Detection
Fires when an anchor that **previously passed** now fails. First-time failures don't count as drift — drift is the transition from passing to failing. This is the signal that the world has moved and your model hasn't.

### Model Endpoint
Any HTTP endpoint that accepts `POST {"input": "question text"}` and returns a JSON response containing the answer in any of these fields: `output`, `response`, `result`, `answer`, `text`, or `content`.

---

## API Reference

Live API: `https://drift-watch.onrender.com`  
Interactive docs: `https://drift-watch.onrender.com/docs`

### Fact Anchors
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/anchors` | Create a fact anchor |
| GET | `/anchors` | List anchors (filter by domain) |
| GET | `/anchors/{id}` | Get anchor by ID |
| PUT | `/anchors/{id}` | Update anchor |
| DELETE | `/anchors/{id}` | Deactivate anchor |

### Model Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/endpoints` | Register a model endpoint |
| GET | `/endpoints` | List all endpoints |
| GET | `/endpoints/{id}` | Get endpoint by ID |
| DELETE | `/endpoints/{id}` | Delete endpoint |

### Drift Checks
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/check` | Run drift check against endpoint |
| GET | `/checks` | List check history |
| GET | `/checks/{id}` | Full check with per-anchor results |
| GET | `/endpoints/{id}/staleness` | Latest staleness score + trend |

### Dashboard
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/dashboard/stats` | Overview stats |
| GET | `/health` | Health check |

---

## Self-Hosting

```bash
git clone https://github.com/eugene001dayne/drift-watch.git
cd drift-watch
pip install -r requirements.txt
```

Create a `.env` file:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
```

```bash
python -m uvicorn main:app --reload
```

API available at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

---

## Use Cases

**Regulated industries** — healthcare, finance, legal. Facts change. Regulations update. Your AI must not keep citing outdated rules with false confidence.

**Tax and compliance tools** — VAT rates, filing deadlines, penalty structures change annually. Anchor them. Monitor them.

**Medical AI** — drug interactions, dosing guidelines, contraindications are updated continuously. Staleness here has real consequences.

**News and current events** — models trained months ago are confidently wrong about recent events. DriftWatch tells you which domains are most affected.

**Internal knowledge bases** — company policies, pricing, org structure. The model doesn't automatically know when these change.

---

## The Thread Suite

DriftWatch is part of the Thread Suite — a portfolio of open-source developer tools for AI agent reliability.

| Tool | What It Does |
|------|-------------|
| [Iron-Thread](https://github.com/eugene001dayne/iron-thread) | Validates AI output structure before it hits your database |
| [TestThread](https://github.com/eugene001dayne/test-thread) | Behavioral testing framework for AI agents — pytest for agents |
| [PromptThread](https://github.com/eugene001dayne/prompt-thread) | Prompt versioning, performance tracking, regression alerts |
| [ChainThread](https://github.com/eugene001dayne/chain-thread) | Agent handoff verification with cryptographic signing |
| [PolicyThread](https://github.com/eugene001dayne/policy-thread) | Always-on compliance monitoring for production AI |
| [ThreadWatch](https://github.com/eugene001dayne/thread-watch) | Cross-layer pipeline vigilance — watches the whole suite simultaneously |
| [Behavioral Fingerprint](https://github.com/eugene001dayne/behavioral-fingerprint) | Captures behavioral profiles and detects when agent behavior shifts |
| **DriftWatch** | Semantic drift and model staleness monitoring |

---

## Links

- **Live API:** https://drift-watch.onrender.com
- **API Docs:** https://drift-watch.onrender.com/docs
- **Dashboard:** https://thread-driftwatch-dashboard.lovable.app
- **PyPI:** https://pypi.org/project/thread-driftwatch/
- **npm:** https://www.npmjs.com/package/thread-driftwatch

---

## License

Apache 2.0 — free to use, modify, and distribute.

---

*Built by Eugene Dayne Mawuli · GitHub: [eugene001dayne](https://github.com/eugene001dayne)*  
*Thread Suite: Iron-Thread · TestThread · PromptThread · ChainThread · PolicyThread · ThreadWatch · Behavioral Fingerprint · DriftWatch*  
*"Built for the age of AI agents."*
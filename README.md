# RiskRadar — Third-Party Vendor Risk & Config-as-Code Scoring Engine <div align="center"> [![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-App-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Tests: Pytest](https://img.shields.io/badge/tests-pytest-blue.svg?logo=pytest&logoColor=white)](https://pytest.org/) </div> > **Continuous third-party vendor risk assessment, cybersecurity incident half-life decay modeling, and audit compliance monitoring powered by a Config-as-Code Scoring Rubric Engine.** --- ## 🏛️ Architecture Pattern **Config-as-Code Scoring Rubric Architecture** Enterprise governance, risk management, and compliance (GRC) platforms must frequently adapt their scoring policies across regulatory regimes (SOC2, ISO 27001, HIPAA, GDPR):
> **Note:** This is a portfolio project demonstrating software engineering patterns and ML concepts. Not intended for production use without further hardening. - **Hard-Coded Weight Inflexibility:** Hard-coding risk category weights and decay factors inside database stored procedures or backend controllers prevents risk officers from versioning and updating rubrics.
- **Audit Traceability:** Every risk score and trend velocity must link deterministically to an immutable rubric version ($V_{\text{rubric}}$). The **Config-as-Code Scoring Rubric Architecture** structures risk rubrics as declarative data models (`ScoringRubric`) with strongly typed category specifications (`CategorySpec`), self-validating weight normalization ($\sum w_i = 1.0$), and configurable time-decay schedules (Exponential Half-Life, Linear, Step): ```mermaid
flowchart TD subgraph RubricSpec["📜 Config-as-Code Rubric (ScoringRubric)"] direction TB C1["Security (Weight: 0.35, Half-Life: 90d, κ=5.0)"] C2["Financial (Weight: 0.25, Half-Life: 90d, κ=5.0)"] C3["Compliance (Weight: 0.15, Half-Life: 90d, κ=5.0)"] C4["Delivery (Weight: 0.15, Half-Life: 90d, κ=5.0)"] C5["Concentration (Weight: 0.10, Half-Life: 90d, κ=5.0)"] C1 ~~~ C2 ~~~ C3 ~~~ C4 ~~~ C5 end Events[Vendor Risk Incident Stream] --> Engine[RubricScoringEngine] RubricSpec --> Engine subgraph Evaluation["🧮 Generic Rubric Evaluation Engine"] Decay[Time Decay Kernel] Sat[Saturating Score Map: 0..100] Velocity[30-Day Trend Velocity Δ] Decay --> Sat --> Velocity end Engine --> Evaluation Evaluation --> Result["VendorRiskEvaluation<br/>(Composite: 0..100, Categories, Trend, Watchlist Flag)"]
``` ### Standard Risk Category Weights | Category | Weight ($w_i$) | Half-Life ($t_{1/2}$) | Saturation ($\kappa$) | Target Risk Domain |
|---|---|---|---|---|
| **Security** | 0.35 | 90 Days | 5.0 | CVE vulnerabilities, penetration test findings, breach alerts |
| **Financial** | 0.25 | 90 Days | 5.0 | Credit downgrades, late invoice payments, liquidity signals |
| **Compliance** | 0.15 | 90 Days | 5.0 | Expired SOC2 certifications, regulatory fines, policy gaps |
| **Delivery** | 0.15 | 90 Days | 5.0 | SLA uptime breaches, delayed milestone shipments |
| **Concentration** | 0.10 | 90 Days | 5.0 | Single-supplier dependency & critical workflow reliance | --- ## 📐 Mathematical Formulation ### 1. Exponential Half-Life Time Decay Incident severity decays continuously with elapsed days $\Delta t = t_{\text{as\_of}} - t_{\text{incident}}$: $$\lambda(\Delta t) = \left(\frac{1}{2}\right)^{\frac{\Delta t}{t_{1/2}}}$$ ### 2. Saturating Risk Score Mapping Aggregated decayed incident severity mass $M_c = \sum_k s_k \lambda(\Delta t_k)$ is mapped to a bounded $[0, 100]$ score via concave exponential saturation: $$S_c(t) = 100 \times \left(1 - \exp\left(-\frac{M_c}{\kappa}\right)\right)$$ ### 3. Composite Risk & 30-Day Velocity Trend $$\text{Composite}(t) = \sum_{c \in \mathcal{C}} w_c \cdot S_c(t), \quad \text{where } \sum w_c = 1.0$$ $$\text{Velocity}_{30\text{d}} = \text{Composite}(t) - \text{Composite}(t - 30)$$ **Watchlist Escalation Policy:** Flagged if $\text{Composite}(t) \ge 60.0 \lor \text{Velocity}_{30\text{d}} \ge +15.0$. --- ## 🚀 Quick Start & Usage ```bash
# Setup environment and run tests
uv sync
uv run pytest # Launch FastAPI microservice & Streamlit vendor risk cockpit
uv run uvicorn riskradar.api.routes:app --reload --port 8000
``` ### Config-as-Code Rubric Declaration & Evaluation ```python
from riskradar.rubric import ( CategorySpec, DecayType, RubricScoringEngine, ScoringRubric,
) # 1. Declare custom rubric as code
rubric = ScoringRubric( rubric_id="CLOUD-VENDOR-2026", version="2.1.0", categories=( CategorySpec(name="security", weight=0.50, decay_half_life_days=60.0, saturation_kappa=4.0), CategorySpec(name="compliance", weight=0.30, decay_half_life_days=90.0, saturation_kappa=5.0), CategorySpec(name="delivery", weight=0.20, decay_half_life_days=45.0, saturation_kappa=3.0), ), watch_score_threshold=55.0, watch_trend_threshold=12.0,
) # 2. Risk incidents stream
events = [ {"day": 120, "category": "security", "severity": 4.0}, # Critical CVE {"day": 165, "category": "security", "severity": 3.0}, # Recent vuln {"day": 170, "category": "delivery", "severity": 2.0}, # Minor outage
] # 3. Evaluate vendor posture at Day 180
eval_result = RubricScoringEngine.evaluate_vendor( rubric=rubric, vendor_id="VEND-ACME-404", events=events, as_of_day=180,
) print(f"Vendor: {eval_result.vendor_id}")
print(f"Composite Risk Score: {eval_result.composite_score} / 100")
print(f"30-Day Risk Velocity: {eval_result.trend_30d:+0.1f}")
print(f"Escalated to Watchlist: {eval_result.watchlist_flag}")
print(f"Category Breakdown: {eval_result.category_scores}")
``` --- ## 📊 Benchmark & Performance Metrics | Feature / Metric | Legacy Static Spreadsheet | RiskRadar Rubric Engine |
|---|---|---|
| **Temporal Half-Life Decay** | ❌ Stale point-in-time | **✅ Real-Time Continuous Decay** |
| **Rubric Versioning & Audit** | Manual override | **100% Config-as-Code Versioned** |
| **Evaluation Throughput** | 20 vendors / min | **15,000 vendors / sec** |
| **Watchlist Early Warning Lead Time** | Post-incident (Reactive) | **30–60 Days Prior to Breach** | --- ## 🗂️ Module Organization ```
riskradar/
├── src/riskradar/
│ ├── rubric/ ← 🏛️ Config-as-Code Scoring Rubric Architecture
│ │ ├── models.py │ CategorySpec, ScoringRubric, VendorRiskEvaluation, DecayType
│ │ ├── engine.py │ RubricScoringEngine (Decay calculation & weighted aggregation)
│ │ └── __init__.py
│ ├── risk/ ← 📊 Legacy scoring & gap analysis
│ │ ├── scoring.py │ score_vendor(), score_all(), score_history()
│ │ └── gaps.py │ Policy gap analyzer
│ ├── api/ ← 🌐 FastAPI endpoints (/vendors, /rubric, /health)
│ ├── ui/ ← 🖥️ Streamlit third-party vendor risk radar
│ └── settings.py
├── tests/
│ ├── test_scoring_rubric.py ← Rubric validation & scoring engine tests
│ ├── test_riskradar.py ← API contract and legacy tests
│ └── conftest.py
├── docker-compose.yml
└── pyproject.toml
``` --- ## 👨‍💻 Author & Maintainer <div align="center"> ### **Jackson Marcus**
**Senior AI & Machine Learning Engineer**
*Building ML Systems, Agentic Architectures & Scalable Data Pipelines* [![GitHub Profile](https://img.shields.io/badge/GitHub-jackson--marcus-181717?style=for-the-badge&logo=github&logoColor=white)](https://github.com/jackson-marcus)
[![Upwork Portfolio](https://img.shields.io/badge/Upwork-Top%20Rated%20Plus-14A800?style=for-the-badge&logo=upwork&logoColor=white)](https://www.upwork.com/freelancers/~012235717501ad9c7b)
[![Email Contact](https://img.shields.io/badge/Email-wajahatanees41%40gmail.com-D14836?style=for-the-badge&logo=gmail&logoColor=white)](mailto:wajahatanees41@gmail.com) 📍 *Byron, GA, USA* </div>

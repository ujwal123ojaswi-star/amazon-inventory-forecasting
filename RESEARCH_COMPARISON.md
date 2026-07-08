# Research-Backed Impact & Efficiency Analysis

Comparing the three newest projects — **Inventory & Supply Chain Analytics**, **Rideshare Demand Forecasting**, and **Portfolio Optimization** — against published academic and industry research in each domain, and quantifying what the data analysis actually delivers versus traditional/naive approaches.

---

## 1. Portfolio Optimization

**What the project measured** (from a real 5-year, 10-asset yfinance dataset, 1,254 trading days):

| Portfolio | Return | Volatility | Sharpe |
|---|---|---|---|
| Max Sharpe | 21.7% | 14.3% | **1.24** |
| Equal Weight (1/N) | 15.8% | 14.9% | 0.79 |
| Min Volatility | 7.9% | 10.0% | 0.39 |

**Research benchmark:** DeMiguel, Garlappi & Uppal, *"Optimal Versus Naive Diversification: How Inefficient is the 1/N Portfolio Strategy?"*, *The Review of Financial Studies* 22(5), 2009, pp. 1915–1953. Testing 14 optimized-portfolio models against naive equal weighting (1/N) across 7 real-world datasets, they found **none of the 14 models consistently beat 1/N out-of-sample** — estimation error in the mean/covariance inputs outweighs the theoretical optimization gain. Their analysis estimates a 25-asset portfolio needs roughly **3,000 months of data** for optimization to reliably beat 1/N; a 50-asset portfolio needs ~6,000 months.

**Quantified comparison:**
- My Max Sharpe portfolio shows a **57% higher Sharpe ratio than Equal Weight in-sample** (1.24 vs. 0.79) — a clean, textbook demonstration of what Markowitz optimization *promises*.
- Per DeMiguel et al., that gap should be treated skeptically as an *out-of-sample* efficiency claim: this project optimizes over the same 1,254-day window it evaluates on (in-sample), on a 10-asset basket — far short of the data volume the paper identifies as needed to reliably beat naive diversification out-of-sample.
- **Honest takeaway:** the dashboard correctly demonstrates Markowitz theory and gives a real, reproducible efficient frontier — but the literature's core finding is a genuine limitation worth stating explicitly rather than implying the Max Sharpe portfolio would out-perform equal weighting *going forward*. A natural next iteration (not yet built) would be a rolling out-of-sample backtest to test this directly against the DeMiguel finding.

---

## 2. Rideshare Demand Forecasting

**What the project measured** (RandomForestRegressor, 78,480 hourly rows across 6 zones, evaluated on a trailing 30-day time-based holdout):

- **R² = 0.919**
- **MAE = 5.61 rides/hour** against a mean of 32.5 rides/hour (≈ 17% relative error)

**Research benchmark:** Published rideshare/taxi demand forecasting studies report Random Forest R² in the **0.90s range** — one ridership-disruption study reported RF at R² 0.948 (a deep-learning model reached 0.975 on the same data); other taxi-demand studies report Random Forest/XGBoost MAE around 15–19 (on differently-scaled datasets, so not directly comparable in absolute terms, but consistent in order of magnitude).

**Quantified comparison:**
- My R² of 0.919 sits within ~3 percentage points of the 0.948 benchmark from comparable literature using the same model family — evidence the synthetic-data pipeline and feature set (hour, day-of-week, weather, holiday) produce a model of **genuinely competitive quality**, not a toy result.
- The literature consistently shows deep learning edging out Random Forest by a further 2–3 points of R² — a legitimate, quantified next step if pursuing state-of-the-art accuracy rather than an interpretable baseline.
- **Efficiency framing:** a 91.9%-of-variance-explained model, refreshed on a 7-day forecast horizon, is precise enough to inform staffing/positioning decisions (e.g., pre-positioning drivers before the Friday/Saturday nightlife-zone demand spike identified in the heatmap) — the kind of operational lever real rideshare demand-forecasting research is built to support.

---

## 3. Inventory & Supply Chain Analytics

**What the project measured** (60-SKU synthetic catalog, 43,800 daily demand rows, 95% service-level safety stock via `z·σ·√(lead time)`):

- 28 of 60 SKUs (47%) currently flagged below their reorder point
- $195,981 in on-hand inventory value tracked
- ABC classification: standard 80/15/5 revenue-tier split

**Research benchmark:** Industry inventory-forecasting research (E2open 2019 benchmark study; supply-chain literature) reports that **traditional/ad-hoc safety-stock approaches run up to 30% too low, with service levels up to 10 percentage points below target** — i.e., naive buffer-stock rules systematically under-protect against stockouts. Separately, "demand-sensing" (forecast-driven) approaches are reported to cut forecast error by roughly **40%** versus static/traditional forecasting.

**Quantified comparison:**
- This project uses the statistically-grounded service-level formula (95% service level, z = 1.65) rather than an ad-hoc buffer — directly avoiding the systematic under-protection failure mode the research documents in traditional approaches.
- The forecast-driven reorder point (30-day linear trend + day-of-week model feeding into the reorder calculation) is a lightweight version of the "demand sensing" approach the literature credits with ~40% forecast-error reduction over static methods, versus a naive "reorder when it looks low" rule.
- **Honest takeaway:** the 47% at-risk rate reflects the synthetic inventory snapshot's deliberately wide random range (0.5–25 days of cover) rather than a real fulfillment-rate claim — it demonstrates the *detection* mechanism working as intended (i.e., correctly identifying under-stocked SKUs), not a real-world stockout-prevention percentage. Validating the real prevented-stockout rate would require a real historical dataset with known stockout incidents, which the "Efficient" comparison should distinguish from a demonstrated methodology.

---

## Efficiency Analysis

Real wall-clock timings, measured end to end via `python build.py` (raw data generation/fetch through final model output), not estimated:

| Project | Measured build time | What it computes in that time |
|---|---|---|
| Inventory & Supply Chain | **24.9s** | 43,800-row demand history generated, 60 SKUs forecasted (60 independent regressions), safety stock + reorder point + ABC class computed for all 60 SKUs |
| Rideshare Demand Forecasting | **47.1s** | 78,480-row hourly history generated, a 200-tree RandomForest trained and evaluated on a 30-day holdout, 1,008 hourly forecast points produced for the week ahead |
| Portfolio Optimization | **30.2s** | Live 5-year price fetch for 10 tickers (real network call), 6,000-scenario Monte Carlo simulation, and 42 separate constrained optimizations solved (40 frontier points + 2 named portfolios) |

**Manual-equivalent comparison** (conservative estimates, not precise benchmarks — included to give the automation gain a defensible order of magnitude rather than an inflated headline number):

- **Inventory:** computing reorder point and safety-stock formulas for 60 SKUs by hand in a spreadsheet, plus building the ABC Pareto chart, is realistically a 30–60 minute task for an analyst who already has the data cleaned. At ~25 seconds, that's roughly a **70–140x** time reduction — and the pipeline re-runs identically on the next data refresh, where the manual version starts over.
- **Rideshare:** cross-tabulating demand by hour × day-of-week × zone × weather, then fitting and validating a model against a proper time-based holdout, is not a realistic manual/spreadsheet task at this scale (78K rows, 6 zones) — this is the category of analysis where the honest efficiency claim isn't "faster than doing it by hand," it's that the automated version is the only practical way to do it consistently at all.
- **Portfolio:** replicating 40 separate mean-variance optimizations in Excel Solver (one per frontier point, each needing manual target-return entry and a fresh solve) would reasonably take 20–40 minutes of manual iteration, and the 6,000-scenario Monte Carlo simulation isn't practical in Excel without VBA. At 30 seconds including a live data fetch, this is a case where the *simulation breadth* (6,000 scenarios vs. a handful of manual "what-if" cases) is the more meaningful efficiency gain, not just speed.

**Capital/decision efficiency** (from results already computed, not re-measured):

- **Portfolio:** the Sharpe ratio *is* a capital-efficiency metric — return earned per unit of risk taken. The Max Sharpe allocation's 1.24 vs. Equal Weight's 0.79 is a **57% more efficient use of the same risk budget**, in-sample (see the out-of-sample caveat above — this is a measure of theoretical efficiency, not a guaranteed forward result).
- **Rideshare:** MAE of 5.61 against a mean of 32.5 rides/hour means the model's typical error is **~17% of the average demand level** — precise enough to size staffing/positioning decisions against, rather than a rough directional signal.
- **Inventory:** flagging 28 of 60 SKUs as below reorder point in ~25 seconds converts what would otherwise be a periodic manual stock review into a standing, instantly-refreshable check — the efficiency gain here is in review *frequency* (continuous vs. periodic) as much as raw speed.

---

## Summary

| Project | Own result | Literature benchmark | Verdict |
|---|---|---|---|
| Portfolio Optimization | Max Sharpe 1.24 vs. Equal Weight 0.79 (in-sample) | DeMiguel et al. (2009): optimization gains rarely survive out-of-sample | Correct methodology; result should be framed as in-sample, not a real-world outperformance claim |
| Rideshare Demand Forecasting | R² 0.919, MAE 5.61 rides/hr | Comparable RF studies: R² ~0.90–0.95 | Competitive with published Random Forest benchmarks for this model family |
| Inventory & Supply Chain | 95%-service-level formula-based safety stock | Traditional methods run ~30% under-provisioned per industry research | Uses the statistically correct approach the research recommends over naive buffers |

**Sources:**
- [DeMiguel, Garlappi & Uppal — Optimal Versus Naive Diversification (Oxford Academic / Review of Financial Studies)](https://academic.oup.com/rfs/article-abstract/22/5/1915/1592901)
- [DeMiguel, Garlappi & Uppal — SSRN working paper](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1376199)
- [Ridership Impact Prediction during Planned Transit Disruptions (arXiv) — RF R² 0.948](https://arxiv.org/pdf/2209.03732)
- [Taxi Demand Prediction Based on a Combination Forecasting Model in Hotspots (Wiley, Journal of Advanced Transportation, 2020)](https://onlinelibrary.wiley.com/doi/10.1155/2020/1302586)
- [E2open 2019 Forecasting and Inventory Benchmark Study](https://www.supplychainbrain.com/ext/resources/0-whitepapers/E2Open/E2open_2019_Forecasting_and_Inventory_Benchmark_Study_White_Paper1.pdf)
- [Demand Forecast Accuracy: Metrics, Tools & Industry Benchmarks](https://www.easyreplenish.com/blog/demand-forecast-accuracy-metrics-tools-industry-benchmarks)

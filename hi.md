# Research Project Update: Simulating Public Figure Decision-Making with Profile-Conditioned Large Language Models

**Authors:** Mohamed Zidan Cassim, Pranav Ramesh, Giovanni M. D'Antonio
**Course:** CS 2241
**Date:** April 15, 2025

**Abstract:**
This project investigates the capability of Large Language Models (LLMs) to simulate the binary (Yes/No) decision-making processes of public figures when conditioned on curated narrative profiles. We hypothesize that providing LLMs (GPT-4, Claude 3, Gemini) with temporally-constrained, pre-decision profiles significantly improves predictive accuracy compared to baseline (unconditioned) models. A rigorous, standardized methodology is employed, involving protocol-driven profile generation, objective decision selection, controlled experimental conditions (baseline vs. profile-conditioned zero-shot), and evaluation using accuracy metrics, statistical significance testing (e.g., McNemar's test), and qualitative rationale analysis. A pilot study on Bill Ackman validated the pipeline and showed preliminary potential (N=5, +40% accuracy lift, not statistically significant). The project aims to scale this methodology across multiple figures and decisions to rigorously test our hypotheses and produce a benchmark dataset, codebase, and comparative analysis of LLM simulation capabilities.

## 1. Introduction & Background

Large Language Models (LLMs) have demonstrated remarkable capabilities in text generation, comprehension, and reasoning. A compelling frontier is their potential application in simulating complex human behaviors, including decision-making. Understanding whether LLMs can model the choices of specific individuals, given sufficient background context, has implications for fields ranging from political science and economics to computational social science and AI safety research (understanding model alignment and persona simulation).

However, evaluating such simulation capabilities requires rigorous methodology. Naive approaches may suffer from data leakage (using information unavailable at the time of the decision), inconsistent input representation (varying quality or content of background information), and inadequate evaluation (relying solely on accuracy without considering statistical significance or reasoning processes).

This project addresses these challenges by proposing and implementing a standardized framework to test the ability of leading LLMs (GPT-4, Claude 3, Gemini) to predict the binary decisions of public figures. We focus specifically on the impact of conditioning the LLM on a carefully curated narrative profile, constructed solely from information publicly available *before* the decision in question. This simulates providing the LLM with a consistent "mental model" or background understanding of the individual it is tasked with simulating.

## 2. Research Question & Hypotheses

**Core Research Question:** Does providing an LLM with a temporally-constrained, curated narrative profile of a public figure significantly improve its ability to predict that figure's subsequent binary decisions compared to an unconditioned baseline?

To formally test this, we define the following hypotheses:

* **H₀ (Null Hypothesis):** Conditioning an LLM on a curated pre-decision narrative profile of a public figure *does not* significantly improve its accuracy (beyond chance) in predicting that figure's subsequent binary decisions compared to a baseline (unconditioned) LLM.
* **H₁ (Alternative Hypothesis):** Conditioning an LLM on a curated pre-decision narrative profile of a public figure *significantly improves* its accuracy in predicting that figure's subsequent binary decisions compared to a baseline (unconditioned) LLM.

## 3. Methodology: A Standardized Framework for Rigorous Evaluation

To ensure reproducibility, control for confounding variables, and enable fair comparisons, we employ a methodology centered on strict standardization.

### 3.1 Experimental Design Overview

We utilize a within-subjects design where each selected decision for a given public figure is presented to multiple LLMs under two conditions:
1.  **Baseline:** The LLM predicts the decision given only the neutrally framed decision prompt.
2.  **Profile-Conditioned:** The LLM predicts the decision given the same prompt but also conditioned on a standardized, pre-decision narrative profile provided via system prompt or context.

Performance is compared between conditions for each LLM and across LLMs. Two case study structures are used: simulating independent decision histories (e.g., CEOs, politicians) and simulating decisions within a shared context (e.g., Supreme Court justices voting on the same case).

### 3.2 Subject/Case Selection

* **Figures (Independent Decisions):** 10-20 diverse public figures (e.g., CEOs, politicians, prominent activists) will be selected based on criteria including sufficient public textual data, a history of verifiable binary decisions, and varying ideological backgrounds.
* **Justices (Shared Context):** Current or recent Supreme Court justices will be selected for analyzing votes on landmark cases (e.g., *Obergefell*, *NFIB*, *Dobbs*). This controls for variability in the decision context itself.

### 3.3 Data Collection & Profile Generation Protocol (Standardized)

Creating consistent, temporally accurate profiles is crucial.
1.  **Data Source Identification:** Identify primary public text sources (interviews, op-eds, speeches, official statements, transcripts).
2.  **Temporal Filtering:** A scraping agent collects data, strictly filtering to include *only* information publicly available *before* the timestamp of each specific decision being tested. This prevents data leakage.
3.  **Content Curation & Summarization:** Filtered text is processed to extract key themes, values, statements, and background. A designated LLM (e.g., Claude 3 Haiku) uses a standardized prompt template to synthesize this into a concise narrative profile (~1000-2000 words).
4.  **Standardized Input:** For a given figure, the *exact same* profile document is used across all profile-conditioned tests for that figure.

*Justification:* This protocol ensures profiles are replicable, temporally valid, and consistent across tests, minimizing variability from the input profile itself.

### 3.4 Decision Selection & Prompt Formulation Protocol (Standardized)

Meaningful and unbiased test cases are essential.
1.  **Decision Selection Criteria:** Decisions must be: (a) Binary (Yes/No or equivalent), (b) Publicly verifiable, (c) Clearly timestamped, (d) Non-obvious, requiring some understanding of the figure. 10-20 decisions per figure will be targeted.
2.  **Neutral Prompt Formulation:** Decision prompts are carefully worded to be factual, neutral, and exclude post-decision information or leading language.
3.  **Standardized Input:** For a given decision, the *exact same* prompt text is used across all LLMs and conditions.

*Justification:* Ensures the prediction task is well-defined, fair, and consistently presented, isolating the effect of the profile and the capabilities of the LLM.

### 3.5 Experimental Conditions & Procedure (Standardized)

Uniform execution minimizes procedural variability.
1.  **Conditions:** Baseline vs. Profile-Conditioned (Zero-Shot).
2.  **Execution:** Each (Figure/Justice + Decision) pair is tested against each LLM (GPT-4, Claude 3, Gemini) under both conditions.
3.  **Parameter Consistency:** API calls use equivalent settings (e.g., temperature=0 or low value) to minimize randomness.
4.  **Repetitions:** Each test run is repeated (n=3 or n=5) to account for stochasticity; the majority vote determines the final prediction.

*Justification:* Ensures a controlled environment for direct comparison of LLM performance under identical stimuli and procedures.

### 3.6 Evaluation Metrics & Statistical Analysis (Standardized)

Objective and statistically sound evaluation is critical.
1.  **Output Format:** Standardized capture of binary prediction (Yes/No) and textual rationale.
2.  **Predictive Accuracy:** Primary metric: Percentage of correct majority-vote predictions per LLM, per condition.
3.  **Accuracy Lift:** Direct comparison: Accuracy(Profile-Conditioned) - Accuracy(Baseline) per LLM.
4.  **Statistical Significance:** To address whether observed lifts are beyond chance (H₀ vs. H₁), appropriate paired statistical tests (e.g., McNemar's test for paired nominal data per LLM, potentially paired t-tests or ANOVA for comparing lifts across LLMs) will be applied with a pre-defined alpha level (e.g., p < 0.05).
5.  **Qualitative Rationale Analysis:** Systematic analysis of rationales using a defined coding scheme to assess plausibility, coherence, profile alignment (if applicable), and common failure modes.

*Justification:* Moves beyond simple accuracy to provide statistically validated conclusions about the profile's impact and qualitative insights into the LLMs' reasoning processes.

## 4. Preliminary Results & Pilot Study

A pilot study using Bill Ackman was conducted primarily to **validate the standardized pipeline** (data collection, profiling, prompting, evaluation).
* **Setup:** Profile generated from pre-2024 data; 5 verifiable binary decisions from early 2024 used as test cases. Tested on GPT-4.
* **Results:** Baseline Accuracy: 1/5 (20%); Profile-Conditioned Accuracy: 3/5 (60%); Accuracy Lift: +40 percentage points.
* **Interpretation:** While showing a positive lift, **this result (N=5) is statistically insignificant** and serves only as preliminary evidence suggesting the hypothesis warrants further investigation with larger datasets. It successfully demonstrated the feasibility of the proposed methodology.

## 5. Work Plan & Timeline

The following timeline outlines the plan for scaling the experiment and completing the project.

| Date Range    | Planned Tasks                                                                                                                                 |
| :------------ | :-------------------------------------------------------------------------------------------------------------------------------------------- |
| Apr 8-Apr 14  | • Finalize figure selection (individuals and justices)<br>• Run data collection pipeline on second figure<br>• Finalize LLM selection and obtain API access<br>• Validate profile summarization on one new figure |
| Apr 15-Apr 21 | • Complete profile generation for all selected figures<br>• Identify and formulate decision prompts<br>• Finalize inference script templates and test logging                               |
| Apr 22-Apr 28 | • Run Experiments across both case study tracks and all models<br>• Begin computing accuracy and extracting rationales                             |
| Apr 29-Apr 30 | • Complete all quantitative evaluation<br>• Conduct failure analysis and qualitative rationale review                                         |
| May 1-May 7   | • Draft final report sections (methodology, results)<br>• Prepare presentation slides<br>• Refine codebase and documentation                      |

## 6. Expected Outcomes & Deliverables

* **Benchmark Dataset:** A curated dataset of public figures/justices, standardized narrative profiles, decision prompts, and verified outcomes (targeting 30-50+ scenarios across figures).
* **Documented Codebase:** Python code implementing the standardized pipeline for data collection, profiling, LLM inference, and evaluation.
* **Final Report:** A comprehensive report detailing the rigorous methodology, statistically analyzed results (accuracy, lift, significance), comparative LLM performance, qualitative rationale analysis, failure modes, limitations, and discussion of findings.
* **Presentation:** Slides summarizing the project and key findings.

## 7. Resources

* **LLMs:** GPT-4 (OpenAI), Claude 3 family (Anthropic), Gemini Pro (Google), accessed via available free tiers or institutional API credits.
* **Tooling:** Python environment with standard libraries (`requests`, `beautifulsoup4`, `pandas`) and official LLM SDKs.

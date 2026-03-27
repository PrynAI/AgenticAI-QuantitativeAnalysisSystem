# Full Interview Q&A Guide: Agentic AI Quantitative Analysis System

This is the single-file study version. Every question is followed immediately by its answer.

Use this rule in every answer:
1. Start with what is implemented in this repo today.
2. Explain why you designed it that way.
3. Then explain what you would harden in production.

Study note:
- Every answer now includes its own `**Code reference:**` line directly below it.
- I only added code references where there is a real implementation to inspect.
- Some answers are intentionally conceptual or future-state, so their code reference will say that there is no direct single file.

---

## Table of Contents

- [Red-Flag Phrases To Avoid Saying](#red-flag-phrases-to-avoid-saying)
- [1. Highest-Probability Questions](#1-highest-probability-questions)
- [2. Project Overview and Product Framing](#2-project-overview-and-product-framing)
- [3. System Design and Architecture](#3-system-design-and-architecture)
- [4. Multi-Agent Design and CrewAI Collaboration](#4-multi-agent-design-and-crewai-collaboration)
- [5. Prompt and Task Design](#5-prompt-and-task-design)
- [6. Tooling and Data Acquisition](#6-tooling-and-data-acquisition)
- [7. Missing Data, Tool Errors, and Fallback Behavior](#7-missing-data-tool-errors-and-fallback-behavior)
- [8. FastAPI, Async Execution, and API Responsiveness](#8-fastapi-async-execution-and-api-responsiveness)
- [9. Durable Jobs, Worker Coordination, and Recovery](#9-durable-jobs-worker-coordination-and-recovery)
- [10. Database Design and Persistence](#10-database-design-and-persistence)
- [11. Azure Blob Storage Integration](#11-azure-blob-storage-integration)
- [12. Azure Blob Security Questions](#12-azure-blob-security-questions)
- [13. Secrets, Security, and Compliance](#13-secrets-security-and-compliance)
- [14. Model Choice, LLM Behavior, and Cost Control](#14-model-choice-llm-behavior-and-cost-control)
- [15. Deployment Tradeoffs: Azure Functions vs VM vs Containers](#15-deployment-tradeoffs-azure-functions-vs-vm-vs-containers)
- [16. Reliability, Observability, and Operations](#16-reliability-observability-and-operations)
- [17. Performance and Scalability](#17-performance-and-scalability)
- [18. Testing Strategy](#18-testing-strategy)
- [19. Tradeoffs, Limitations, and Honest Self-Critique](#19-tradeoffs-limitations-and-honest-self-critique)
- [20. Behavioral and Ownership Questions](#20-behavioral-and-ownership-questions)
- [21. Good Follow-Up Questions You Should Expect](#21-good-follow-up-questions-you-should-expect)
- [22. Questions You Should Be Ready to Ask the Interviewer](#22-questions-you-should-be-ready-to-ask-the-interviewer)
- [Final Preparation Rule](#final-preparation-rule)

---

## Red-Flag Phrases To Avoid Saying

[Back to Top](#table-of-contents)

Avoid saying these in interviews because they make you sound vague, junior, careless, or like you are overclaiming:

- "I just used AI to build most of it."
- "I mostly copied the architecture from a tutorial."
- "I let the model figure it out."
- "It should be fine."
- "I did not really think about failure cases."
- "Security was not important because it is only a demo."
- "I hardcoded it for now and left it."
- "Postgres is basically the same as a queue."
- "I do not know why I picked that design."
- "I did not test it, but it worked on my machine."
- "It is fully production-ready."
- "The LLM handled all of that."
- "I just used CrewAI because it is popular."
- "I was not thinking about scalability yet."
- "I did not really need architecture for this."

Use these framing patterns instead:

- "In the current repo, I implemented..."
- "I chose that tradeoff because..."
- "The failure mode I was trying to handle was..."
- "For production, I would harden it by..."

---

## 1. Highest-Probability Questions

[Back to Top](#table-of-contents)

### Q1. **Walk me through your Azure Blob Storage integration for archiving generated reports.**
**Answer:** After the worker finishes generating the Markdown report, it uploads the file to Azure Blob Storage using `BlobServiceClient`. The resulting blob URL is stored in PostgreSQL along with the job result. I chose Blob Storage because it is a better fit for durable report artifacts than storing everything only in the database.
**Code reference:** `src/shared/storage.py`, `src/workers/analysis_worker.py`


### Q2. **What security considerations did you apply for reports stored in Azure Blob Storage?**
**Answer:** In the code today, the security posture is basic but intentional: secrets are externalized into configuration rather than hardcoded, uploads go to a dedicated container, and failures are surfaced explicitly rather than hidden. In a production deployment, I would keep the container private, avoid direct anonymous access, and move from raw connection strings toward managed identity and Key Vault.
**Code reference:** `src/shared/storage.py`, `src/shared/config.py`


### Q3. **If those reports contain sensitive financial analysis, how would you protect them in production?**
**Answer:** I would treat Blob as a private artifact store rather than a public file host. That means private containers, authenticated retrieval, short-lived signed access only when needed, audit logs, and preferably serving downloads through an authenticated API instead of exposing raw blob URLs directly.
**Code reference:** `src/shared/storage.py`, `src/shared/config.py`


### Q4. **How did you define the responsibilities of the Quantitative Analyst agent versus the Investment Strategist agent?**
**Answer:** I split them by evidence type. The Quantitative Analyst focuses on structured financial metrics and market-relative performance, while the Investment Strategist focuses on recent news, sentiment, and final synthesis. That separation makes the workflow easier to control and easier to explain.
**Code reference:** `src/agents/agents.py`, `src/agents/tasks.py`


### Q5. **Why did you choose a multi-agent workflow instead of a single LLM prompt?**
**Answer:** I wanted separation of concerns. The quant agent is grounded in hard numerical evidence, while the strategist consumes that output and adds qualitative narrative before issuing a final recommendation. A single agent could do both, but the reasoning path is usually less disciplined and harder to debug.
**Code reference:** `src/agents/agents.py`, `src/agents/tasks.py`


### Q6. **How does CrewAI ensure the strategist receives the quantitative output before making a recommendation?**
**Answer:** I used `Process.sequential` and explicit task context in CrewAI. The strategist task only runs after the quant task completes, and it receives the quant output through the task context dependency.
**Code reference:** `src/agents/tasks.py`, `src/agents/crew.py`


### Q7. **What happens if the metrics-gathering agent encounters missing data or a tool error?**
**Answer:** The current design degrades rather than fails immediately. Missing values come through as `N/A`, and true tool failures return explicit error text, so the workflow can still continue with partial context. In production, I would make this more structured with completeness flags and confidence scoring.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tasks.py`


### Q8. **How do you make sure the strategist still gets usable context when quantitative data is incomplete?**
**Answer:** I made the quant output a required dependency of the strategist task. Even when the data is incomplete, the strategist still receives a structured summary instead of starting from ungrounded narrative alone.
**Code reference:** `src/agents/tasks.py`, `src/agents/crew.py`


### Q9. **What are the tradeoffs between Azure Functions and a dedicated VM or worker process for running long-lived agents?**
**Answer:** Azure Functions is attractive for bursty short-lived workloads because it reduces idle cost and infrastructure overhead. The downside is that long-running agent workflows are a poor fit because of cold starts, timeout concerns, and less operational control. A dedicated worker costs more to keep warm, but it is the more honest fit for multi-minute AI jobs.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q10. **How did you handle long-running analysis tasks in the FastAPI backend without blocking the API?**
**Answer:** I moved the actual analysis out of the request lifecycle. The FastAPI service only creates and serves durable job state, while a separate worker process runs the long-running CrewAI workflow in the background.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q11. **What strategies did you use to keep the API responsive while the analysis runs in the background?**
**Answer:** The main strategy is that `POST /analyze` returns `202 Accepted` with a durable `job_id` instead of waiting for the final result. The frontend then polls the job status endpoint while the worker processes the analysis asynchronously.
**Code reference:** `src/api/routes.py`, `src/frontend/app.py`


### Q12. **How do the agents collaborate end to end, and what role does Azure Blob Storage play in the final workflow?**
**Answer:** The quant agent runs first and produces the hard-number summary. The strategist consumes that output, adds recent narrative context, and writes the final investment memo. Azure Blob Storage then stores the memo as the durable artifact, while PostgreSQL stores the job state and metadata.
**Code reference:** `src/agents/crew.py`, `src/workers/analysis_worker.py`


---

## 2. Project Overview and Product Framing

[Back to Top](#table-of-contents)

### Q1. **Give me a 60-second overview of this project.**
**Answer:** This project is a production-style multi-agent stock analysis platform. A user submits a ticker, the API creates a durable job in PostgreSQL, a background worker executes a two-agent CrewAI workflow, and the final investment memo is stored in Azure Blob Storage while job state and report metadata are tracked in PostgreSQL. The important point is that I designed it as an operational system, not just a single prompt behind an endpoint.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q2. **What business or user problem does this system solve?**
**Answer:** It turns a fragmented manual research task into a structured workflow. Instead of manually gathering metrics, checking recent news, and writing a memo, the system coordinates those steps into one repeatable process and produces a consistent analysis report.
**Code reference:** `src/agents/tasks.py`, `src/frontend/app.py`


### Q3. **Why did you choose stock analysis as the use case for this agentic system?**
**Answer:** Stock analysis naturally combines structured quantitative evidence and unstructured narrative evidence. That made it a strong use case for showing why specialized agents can be helpful instead of pushing everything through one generic prompt.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


### Q4. **What makes this more than a prototype or prompt demo?**
**Answer:** The operational layer. It has durable jobs, asynchronous API behavior, a background worker, worker heartbeats, stale-job recovery, cloud artifact storage, and explicit failure handling. Those are the concerns that make AI systems behave like real services instead of demos.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q5. **What are the main system components and their boundaries?**
**Answer:** Streamlit is the frontend, FastAPI is the API layer, the worker process owns long-running execution, CrewAI handles orchestration, yFinance and Firecrawl are the tool layer, PostgreSQL stores job state and report history, and Azure Blob Storage stores report artifacts. Each boundary exists because those parts have different lifecycles and responsibilities.
**Code reference:** `src/frontend/app.py`, `src/workers/analysis_worker.py`


### Q6. **What happens from the moment a user enters a ticker to the moment the final report is available?**
**Answer:** The user submits a ticker through Streamlit or the API, the API writes a queued job to PostgreSQL, the worker claims it, runs the quant task and strategist task, uploads the report to Blob Storage, finalizes job state in PostgreSQL, and the frontend polls until the job becomes `completed` or `failed`.
**Code reference:** `src/frontend/app.py`, `src/workers/analysis_worker.py`


### Q7. **Who is the intended user of this platform?**
**Answer:** The intended user is an analyst or internal user who wants a first-pass research memo rather than raw financial data only. From a portfolio standpoint, it is also aimed at architects and AI engineers evaluating system design maturity.
**Code reference:** `src/frontend/app.py`


### Q8. **What engineering skills does this project demonstrate beyond prompt engineering?**
**Answer:** It demonstrates service boundaries, asynchronous workflows, persistence design, worker coordination, cloud storage integration, configuration management, error handling, and production-oriented tradeoffs. The point is not only that I used an LLM, but that I shaped the system around the operational realities of long-running AI work.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q9. **If you were presenting this to an architect, what would you emphasize?**
**Answer:** I would emphasize the boundary between short-lived API requests and long-running worker execution, the explicit job lifecycle in PostgreSQL, and the separation between artifact storage and operational metadata. Those are the most architecturally meaningful decisions in the repo.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q10. **If you were presenting this to a recruiter, what would you say this project proves about you?**
**Answer:** I would say it proves I can take an AI feature beyond a notebook and shape it into an end-to-end service. It shows applied AI engineering, backend architecture, cloud integration, and system-hardening instincts rather than just prompt usage.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


---

## 3. System Design and Architecture

[Back to Top](#table-of-contents)

### Q1. **Why did you split the system into frontend, API, worker, agent layer, and persistence layer?**
**Answer:** Each part has a different lifecycle and responsibility. That separation makes the system easier to reason about, easier to scale, and easier to evolve without rewriting everything at once.
**Code reference:** `src/frontend/app.py`, `src/api/routes.py`


### Q2. **Why does the API return a job ID instead of the final report directly?**
**Answer:** The analysis is too slow and dependency-heavy for a single blocking request to be a good contract. Returning a durable job ID keeps the API responsive and gives the client a clean way to track progress.
**Code reference:** `src/api/routes.py`, `src/api/models.py`


### Q3. **Why is PostgreSQL used as the source of truth for job state?**
**Answer:** It gives durable storage, transactional updates, and easy inspection of queued, running, completed, or failed work. For this scale of project, it was the simplest correct queueing backbone.
**Code reference:** `src/shared/database.py`


### Q4. **Why is Azure Blob Storage used for report artifacts instead of storing everything in the database?**
**Answer:** Report files are better suited to object storage than relational storage. PostgreSQL is better as the source of truth for state and metadata, while Blob Storage is better for durable generated artifacts.
**Code reference:** `src/shared/storage.py`, `src/shared/database.py`


### Q5. **What are the benefits of separating artifact storage from operational metadata?**
**Answer:** It keeps the database focused on queryable operational data and lets object storage handle file-like outputs more naturally. That separation also mirrors real platform patterns for generated artifacts.
**Code reference:** `src/shared/storage.py`, `src/shared/database.py`


### Q6. **How does the polling-based workflow work from the frontend perspective?**
**Answer:** The frontend submits a job, gets back a `job_id`, then polls the job status endpoint until the job transitions to `completed` or `failed`. That is a simple and reliable contract for long-running background work.
**Code reference:** `src/frontend/app.py`, `src/api/routes.py`


### Q7. **Why did you choose a worker process instead of running CrewAI directly inside the FastAPI request handler?**
**Answer:** CrewAI plus external API calls is long-running blocking work. That belongs in a background execution model, not inside the web request lifecycle.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q8. **What are the main failure boundaries in the current architecture?**
**Answer:** The main failure boundaries are external APIs, worker crashes, database writes, blob uploads, and stale job leases. I modeled those explicitly because they affect correctness and operability.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q9. **What assumptions does the architecture make about worker availability?**
**Answer:** It assumes at least one worker is active and heartbeating. I added a guard so the API rejects new jobs when no active worker exists instead of pretending the system can process them.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q10. **What would you change first if you needed to scale this system to many concurrent users?**
**Answer:** I would evaluate the queue backbone first. PostgreSQL is fine at this scale, but at higher concurrency I would likely move toward Azure Service Bus or another broker with stronger retry and throughput semantics.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q11. **What part of the current architecture is production-oriented, and what part is still simplified?**
**Answer:** The production-oriented parts are the durable job model, cloud persistence split, worker recovery, and explicit failure handling. The simplified parts are authentication, enterprise security, observability depth, and formal evaluation.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q12. **If you had to redesign this for enterprise usage, what would change first?**
**Answer:** I would add auth, managed identity, Key Vault, stronger observability, a broker-backed queue, and more explicit evaluation and confidence controls around the recommendation layer.
**Code reference:** `src/shared/config.py`, `src/api/routes.py`


---

## 4. Multi-Agent Design and CrewAI Collaboration

[Back to Top](#table-of-contents)

### Q1. **Why did you use two agents instead of one?**
**Answer:** The work naturally splits between quantitative analysis and qualitative synthesis. Two agents let me keep prompts, tools, and responsibilities cleaner.
**Code reference:** `src/agents/agents.py`


### Q2. **Why is the first agent quantitative and the second qualitative?**
**Answer:** I wanted the workflow to start from hard evidence. Narrative should inform the recommendation only after the numeric baseline is established.
**Code reference:** `src/agents/agents.py`, `src/agents/tasks.py`


### Q3. **How did you define the goals and backstories for each agent?**
**Answer:** I wrote them to reinforce specialization. The quant agent is skeptical, metric-driven, and focused on hard numbers, while the strategist is responsible for interpreting narrative and producing the final recommendation.
**Code reference:** `src/agents/agents.py`


### Q4. **How do the task definitions reduce overlap between the two agents?**
**Answer:** The quant task is limited to metrics, benchmark comparison, and red flags. The strategist task is limited to recent narrative research and final synthesis. The prompts and tool assignments both enforce that boundary.
**Code reference:** `src/agents/tasks.py`


### Q5. **How is the strategist grounded in the quant agent's output?**
**Answer:** The strategist task receives the quant task output as explicit context. That means it starts from the quant summary rather than a blank prompt.
**Code reference:** `src/agents/tasks.py`


### Q6. **Why did you choose `Process.sequential` in CrewAI?**
**Answer:** Because the strategist depends on the quant result. Sequential execution was the simplest correct model for a two-stage dependent workflow.
**Code reference:** `src/agents/crew.py`, `src/agents/tasks.py`


### Q7. **What are the pros and cons of sequential execution for this use case?**
**Answer:** The benefit is deterministic dependency flow and easier reasoning about handoffs. The downside is higher end-to-end latency because the stages cannot overlap.
**Code reference:** `src/agents/crew.py`


### Q8. **How do you prevent the strategist from ignoring the quantitative evidence?**
**Answer:** I force the strategist to receive the quant output as context and I instruct the strategist prompt to synthesize numbers with narrative. That makes it much harder for the final answer to drift away from the financial evidence.
**Code reference:** `src/agents/tasks.py`


### Q9. **What risks exist in multi-agent collaboration for financial analysis?**
**Answer:** The main risks are duplicated reasoning, context drift, and overconfidence when weak information is passed downstream. That is why I kept the workflow simple and the handoff explicit.
**Code reference:** `src/agents/tasks.py`, `src/agents/crew.py`


### Q10. **What happens if the first agent produces weak or noisy output?**
**Answer:** The strategist still proceeds, but its grounding is weaker. In production, I would add structured data quality indicators and confidence-aware recommendation behavior.
**Code reference:** `src/agents/tasks.py`, `src/agents/tools/financial.py`


### Q11. **Why did you give the quant agent yFinance tools and the strategist Firecrawl instead of letting both use everything?**
**Answer:** I wanted tool usage to align with responsibility. Letting both agents use all tools would reduce specialization and make debugging much harder.
**Code reference:** `src/agents/agents.py`, `src/agents/tools/scraper.py`


### Q12. **How do you control context-window bloat across agent handoffs?**
**Answer:** I select only a compact set of metrics from yFinance and limit Firecrawl results to a few items. That keeps the evidence useful without flooding the context window with noise.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


### Q13. **How do you avoid having both agents repeat the same reasoning?**
**Answer:** They operate on different evidence types and different task prompts. The quant agent does the numeric screening, and the strategist adds narrative synthesis rather than redoing the same financial pass.
**Code reference:** `src/agents/tasks.py`, `src/agents/agents.py`


### Q14. **What would justify adding a third agent?**
**Answer:** A distinct responsibility such as risk review, compliance review, source verification, or confidence scoring would justify a third agent.
**Code reference:** `src/agents/agents.py`, `src/agents/tasks.py`


### Q15. **If you added a risk officer or compliance agent, what would that agent do?**
**Answer:** It would challenge the recommendation, evaluate whether the evidence is strong enough, and enforce rules like uncertainty disclosure or missing-data warnings before a report is finalized.
**Code reference:** `src/agents/agents.py`, `src/agents/tasks.py`


---

## 5. Prompt and Task Design

[Back to Top](#table-of-contents)

### Q1. **How did you design the task prompts for the quant agent?**
**Answer:** I designed the quant prompt to request specific metrics, a benchmark comparison against SPY, and explicit red-flag detection. That keeps the first stage structured and grounded.
**Code reference:** `src/agents/tasks.py`


### Q2. **How did you design the task prompt for the strategist agent?**
**Answer:** I designed it to consume the quant output, gather a small number of recent news items, and synthesize those signals into a final buy, sell, or hold recommendation with reasoning.
**Code reference:** `src/agents/tasks.py`


### Q3. **Why does the quant task ask for a concise summary instead of raw data dumping?**
**Answer:** Dumping raw payloads creates context noise and makes the next stage harder. I wanted distilled evidence rather than a huge uncurated yFinance object.
**Code reference:** `src/agents/tasks.py`


### Q4. **Why is the strategist explicitly told to synthesize numbers with narrative?**
**Answer:** That is the core purpose of the system. Financial analysis should combine quantitative and qualitative evidence, but only in a structured way.
**Code reference:** `src/agents/tasks.py`


### Q5. **How do you make prompt instructions specific enough to reduce hallucination?**
**Answer:** I make each agent responsible for a narrow kind of evidence, constrain the tools they can use, and explicitly ground the strategist in the quant output. Prompt scope is a big part of hallucination control.
**Code reference:** `src/agents/tasks.py`, `src/agents/agents.py`


### Q6. **How do you balance structured outputs with flexibility for the model?**
**Answer:** I prescribe what evidence must be considered, but I still leave room for natural reasoning in the final narrative. Over-constraining everything can make the report brittle.
**Code reference:** `src/agents/tasks.py`


### Q7. **Why is the final report written in Markdown?**
**Answer:** Markdown is readable in the UI, easy to store, easy to download, and works well as a durable report artifact for both humans and systems.
**Code reference:** `src/agents/tasks.py`


### Q8. **What would you change in the prompts if the outputs became too verbose?**
**Answer:** I would tighten expected-output instructions, add length limits, and possibly require more explicit section boundaries or bullet caps.
**Code reference:** `src/agents/tasks.py`


### Q9. **What would you change if the strategist kept over-weighting news over fundamentals?**
**Answer:** I would strengthen the prompt language about the quant summary being the primary grounding layer and require the recommendation to reference concrete metrics.
**Code reference:** `src/agents/tasks.py`


### Q10. **How do you think about prompt design differently when building a system rather than a one-off chat workflow?**
**Answer:** In a system, prompt design is about controlling handoffs, tool usage, failure behavior, and downstream consistency, not just about getting one nice answer once.
**Code reference:** `src/agents/tasks.py`, `src/agents/crew.py`


---

## 6. Tooling and Data Acquisition

[Back to Top](#table-of-contents)

### Q1. **Why did you choose yFinance for quantitative data?**
**Answer:** It is fast to integrate, gives good public-market coverage, and is sufficient for a portfolio project that needs real market data without a paid enterprise feed.
**Code reference:** `src/agents/tools/financial.py`


### Q2. **What are the limitations of using yFinance in a production-style system?**
**Answer:** It is not an institutional-grade data contract. The limitations are consistency, guarantees, and long-term reliability compared with stronger commercial providers.
**Code reference:** `src/agents/tools/financial.py`


### Q3. **Why did you choose Firecrawl for web research?**
**Answer:** I wanted the strategist to consume cleaned textual content rather than only snippet-level search results. Firecrawl is useful for getting readable evidence into the model.
**Code reference:** `src/agents/tools/scraper.py`


### Q4. **Why do you limit Firecrawl search results instead of pulling many articles?**
**Answer:** More articles often add more noise than value. Limiting the result set helps control latency and context size while still giving the strategist enough narrative evidence.
**Code reference:** `src/agents/tools/scraper.py`


### Q5. **Why do you serialize the fundamentals payload as JSON text for the agent?**
**Answer:** JSON text is a stable structured format for the agent to consume. It is more reliable than implicitly returning an in-memory Python object and hoping the framework handles it cleanly.
**Code reference:** `src/agents/tools/financial.py`


### Q6. **How did you decide which financial metrics to include in the fundamentals tool?**
**Answer:** I chose a compact set that gives a useful snapshot of valuation, size, profitability, volatility, and price context: price, market cap, P/E, EPS, beta, and 52-week range.
**Code reference:** `src/agents/tools/financial.py`


### Q7. **Why compare the target stock against SPY?**
**Answer:** SPY gives a simple market-relative benchmark. It helps the quant agent answer whether the stock outperformed or underperformed the broader market over the same period.
**Code reference:** `src/agents/tasks.py`, `src/agents/tools/financial.py`


### Q8. **What value does the one-year relative performance comparison add?**
**Answer:** It provides directional context without requiring a full analytics engine. It is a lightweight but useful measure of relative performance.
**Code reference:** `src/agents/tools/financial.py`


### Q9. **What are the risks of relying on third-party external APIs during analysis?**
**Answer:** They can be slow, incomplete, unavailable, or inconsistent. That is why error handling, retries, and fallback behavior matter so much in this kind of system.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


### Q10. **How would you harden the tool layer if this became customer-facing?**
**Answer:** I would add retries, timeouts, structured error payloads, caching, provider abstraction, and stronger validation of returned data before it reaches the agents.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


---

## 7. Missing Data, Tool Errors, and Fallback Behavior

[Back to Top](#table-of-contents)

### Q1. **What happens if Yahoo Finance returns missing metrics such as EPS or beta?**
**Answer:** The tool returns `N/A` for missing fields and still returns the rest of the payload. That allows the workflow to degrade gracefully instead of failing immediately.
**Code reference:** `src/agents/tools/financial.py`


### Q2. **What happens if the fundamental analysis tool fails entirely?**
**Answer:** The tool returns an explicit error string and the workflow continues with degraded context. That keeps the pipeline alive, although I would make this more structured in production.
**Code reference:** `src/agents/tools/financial.py`


### Q3. **Why did you choose to return tool-level error text rather than crash the entire crew immediately?**
**Answer:** I wanted the downstream agent to know that the upstream tool had a problem instead of only failing silently. The tradeoff is that this is less structured than an explicit error schema.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


### Q4. **How does the strategist behave when the quant output is incomplete?**
**Answer:** It still consumes whatever context the quant task produced. Today that behavior depends mostly on prompt quality; in production I would make confidence reduction more explicit.
**Code reference:** `src/agents/tasks.py`, `src/agents/crew.py`


### Q5. **How would you improve the current missing-data handling if you had more time?**
**Answer:** I would return structured fields like `available_metrics`, `missing_metrics`, `error_type`, and `confidence` instead of only `N/A` values or natural-language error text.
**Code reference:** `src/agents/tools/financial.py`


### Q6. **How do you distinguish between "metric unavailable" and "integration failure"?**
**Answer:** Conceptually, partial data means the metric is unavailable, while a hard failure means the integration failed. I would make that distinction explicit in the tool schema if I were hardening the system.
**Code reference:** `src/agents/tools/financial.py`


### Q7. **How would you prevent the strategist from making an overconfident recommendation when data quality is weak?**
**Answer:** I would require the final report to mention missing evidence and lower confidence when critical metrics are absent. Today that is mostly a prompt-level behavior rather than a hard rule.
**Code reference:** `src/agents/tasks.py`


### Q8. **How would you score confidence in the final recommendation?**
**Answer:** I would base it on data completeness, number of successful tool calls, agreement between quant and narrative signals, and the availability of critical metrics.
**Code reference:** `src/agents/tasks.py`


### Q9. **What additional validation would you add around ticker input and tool outputs?**
**Answer:** I would add ticker format validation, expected-schema validation for tool responses, and guardrails around empty or malformed data before agents consume it.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


### Q10. **If one external service is down, should the job fail, degrade gracefully, or retry? Why?**
**Answer:** It depends on the service and stage. Market-data gaps may justify graceful degradation, transient infra failures should retry, and persistence failures should fail loudly because false success is worse than visible failure.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/storage.py`


---

## 8. FastAPI, Async Execution, and API Responsiveness

[Back to Top](#table-of-contents)

### Q1. **Why is long-running CrewAI execution a poor fit for a single blocking HTTP request?**
**Answer:** It ties user experience directly to external latency and makes capacity management more fragile. It also creates timeout and concurrency problems for the API layer.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q2. **How did you redesign the API to stay responsive during long analyses?**
**Answer:** I made the API responsible only for job submission and status retrieval. The long-running analysis happens in the worker process.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q3. **Why does `POST /analyze` return `202 Accepted`?**
**Answer:** Because the request is accepted for processing but not yet complete. That is the correct contract for a durable long-running job.
**Code reference:** `src/api/routes.py`, `src/api/models.py`


### Q4. **What does the status endpoint return, and why is that useful for clients?**
**Answer:** It returns the job state, timestamps, worker ownership, final report content if complete, blob URL if available, and error information on failure. That gives the client a full picture of the lifecycle.
**Code reference:** `src/api/routes.py`, `src/api/models.py`


### Q5. **Why is polling acceptable here, and when would you switch to push-based updates?**
**Answer:** Polling is acceptable because the UI is simple and the frequency is low. If I needed richer real-time behavior or much larger scale, I would consider WebSockets, SSE, or event-driven notifications.
**Code reference:** `src/frontend/app.py`, `src/api/routes.py`


### Q6. **Why not use FastAPI `BackgroundTasks` for this workflow?**
**Answer:** Because the workload is too long-running and operationally significant. I wanted a durable worker execution model rather than an in-process helper mechanism.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q7. **What are the tradeoffs between threadpool offloading and a separate worker process?**
**Answer:** Threadpool offloading can help with sync calls, but it is not durable job execution. A separate worker process adds more moving parts but is much cleaner for multi-minute AI workflows.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q8. **How do you keep the event loop from being blocked by synchronous database work?**
**Answer:** I keep the API layer lightweight and use threadpool wrappers for synchronous DB access. The more important design choice is that the heavy analysis work is not running inside the API process.
**Code reference:** `src/api/routes.py`


### Q9. **What happens if the client disconnects right after submitting a job?**
**Answer:** The job still exists because it is stored durably in PostgreSQL. The lifecycle no longer depends on the client connection.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q10. **How would you support progress updates beyond just queued/running/completed/failed?**
**Answer:** I would add stage-level statuses such as `collecting_metrics`, `researching_news`, `writing_report`, and `persisting_artifacts`.
**Code reference:** `src/api/models.py`, `src/shared/database.py`


### Q11. **How would you add authentication and rate limiting to this API?**
**Answer:** I would add auth at the API boundary, per-user authorization on job access, request quotas, and rate limiting. I would be explicit in interviews that this repo does not implement those controls yet.
**Code reference:** `src/api/routes.py`


### Q12. **How would you expose this safely to multiple tenants?**
**Answer:** I would add tenant identity, access scoping on job reads, tenant-aware storage layout, quotas, and stricter isolation of metadata and artifacts.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


---

## 9. Durable Jobs, Worker Coordination, and Recovery

[Back to Top](#table-of-contents)

### Q1. **What job states does the system support, and why those states?**
**Answer:** The system supports `queued`, `running`, `completed`, and `failed`. That is enough to make the lifecycle clear without overcomplicating the state machine.
**Code reference:** `src/shared/database.py`, `src/api/models.py`


### Q2. **How does a worker claim the next job safely?**
**Answer:** It uses a locking query with `skip_locked`, selects the next queued job, marks it `running`, and attaches a `worker_id`. That prevents duplicate claims under normal operation.
**Code reference:** `src/shared/database.py`


### Q3. **Why did you use the database as a durable queue instead of an in-memory structure?**
**Answer:** For this scale, it was the simplest correct mechanism. It kept job state, history, and queue semantics in one place without adding another infrastructure dependency.
**Code reference:** `src/shared/database.py`


### Q4. **What is the purpose of worker heartbeats?**
**Answer:** Worker heartbeats prove that at least one execution process is alive recently enough for the API to accept new work.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q5. **What is the purpose of job heartbeats?**
**Answer:** Job heartbeats prove that a specific running job is still making progress. That supports lease-based recovery if the worker disappears.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q6. **How do stale-job recovery and re-queueing work?**
**Answer:** The system scans for `running` jobs whose heartbeat is too old and moves them back to `queued`. Another worker can then claim them later.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q7. **What problem does stale-job recovery solve?**
**Answer:** It solves the orphaned-job problem. Without it, a worker crash could leave a job stuck in `running` forever.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q8. **What happens if a worker crashes during report generation?**
**Answer:** The job eventually becomes stale and is re-queued. That gives the system a recovery path instead of leaving the job permanently stuck.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q9. **What happens if a worker crashes after Blob upload but before job completion?**
**Answer:** There is a risk of artifact duplication or partial completion. I reduced the database inconsistency risk by making the report-log write and job-completion update atomic, but Blob remains an external side effect, so stronger idempotency would still be needed for a hardened version.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q10. **Why is atomic job finalization important?**
**Answer:** It reduces cases where the report log and job status disagree. The database should not say one thing while the report record says another.
**Code reference:** `src/shared/database.py`


### Q11. **How did you reduce inconsistent outcomes between artifact persistence and job state?**
**Answer:** I combined report-log persistence and job completion into one database transaction. That gives much stronger consistency on the database side.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q12. **What duplication risks still exist in this design?**
**Answer:** Blob uploads can still duplicate if a job is retried after partial success. That is where idempotent artifact naming or deduplication logic would help.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/storage.py`


### Q13. **How would you make retries idempotent?**
**Answer:** I would use stable artifact identifiers per job, check whether output already exists, and record enough metadata to detect partial prior completion.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q14. **What happens if there are no active workers and the API receives a job submission?**
**Answer:** The API returns `503` instead of accepting work it cannot process. That was an intentional correctness improvement.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q15. **Why does the health endpoint report `healthy`, `degraded`, or `unhealthy`?**
**Answer:** It distinguishes between full service availability, degraded operation caused by missing workers, and true unhealthy states like database access failure.
**Code reference:** `src/api/main.py`, `src/shared/database.py`


### Q16. **What would you monitor in production for worker health?**
**Answer:** I would monitor worker heartbeat recency, queue depth, oldest queued job age, running job count, stale-job recovery count, completion rate, failure rate, and average job duration.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q17. **What are the limits of using PostgreSQL as a queue?**
**Answer:** The limits are polling overhead, contention at higher concurrency, and weaker native retry and dead-letter semantics than a real broker. It is fine here, but not the final answer at larger scale.
**Code reference:** `src/shared/database.py`


### Q18. **At what point would you move to a real message broker such as Azure Service Bus?**
**Answer:** I would move when throughput, retry control, delayed retries, multi-service consumption, or operational scale justify a dedicated broker.
**Code reference:** `src/shared/database.py`


---

## 10. Database Design and Persistence

[Back to Top](#table-of-contents)

### Q1. **What tables are used in this project, and what does each one represent?**
**Answer:** The main tables are `analysis_jobs`, `reports_log`, and `worker_heartbeats`. They store job lifecycle, report history, and worker liveness respectively.
**Code reference:** `src/shared/database.py`


### Q2. **Why does the system store both a `reports_log` entry and an `analysis_jobs` record?**
**Answer:** The job row supports operational polling and status, while the report log acts as a historical record of completed outputs. They serve different concerns.
**Code reference:** `src/shared/database.py`


### Q3. **Which fields are most important in the `analysis_jobs` table?**
**Answer:** The important fields are `id`, `ticker`, `status`, `worker_id`, `report_content`, `report_url`, `error_message`, and the lifecycle timestamps. Those fields make each job inspectable end to end.
**Code reference:** `src/shared/database.py`


### Q4. **Why do you store timestamps such as `created_at`, `started_at`, and `completed_at`?**
**Answer:** They let me reason about queue delay, processing time, and operational performance. They are basic observability data.
**Code reference:** `src/shared/database.py`


### Q5. **How does the database schema support operational debugging?**
**Answer:** You can inspect where a job stalled, whether it was claimed, which worker took it, and whether it failed before or after artifact persistence.
**Code reference:** `src/shared/database.py`


### Q6. **Why is `worker_id` stored on the job record?**
**Answer:** It helps attribute running work to a specific worker and makes ownership and failure scenarios easier to diagnose.
**Code reference:** `src/shared/database.py`


### Q7. **What data would you index first if job volume increased significantly?**
**Answer:** I would prioritize indexes on `status`, `created_at`, possibly `updated_at`, and any fields used by queue scans or dashboards.
**Code reference:** `src/shared/database.py`


### Q8. **What consistency guarantees does the current SQLAlchemy flow provide?**
**Answer:** It gives transactional guarantees for multi-step database updates within a single session and commit. It does not make external side effects such as Blob uploads transactional.
**Code reference:** `src/shared/database.py`


### Q9. **What would you change if report payloads became much larger?**
**Answer:** I would likely store less duplicated content in the job table and rely more on Blob Storage plus metadata pointers to reduce database bloat.
**Code reference:** `src/shared/database.py`, `src/shared/storage.py`


### Q10. **Would you ever stop storing full report content in Postgres? Why or why not?**
**Answer:** Possibly, if report volume or size grew enough to make that inefficient. For this project it is still useful because the API can return the report directly without an extra fetch step.
**Code reference:** `src/shared/database.py`, `src/shared/storage.py`


---

## 11. Azure Blob Storage Integration

[Back to Top](#table-of-contents)

### Q1. **Why did you choose Azure Blob Storage for report archiving?**
**Answer:** It is a natural fit for durable report files and aligns well with the Azure-oriented architecture in the project.
**Code reference:** `src/shared/storage.py`


### Q2. **How does the application connect to Blob Storage?**
**Answer:** It uses the Azure Blob Python SDK with a connection string loaded from configuration. The storage service initializes the client and ensures the `reports` container exists.
**Code reference:** `src/shared/storage.py`, `src/shared/config.py`


### Q3. **What does the upload path look like in the worker flow?**
**Answer:** The crew writes `investment_report_<TICKER>.md` locally, the worker uploads that file to Blob Storage, and then the blob URL is written back to the job result.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/storage.py`


### Q4. **Why is the worker responsible for uploading the report instead of the API?**
**Answer:** The worker owns the long-running pipeline and knows whether report generation actually succeeded. The API should remain lightweight.
**Code reference:** `src/workers/analysis_worker.py`


### Q5. **What is the purpose of the dedicated `reports` container?**
**Answer:** It gives a clean logical home for generated report artifacts. It is a simple but useful storage boundary.
**Code reference:** `src/shared/storage.py`


### Q6. **Why is the report stored as a file artifact and not just returned inline forever?**
**Answer:** Storing it as an artifact preserves it beyond process lifetime and allows later retrieval independent of the immediate API response.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/storage.py`


### Q7. **What happens if the local report file is missing at upload time?**
**Answer:** The storage layer raises a `FileNotFoundError`, which causes the job to fail rather than pretending the upload succeeded.
**Code reference:** `src/shared/storage.py`


### Q8. **How does the code handle Blob upload errors?**
**Answer:** Blob upload errors are raised explicitly as exceptions. That was a deliberate fix because silent or misleading behavior would make the system untrustworthy.
**Code reference:** `src/shared/storage.py`


### Q9. **How would you improve blob naming conventions for large-scale usage?**
**Answer:** I would add job IDs, timestamps, tenant or environment prefixes, and possibly version suffixes. That would improve uniqueness, organization, and idempotency.
**Code reference:** `src/shared/storage.py`


### Q10. **How would you handle versioning if the same ticker is analyzed many times?**
**Answer:** I would version by job ID or timestamp rather than overwriting by ticker name alone. That preserves history and reduces accidental collisions.
**Code reference:** `src/shared/storage.py`, `src/shared/database.py`


---

## 12. Azure Blob Security Questions

[Back to Top](#table-of-contents)

### Q1. **What Blob Storage security measures are implemented in the code today?**
**Answer:** The implemented measures are basic: secrets are not hardcoded, the storage layer is isolated behind configuration and a service class, and upload failures are handled explicitly. The repo does not yet implement advanced Azure-native security controls by itself.
**Code reference:** `src/shared/storage.py`, `src/shared/config.py`


### Q2. **What security risks come with using connection strings in environment variables?**
**Answer:** Connection strings are powerful shared secrets. If they leak through logs, CI output, or a compromised machine, an attacker may gain broad storage access.
**Code reference:** `src/shared/config.py`


### Q3. **If the reports contain sensitive financial analysis, what Azure controls would you add in production?**
**Answer:** I would add private containers, managed identity, RBAC, Key Vault, private endpoints, audit logging, and controlled retrieval paths instead of direct public access.
**Code reference:** `src/shared/storage.py`, `src/shared/config.py`


### Q4. **Would you keep the blob container public or private? Why?**
**Answer:** Private. AI-generated reports are usually internal artifacts, not public web assets.
**Code reference:** `src/shared/storage.py`


### Q5. **When would you use SAS tokens versus service-side retrieval through the API?**
**Answer:** I would use SAS only when a client truly needs short-lived direct object access. Otherwise I would prefer service-side retrieval through the API so access control stays centralized.
**Code reference:** `src/shared/storage.py`


### Q6. **When would you use Azure RBAC and managed identity?**
**Answer:** When the service runs inside Azure and can authenticate without long-lived secrets. That is the cleaner production pattern.
**Code reference:** `src/shared/config.py`


### Q7. **How would you avoid exposing raw blob URLs directly to end users?**
**Answer:** I would authorize the caller in the API and either proxy the download or mint a short-lived signed URL only when necessary.
**Code reference:** `src/shared/storage.py`, `src/api/routes.py`


### Q8. **How would you handle secret rotation for Blob access?**
**Answer:** I would store secrets in Key Vault, minimize credential scope, and design the service to reload or redeploy safely when rotated.
**Code reference:** `src/shared/config.py`


### Q9. **Would you enable encryption at rest only, or also customer-managed keys? Why?**
**Answer:** Encryption at rest is the baseline. I would consider customer-managed keys if compliance or enterprise key-control requirements justified the added complexity.
**Code reference:** `src/shared/storage.py`


### Q10. **How would private endpoints improve the security posture?**
**Answer:** They remove public network exposure and keep traffic inside the virtual network boundary.
**Code reference:** `src/shared/config.py`


### Q11. **How would you design secure report access for multiple internal teams?**
**Answer:** I would separate access by identity and role and possibly by storage path or account depending on sensitivity and tenancy needs.
**Code reference:** `src/shared/storage.py`


### Q12. **What audit logging would you want around report access?**
**Answer:** I would want logs showing who accessed which artifact, when, and from where. That is important for auditability and incident review.
**Code reference:** `src/shared/storage.py`


### Q13. **How would lifecycle policies help with retention and cost management?**
**Answer:** They help move old artifacts to cheaper tiers, enforce retention windows, and manage storage costs as report volume grows.
**Code reference:** `src/shared/storage.py`


### Q14. **What would you change if compliance required stricter controls around generated reports?**
**Answer:** I would tighten access paths, reduce direct blob exposure, add stronger encryption and key management controls, and formalize retention and audit processes.
**Code reference:** `src/shared/storage.py`, `src/shared/config.py`


---

## 13. Secrets, Security, and Compliance

[Back to Top](#table-of-contents)

### Q1. **How are secrets managed in this project today?**
**Answer:** Secrets are managed through environment variables and loaded via Pydantic settings. That is fine for local development but not the full production answer.
**Code reference:** `src/shared/config.py`


### Q2. **Why is `.env` acceptable for local development but not enough for enterprise production?**
**Answer:** It is simple and developer-friendly for local work, but it depends on host-level secrecy and manual distribution. Enterprise production needs stronger secret storage and access control.
**Code reference:** `src/shared/config.py`


### Q3. **What would you move into Azure Key Vault in a production deployment?**
**Answer:** I would move OpenAI, Firecrawl, Blob Storage, and Postgres secrets there, or replace some of them with managed identity where possible.
**Code reference:** `src/shared/config.py`


### Q4. **How would you separate dev, test, and prod credentials?**
**Answer:** I would use environment-specific secret stores, separate cloud resources, and strict non-reuse of credentials across environments.
**Code reference:** `src/shared/config.py`


### Q5. **What is your threat model for this system?**
**Answer:** I would focus on secret leakage, unauthorized access to generated reports, API abuse, data exfiltration from cloud storage, and misuse of the AI workflow itself.
**Code reference:** `src/shared/config.py`, `src/api/routes.py`


### Q6. **What data in this project is sensitive, and what is not?**
**Answer:** The stock ticker itself is not sensitive, but generated report content, cloud credentials, and operational metadata can be. If the reports are internal research, they should be treated as sensitive artifacts.
**Code reference:** `src/shared/database.py`, `src/shared/storage.py`


### Q7. **How would you sanitize or redact logs to avoid leaking secrets or analysis content?**
**Answer:** I would avoid logging raw secrets, minimize full report dumps, and keep error messages explicit enough for debugging without exposing sensitive values.
**Code reference:** `src/workers/analysis_worker.py`, `src/api/routes.py`


### Q8. **How would you secure outbound access to OpenAI, Firecrawl, Postgres, and Blob in production?**
**Answer:** I would use managed identity where possible, controlled secret management, network restrictions, and tighter egress controls in the Azure deployment.
**Code reference:** `src/shared/config.py`, `src/shared/storage.py`


### Q9. **What network-level controls would you add if this ran inside Azure?**
**Answer:** I would add private endpoints, VNet integration, NSGs, and routing of sensitive service traffic over private rather than public paths.
**Code reference:** `src/shared/config.py`


### Q10. **How would you think about compliance if the analysis were used in a regulated setting?**
**Answer:** I would add stronger access controls, auditability, retention rules, model governance, and likely a human review step before any recommendation is treated as decision-support output.
**Code reference:** `src/shared/config.py`


---

## 14. Model Choice, LLM Behavior, and Cost Control

[Back to Top](#table-of-contents)

### Q1. **Why did you make the model name environment-configurable?**
**Answer:** Model selection affects cost, latency, and output quality, so it belongs in runtime configuration rather than being hardcoded inside the agent factory.
**Code reference:** `src/shared/config.py`, `src/agents/agents.py`


### Q2. **How would model selection affect latency, quality, and cost?**
**Answer:** A stronger model usually improves synthesis quality but increases latency and cost. A lighter model lowers cost and latency but may weaken reasoning quality across mixed evidence.
**Code reference:** `src/shared/config.py`, `src/agents/agents.py`


### Q3. **What parts of this workflow are deterministic and what parts are model-driven?**
**Answer:** Queue handling, persistence, heartbeats, and tool invocation plumbing are deterministic. Summarization, synthesis, and the final narrative recommendation are model-driven.
**Code reference:** `src/agents/agents.py`, `src/agents/tools/financial.py`


### Q4. **How do you think about hallucination risk in a recommendation system like this?**
**Answer:** It is real because the final recommendation is still LLM-generated. I reduce it by grounding agents in tools and structured handoffs, but I would not claim the system eliminates hallucination.
**Code reference:** `src/agents/tasks.py`, `src/agents/tools/financial.py`


### Q5. **How would you reduce hallucinations without making the output too rigid?**
**Answer:** I would add source citations, structured evidence fields, confidence scoring, and possibly schema validation around the final recommendation.
**Code reference:** `src/agents/tasks.py`, `src/agents/agents.py`


### Q6. **When would you add structured output validation on the final recommendation?**
**Answer:** Once downstream consumers needed reliable machine-readable results or stronger guardrails around recommendation format.
**Code reference:** `src/agents/tasks.py`


### Q7. **How would you measure whether the strategist is making grounded decisions?**
**Answer:** I would check whether the final report refers back to actual metrics and retrieved news rather than drifting into generic market language.
**Code reference:** `src/agents/tasks.py`, `src/agents/tools/scraper.py`


### Q8. **Would you use the same model for both agents in a production setting? Why or why not?**
**Answer:** Today I use the same configured model for simplicity and consistent behavior. In production I might split models if the cost-quality tradeoff justified it.
**Code reference:** `src/agents/agents.py`, `src/shared/config.py`


### Q9. **Where would you consider caching to reduce cost?**
**Answer:** I would consider caching stable market data lookups, repeated benchmark data like SPY within a short window, and some research results when freshness requirements allow it.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


### Q10. **How would you benchmark one model against another for this use case?**
**Answer:** I would compare latency, token cost, factual grounding, consistency of verdicts, and human review of report usefulness across a representative ticker set.
**Code reference:** `src/shared/config.py`, `src/agents/agents.py`


---

## 15. Deployment Tradeoffs: Azure Functions vs VM vs Containers

[Back to Top](#table-of-contents)

### Q1. **Why is Azure Functions not always ideal for long-running agent workflows?**
**Answer:** Because long-running AI workflows suffer from cold starts, timeout pressure, and less control over always-on execution. That makes Functions a weaker fit for multi-minute jobs.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q2. **What are the main tradeoffs between Azure Functions and a dedicated worker on a VM?**
**Answer:** Functions reduces idle cost and infrastructure overhead, while a dedicated worker gives better control, easier debugging, and a cleaner fit for long-running execution.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q3. **How do cost models differ between Functions and always-on compute?**
**Answer:** Functions is usually cheaper at low and bursty volume, while always-on compute costs more steadily but avoids paying with unpredictability and cold-start friction.
**Code reference:** `src/workers/analysis_worker.py`


### Q4. **How do cold starts affect AI workflows with multiple external dependencies?**
**Answer:** They add startup delay on top of already variable external latency, which hurts the user experience and makes runtime less predictable.
**Code reference:** `src/workers/analysis_worker.py`


### Q5. **How do timeout limits influence the design?**
**Answer:** Heavily. If the platform cannot reliably hold the workload long enough, it is the wrong execution model for the job.
**Code reference:** `src/workers/analysis_worker.py`


### Q6. **What are the maintenance tradeoffs of a VM-based worker?**
**Answer:** A VM gives more control, but it also increases patching, monitoring, and infrastructure maintenance responsibility.
**Code reference:** `src/workers/analysis_worker.py`


### Q7. **When would Azure Container Apps be a better fit than either Functions or a raw VM?**
**Answer:** When I want containerized API and worker services, autoscaling, and less raw infrastructure management than a VM while still supporting long-running workers better than Functions.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q8. **If this had bursty traffic, how would your deployment choice change?**
**Answer:** I would lean more toward autoscaled containers or broker-driven worker pools instead of a single always-on worker.
**Code reference:** `src/workers/analysis_worker.py`


### Q9. **If this needed predictable low latency, how would your deployment choice change?**
**Answer:** I would keep warm workers and avoid platforms with cold-start behavior that adds variability.
**Code reference:** `src/workers/analysis_worker.py`


### Q10. **If this became a team-managed platform, what hosting model would you recommend and why?**
**Answer:** I would likely recommend containerized API and worker services plus a proper message broker. That balances control and operability better than either Functions-only or a manually managed VM.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


---

## 16. Reliability, Observability, and Operations

[Back to Top](#table-of-contents)

### Q1. **What are the top operational failure modes in this project?**
**Answer:** External API failure, worker crashes, missing workers, stale jobs, Blob upload failure, database write failure, and weak or incomplete upstream data.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q2. **What does the current health endpoint tell you, and what does it not tell you?**
**Answer:** It tells me whether the API can talk to the database and whether at least one worker is heartbeating. It does not tell me anything about output quality or whether external dependencies are degraded.
**Code reference:** `src/api/main.py`


### Q3. **What metrics would you put on a dashboard?**
**Answer:** Queue depth, oldest queued job age, running job count, completion rate, failure rate, average duration, stale recovery count, and worker heartbeat recency.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q4. **What alerts would you set up first?**
**Answer:** No active workers, high failure rate, oldest queued job age over threshold, repeated stale-job recoveries, and persistence failures.
**Code reference:** `src/api/main.py`, `src/workers/analysis_worker.py`


### Q5. **How would you trace a failed job across API, worker, database, and blob storage?**
**Answer:** I would follow the `job_id` through API logs, worker logs, job table state, and Blob persistence outcomes. The durable job table is especially useful because it captures status and timestamps.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q6. **Why did you remove LangSmith/LangChain tracing from this repo?**
**Answer:** I did not want the repo coupled to that tracing path and wanted to simplify configuration. The current system relies on simpler logs and durable job state instead.
**Code reference:** `src/agents/crew.py`, `src/shared/config.py`


### Q7. **Without LangSmith, how would you improve observability for agent execution?**
**Answer:** I would add structured logs, per-stage status updates, metrics, correlation IDs, and possibly OpenTelemetry later if I needed deeper distributed tracing.
**Code reference:** `src/api/main.py`, `src/workers/analysis_worker.py`


### Q8. **What logs are most useful when debugging a failed analysis?**
**Answer:** Job submission, job claim, heartbeat failures, tool failures, Blob upload failures, database finalization failures, and explicit completion or failure logs with `job_id`.
**Code reference:** `src/workers/analysis_worker.py`, `src/api/routes.py`


### Q9. **How would you measure average job duration and failure rate?**
**Answer:** I would measure them from job timestamps in PostgreSQL plus worker-side metrics and logs.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q10. **How would you detect a worker that is alive but unhealthy?**
**Answer:** A worker can still heartbeat while repeatedly failing jobs or making no progress. That is why I would monitor throughput and failure patterns in addition to liveness.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q11. **How would you investigate reports of duplicate job execution?**
**Answer:** I would inspect stale-job timing, heartbeat recency, claim logs, and whether a job was re-queued while the original worker was slow instead of actually dead.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q12. **What would you add to support auditability?**
**Answer:** Stronger event logs, user attribution, access logs for report retrieval, and more explicit stage transitions in the job lifecycle.
**Code reference:** `src/shared/database.py`, `src/api/routes.py`


---

## 17. Performance and Scalability

[Back to Top](#table-of-contents)

### Q1. **What are the main latency drivers in this system?**
**Answer:** OpenAI inference, Firecrawl retrieval, and market-data fetches. The queue layer is not usually the first latency source at this scale.
**Code reference:** `src/agents/crew.py`, `src/agents/tools/scraper.py`


### Q2. **Which external dependency is most likely to become the bottleneck?**
**Answer:** Firecrawl and model inference are the most likely bottlenecks because both are external and can vary significantly in latency.
**Code reference:** `src/agents/tools/scraper.py`, `src/agents/crew.py`


### Q3. **What happens if ten users submit jobs at the same time?**
**Answer:** The jobs queue in PostgreSQL and are processed by available workers. Throughput then depends on how many workers are running and how long each analysis takes.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q4. **How would the current Postgres-backed queue behave under heavier load?**
**Answer:** It would still work, but eventually it would show more polling overhead and contention than a dedicated broker-backed system.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q5. **What are the first scaling limits of the current design?**
**Answer:** External API latency, sequential workflow time, and queue architecture. Those will hurt earlier than raw CPU in many cases.
**Code reference:** `src/shared/database.py`, `src/agents/crew.py`


### Q6. **How would you scale worker throughput horizontally?**
**Answer:** I would run multiple worker instances that all claim from the same durable queue.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q7. **What work would you parallelize, and what work should stay sequential?**
**Answer:** I would keep the quant-to-strategist dependency sequential, but I might parallelize independent data acquisition steps inside the workflow if they did not compromise clarity.
**Code reference:** `src/agents/crew.py`, `src/agents/tasks.py`


### Q8. **How would you improve report generation time without hurting quality?**
**Answer:** I would optimize prompts, reduce unnecessary context, cache stable tool results, and evaluate whether both agents need the same model size.
**Code reference:** `src/agents/tasks.py`, `src/agents/tools/scraper.py`


### Q9. **Where could you cache safely in this workflow?**
**Answer:** Stable market data lookups, repeated SPY benchmark data within a short window, and some research results when freshness requirements allow it.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


### Q10. **What architecture changes would you make for much higher scale?**
**Answer:** I would move toward a broker-backed queue, containerized worker autoscaling, stronger caching, and more formal observability and rate control.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


---

## 18. Testing Strategy

[Back to Top](#table-of-contents)

### Q1. **How would you unit test the financial tools?**
**Answer:** I would mock yFinance responses and verify that the tool returns the expected metrics, handles missing fields correctly, and surfaces errors properly.
**Code reference:** `src/agents/tools/financial.py`


### Q2. **How would you test the worker loop without calling real external APIs?**
**Answer:** I would mock the crew execution, storage service, and database calls so I could validate state transitions without real network dependency.
**Code reference:** `src/workers/analysis_worker.py`


### Q3. **What integration tests would you prioritize first?**
**Answer:** Job submission, worker claim behavior, successful completion, failure handling, and stale-job requeue behavior.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q4. **How would you test stale-job recovery?**
**Answer:** I would create a running job with an old heartbeat timestamp, run the recovery logic, and assert that it moves back to `queued`.
**Code reference:** `src/shared/database.py`


### Q5. **How would you test the API contract for queued, running, completed, and failed jobs?**
**Answer:** I would create jobs in each state and assert that the status endpoint serializes the expected fields correctly for each one.
**Code reference:** `src/api/routes.py`, `src/api/models.py`


### Q6. **How would you test Blob upload failures safely?**
**Answer:** I would stub the storage client to raise an error and then verify that the worker marks the job as failed.
**Code reference:** `src/shared/storage.py`, `src/workers/analysis_worker.py`


### Q7. **How would you test database transaction behavior around job completion?**
**Answer:** I would force a failure during finalization and assert that the database rolls back partial state correctly.
**Code reference:** `src/shared/database.py`


### Q8. **What should be mocked and what should be run against real services?**
**Answer:** Unit and most integration tests should mock external AI and data services. I would keep a smaller set of controlled end-to-end tests against real services in a non-production environment.
**Code reference:** `src/agents/tools/financial.py`, `src/workers/analysis_worker.py`


### Q9. **How would you structure end-to-end tests for this system?**
**Answer:** Submit a ticker, wait for the worker to process it, verify the final job state, and assert that both the report artifact and metadata exist.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q10. **What gaps exist in the current repo's testing story?**
**Answer:** The main gap is that the repo does not yet include a real automated test suite. I would be honest about that and explain how I would add coverage.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


---

## 19. Tradeoffs, Limitations, and Honest Self-Critique

[Back to Top](#table-of-contents)

### Q1. **What is the weakest part of the current design?**
**Answer:** The weakest part is that it still relies on a Postgres-backed queue and relatively light observability. It is strong for a portfolio project, but not the final architecture at higher scale.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q2. **What is intentionally simplified in this repository?**
**Answer:** Authentication, authorization, enterprise observability, formal evaluation, and some Azure security hardening are intentionally simplified.
**Code reference:** `src/api/routes.py`, `src/shared/config.py`


### Q3. **What security features would you add before calling this enterprise-ready?**
**Answer:** Auth, managed identity, Key Vault, private network paths, stronger access control on artifacts, and better audit logging.
**Code reference:** `src/shared/config.py`, `src/shared/storage.py`


### Q4. **What would you replace first if the system had to support heavy traffic?**
**Answer:** The queue backbone. That is the main scaling pressure point.
**Code reference:** `src/shared/database.py`


### Q5. **What would you improve in the agent prompts?**
**Answer:** I would improve citation behavior, confidence disclosure, and more explicit linkage between evidence and final verdict.
**Code reference:** `src/agents/tasks.py`


### Q6. **What would you improve in the data quality layer?**
**Answer:** Stronger validation, retries, provider abstraction, and structured completeness and confidence indicators.
**Code reference:** `src/agents/tools/financial.py`, `src/agents/tools/scraper.py`


### Q7. **What would you improve in the persistence model?**
**Answer:** I would think harder about idempotent artifact handling and whether the job table should continue storing full report content long-term.
**Code reference:** `src/shared/database.py`, `src/shared/storage.py`


### Q8. **What would you improve in the user experience?**
**Answer:** Richer progress stages, better failure messaging, and possibly side-by-side evidence views for metrics and retrieved news.
**Code reference:** `src/frontend/app.py`, `src/api/routes.py`


### Q9. **What technical debt are you aware of in the current codebase?**
**Answer:** Mostly around evaluation, security hardening, observability, and queue maturity. The service boundaries themselves are in a good place.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q10. **If you had one more week on this project, what would you ship next?**
**Answer:** I would focus on formal evaluation, auth and cloud-secret hardening, and stronger queue semantics or idempotency.
**Code reference:** `src/shared/config.py`, `src/shared/database.py`


---

## 20. Behavioral and Ownership Questions

[Back to Top](#table-of-contents)

### Q1. **What was the hardest engineering problem in this project?**
**Answer:** Moving from a blocking AI demo to a reliable background workflow. That required thinking about job boundaries, worker ownership, persistence, and failure handling together.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q2. **What bug or design flaw did you discover and fix that materially improved the system?**
**Answer:** The biggest one was the original blocking API design. Refactoring it into durable jobs plus a worker process made the architecture much more defensible.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q3. **Describe a time when you changed the architecture after realizing the first version was not good enough.**
**Answer:** The first version ran the whole analysis inside the request lifecycle. Once it became clear that long-running AI work did not belong there, I changed it to a job-and-worker model with explicit state and recovery.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q4. **How did you decide what was worth hardening and what was not?**
**Answer:** I hardened correctness and operability first: job execution, persistence truthfulness, worker recovery, and configuration behavior. I deprioritized improvements that did not change functional reliability.
**Code reference:** `src/shared/database.py`, `src/shared/storage.py`


### Q5. **How did you balance speed of delivery against production correctness?**
**Answer:** I built the simplest working version first, then hardened the highest-risk failure modes in priority order. That let me move quickly without pretending the first version was production-ready.
**Code reference:** `src/api/routes.py`, `src/shared/database.py`


### Q6. **What part of this project best demonstrates senior-level thinking?**
**Answer:** Treating AI work as distributed work with explicit state instead of as a long function call behind an endpoint. That is the biggest system-design signal in the project.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q7. **If a hiring manager asked what you are most proud of here, what would you say?**
**Answer:** I would say I am most proud that the repo now tells a coherent systems story. It is not just "I used CrewAI"; it is "I designed how long-running AI work should behave in a service."
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q8. **If a teammate challenged your choice of Postgres-backed jobs, how would you defend it?**
**Answer:** I would say it was a deliberate tradeoff for this scale: fewer dependencies, simpler state model, faster implementation, and good-enough semantics for the current stage.
**Code reference:** `src/shared/database.py`


### Q9. **If a principal engineer asked what you would redesign next, what would you say?**
**Answer:** Broker-backed queuing, stronger auth and cloud security, and more formal evaluation and confidence controls.
**Code reference:** `src/shared/database.py`, `src/shared/config.py`


### Q10. **What did this project teach you about building agentic systems beyond just calling an LLM?**
**Answer:** It taught me that once you care about reliability, recovery, persistence, and operational correctness, agentic systems become real systems engineering work rather than prompt experiments.
**Code reference:** `src/agents/crew.py`, `src/workers/analysis_worker.py`


---

## 21. Good Follow-Up Questions You Should Expect

[Back to Top](#table-of-contents)

### Q1. **Can you explain that design choice with an example failure scenario?**
**Answer:** Yes. For example, if a worker dies mid-job, heartbeats stop, the job lease expires, and the system re-queues the work instead of leaving it stuck in `running` forever. That is the kind of concrete failure mode I was designing for.
**Code reference:** `src/workers/analysis_worker.py`, `src/shared/database.py`


### Q2. **What tradeoff did you accept by choosing that approach?**
**Answer:** I accepted more moving parts in exchange for better correctness, recoverability, and clearer service boundaries.
**Code reference:** `src/api/routes.py`, `src/workers/analysis_worker.py`


### Q3. **What would break first if traffic increased 10x?**
**Answer:** External API latency and the Postgres-backed queue would be the first stress points. Those would show pressure before many other parts of the system.
**Code reference:** `src/shared/database.py`, `src/workers/analysis_worker.py`


### Q4. **How would you monitor that in production?**
**Answer:** Queue depth, oldest queued job age, worker heartbeat recency, failure rate, p95 job duration, and external dependency errors.
**Code reference:** `src/api/main.py`, `src/shared/database.py`


### Q5. **What is implemented now versus what you are describing as future-state architecture?**
**Answer:** Implemented now: durable jobs, worker heartbeats, stale-job recovery, cloud persistence separation, and multi-agent orchestration. Future-state hardening: auth, Key Vault, managed identity, broker-backed queue, stronger evaluation, and deeper observability.
**Code reference:** `src/api/routes.py`, `src/shared/config.py`


### Q6. **How would you explain this system to a non-technical stakeholder?**
**Answer:** I would say it uses specialized AI roles to gather financial facts, read recent market context, and then produce a research memo automatically while storing the result safely for review.
**Code reference:** `src/frontend/app.py`, `src/api/routes.py`


### Q7. **How would you justify the cloud cost of this design?**
**Answer:** It avoids blocking expensive web workers, stores artifacts in the right storage layer, and lets compute scale at the worker boundary instead of overloading the API layer. That is a better cost-performance shape than a naive synchronous design.
**Code reference:** `src/api/routes.py`, `src/shared/storage.py`


### Q8. **How would you make the recommendation more trustworthy?**
**Answer:** Add citations, confidence scoring, clearer evidence sections, and possibly a human review step for low-confidence outputs.
**Code reference:** `src/agents/tasks.py`, `src/agents/tools/financial.py`


### Q9. **How would you secure it if external users could upload arbitrary tickers at high volume?**
**Answer:** I would add auth, rate limits, quotas, abuse monitoring, and input validation before exposing it broadly.
**Code reference:** `src/api/routes.py`, `src/shared/config.py`


### Q10. **If this were going into production next month, what are the three must-do hardening tasks?**
**Answer:** Security and identity, observability and testing, and stronger queue or idempotency semantics.
**Code reference:** `src/shared/config.py`, `src/shared/database.py`


---

## 22. Questions You Should Be Ready to Ask the Interviewer

[Back to Top](#table-of-contents)

### Q1. **How mature is your current AI platform stack: prototype, pilot, or production?**
**Answer:** Ask this to understand whether they need someone who can prototype quickly or someone who can harden systems already in production. It tells you what maturity level they operate at.
**Code reference:** No direct single code file. This item is mainly interview strategy rather than implemented repo logic.


### Q2. **How does your team currently handle long-running AI workflows operationally?**
**Answer:** Ask this to learn whether they already use queues, workers, or orchestration frameworks for AI workloads. It reveals how mature their AI operations are.
**Code reference:** No direct single code file. This item is mainly interview strategy rather than implemented repo logic.


### Q3. **What is the biggest pain point today: latency, cost, quality, observability, or reliability?**
**Answer:** Ask this so you know where the team is hurting most. That helps you position your strengths against their real needs.
**Code reference:** No direct single code file. This item is mainly interview strategy rather than implemented repo logic.


### Q4. **Do your AI workloads run inside request-response paths, background workers, or both?**
**Answer:** Ask this because it shows you understand that AI workloads do not all belong in request-response flows. Their answer reveals architectural maturity.
**Code reference:** No direct single code file. This item is mainly interview strategy rather than implemented repo logic.


### Q5. **How does your team think about evaluation and grounding for multi-step agent workflows?**
**Answer:** Ask this to understand whether they treat evaluation as a first-class system concern or still optimize prompts ad hoc.
**Code reference:** No direct single code file. This item is mainly interview strategy rather than implemented repo logic.


### Q6. **How do you currently secure generated artifacts and intermediate data?**
**Answer:** Ask this because generated artifacts are often overlooked security surfaces in AI systems. It signals that you think beyond the model call.
**Code reference:** No direct single code file. This item is mainly interview strategy rather than implemented repo logic.


### Q7. **Are you more interested in model innovation or productionizing known patterns reliably?**
**Answer:** Ask this to understand whether the role leans more research-heavy or systems-heavy. That helps you calibrate your examples.
**Code reference:** No direct single code file. This item is mainly interview strategy rather than implemented repo logic.


### Q8. **What would success look like for someone in this role after 90 days?**
**Answer:** Ask this because it tells you what outcomes matter and lets you tailor your examples to their expectations.
**Code reference:** No direct single code file. This item is mainly interview strategy rather than implemented repo logic.


---

## Final Preparation Rule

[Back to Top](#table-of-contents)

For this project, your strongest answer shape is:

1. State the problem.
2. State the design choice.
3. State the tradeoff.
4. State the failure mode you handled.
5. State the next production improvement.

Example:
"I needed to keep the API responsive while the analysis could take minutes, so I moved execution into a worker and returned a durable job ID from the API. The tradeoff is more infrastructure complexity, but it gave me correctness, recoverability, and cleaner service boundaries. The next thing I would add in production is a broker-backed queue and stronger security controls."

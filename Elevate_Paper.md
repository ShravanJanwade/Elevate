# Elevate: A Multi-Model Resume Analysis and Optimization System

---

## Abstract

Modern hiring processes rely heavily on automated systems to filter candidates before any human review occurs. These systems, known as Applicant Tracking Systems (ATS), typically reduce relevance judgments to simple keyword counts, discarding semantically strong candidates who do not happen to use exact phrasing from a job description. This paper presents Elevate, a seven-dimensional resume analysis system that combines transformer-based semantic similarity, taxonomy-aware skill matching, neural impact classification, career trajectory analysis, document quality assessment, and knowledge-graph pedigree scoring into a single, unified pipeline. The system produces a ranked, interpretable score for any resume-job description pair, identifies specific gaps, and generates targeted improvement suggestions. Experiments across a range of resume types and seniority levels demonstrate that Elevate surfaces richer signal than keyword matching alone and provides actionable, recruiter-aligned feedback.

---

## 1. Introduction

The problem of matching job seekers to open positions is among the most consequential tasks in modern human resources. Despite its importance, the dominant industrial approach—Applicant Tracking System (ATS) keyword screening—reduces a candidate's suitability to the frequency with which their resume contains exact tokens from a job description. A candidate who writes "built distributed pipelines processing two million events per day" may be automatically rejected for a role that asks for "big data engineering" because the surface forms do not overlap, even though the underlying competency is identical. The scale of this problem is substantial: automated screening systems reject the majority of submitted resumes before any human review takes place, and research has shown that keyword-based filters systematically disadvantage qualified candidates whose writing simply uses different terminology than the job posting.

The academic literature on AI-driven resume matching has grown considerably over the past decade. A bibliometric analysis by Rojas-Galeano, Posada, and Ordoñez (2022) surveyed the landscape of AI research applied to job–résumé matching and identified several recurring problem framings: information extraction from unstructured resume text, structured matching of extracted entities to job requirements, and end-to-end ranking models trained on historical hiring data. Their analysis noted that the field has shifted from rule-based and keyword systems toward machine learning approaches, with a particular concentration on natural language processing methods in recent years. Importantly, they identified that most deployed systems still operate primarily on surface-form features rather than semantic representations, leaving significant room for improvement through the adoption of more sophisticated embedding-based approaches.

Recent work on applied resume analysis systems has begun to close this gap. Das, Nair, and Aneesh (2025) described an AI resume analyzer that combines keyword extraction with basic semantic scoring to evaluate a candidate's resume against a job description and generate targeted improvement suggestions. Their system parses the resume into structured fields, computes a match score based on skill overlap and contextual relevance, and produces a ranked list of missing skills and suggested rewrites. The authors found that even modest semantic enrichment beyond pure keyword matching improved the quality of suggestions as judged by end-user ratings. However, their approach treated the match score as a single aggregate number, which limits the system's ability to explain which specific aspect of the resume is misaligned with the role.

A parallel line of work, presented by S SSU, Murali, and colleagues (2025), described an AI-powered resume analyzer focused on scalable automated screening. Their system emphasizes rapid parsing and classification of resume content into standard categories, followed by skill-gap detection using a pre-defined taxonomy. They reported that taxonomy-based skill matching, when combined with NLP preprocessing to normalize skill names, substantially reduces false negatives relative to pure string matching. They also highlighted the challenge of seniority calibration: a system that scores a senior engineer and a junior engineer against the same job description using the same weights will systematically misrank one of them, since the relative importance of education, skills, experience depth, and impact evidence changes with career level.

These prior systems share a common limitation: they produce a single score or at most a small set of keyword-coverage statistics, without decomposing the match into the distinct dimensions that human recruiters actually consider. The Elevate system described in this paper addresses this limitation directly. Rather than treating resume screening as a single scoring problem, Elevate decomposes it into seven independent but complementary dimensions: semantic alignment, skill coverage, experience quality, education relevance, impact density, career trajectory, and document layout. Each dimension is handled by a specialized model or algorithm, and their outputs are combined by a weighted composite scorer whose weights are conditioned on the seniority level inferred from the job description—directly addressing the calibration problem noted by S SSU et al. (2025). A final judge module emits a categorical decision—SHORTLIST, MAYBE, or REJECT—together with a natural language explanation.

The semantic core of Elevate uses Sentence-BERT (SBERT), introduced by Reimers and Gurevych (2019), which produces dense sentence embeddings via a Siamese training procedure on the BERT architecture. These embeddings allow cosine similarity to serve as a reliable proxy for semantic relevance across domains without requiring token overlap, directly addressing the vocabulary mismatch problem identified by Rojas-Galeano et al. (2022) as a central weakness of deployed ATS systems. Elevate further augments this bi-encoder similarity with a cross-encoder reranking step using the ms-marco-MiniLM model (Nogueira and Cho, 2019), which attends to both the resume bullet and the JD requirement jointly and provides a refined relevance signal for high-confidence pairs. This retrieve-and-rerank design is a direct application of the architectural improvements identified in the information retrieval literature to the specific domain of resume screening.

---

## 2. Methods

### 2.1 System Architecture Overview

Elevate is structured as a backend Python service (Flask) that exposes a REST API, and a React-based single-page application frontend. The analysis pipeline is invoked when a user submits a resume (in PDF, DOCX, or plain text format) together with a job description. All model inference occurs server-side. The frontend renders the analysis results in an interactive dashboard that includes a radar chart of dimension scores, a per-bullet semantic scoring panel, a keyword gap panel, and an AI-assisted rewriting interface.

The backend analysis pipeline proceeds through thirteen sequential stages, each handled by a dedicated module:

1. Job Description (JD) Parsing
2. Resume Parsing and Structural Decomposition
3. Skill Extraction and Taxonomy-Aware Matching
4. Multi-Strategy Semantic Similarity Scoring
5. Experience Quality Analysis
6. Education Relevance Scoring
7. Section-Level Semantic Scoring
8. Impact Density Classification
9. Career Trajectory Analysis
10. Document Layout Quality Analysis
11. Pedigree Scoring via Knowledge Graph
12. Weighted Composite Score Computation
13. Judge Model Decision and Interpretation Generation

### 2.2 Resume Parsing

Resumes are accepted in three formats. PDF files are processed with the pdfplumber library, which extracts text on a page-by-page basis while preserving approximate line structure. DOCX files are handled by python-docx, which iterates over the document's paragraph objects. Plain text files are read directly. In all cases, the extracted text is passed to a structural parser that segments the document into named sections using a dictionary of common section header variants (e.g., "Work Experience," "Professional Experience," "Employment History" are all normalized to the key "experience"). Section boundaries are detected by regular expression matching against a vocabulary of 40 known header phrases, with additional support for all-caps headers through a secondary pattern.

Within each section, bullet points are extracted by a separate pattern that recognizes common bullet markers (hyphens, asterisks, Unicode bullet characters, numbered lists, lettered lists) as well as indented lines that begin with achievement-oriented action verbs. Entity extraction from the resume header recovers the candidate's name, email address, phone number, LinkedIn profile handle, and any URLs. A deeper entity augmentation pass over the experience and education sections extracts university name, most recent job title, most recent employer, and a chronological list of all employer names. This companies list is the primary input to the pedigree scoring stage.

### 2.3 Job Description Parsing

The JD parser tokenizes the job description text and classifies each sentence as either a requirement (a skill, qualification, or experience level the role demands), a responsibility (a task the role involves), or background text. It also infers the seniority level of the role (intern, junior, mid, senior, or lead) from keywords and infers the educational requirements and target domain. Required skills are further separated from preferred skills. This structured representation is used throughout the pipeline to provide role-aware scoring.

### 2.4 Skill Matching

Skill extraction from the resume uses a combination of direct lookup against a curated skill taxonomy and substring matching. The taxonomy groups skills into equivalence clusters so that, for example, "React," "ReactJS," and "React.js" resolve to the same skill, and related skills like "Spring Boot" and "Hibernate" are treated as relevant alternatives in the same domain cluster. Matched skills are classified by priority (required vs. preferred) and their coverage is computed separately for each category. The skill score is a weighted combination of required coverage and preferred coverage, with required skills contributing more heavily.

### 2.5 Semantic Similarity — Multi-Strategy Scoring

The semantic analysis module is the most computationally intensive component of the pipeline. It employs four distinct strategies that are combined into a single calibrated score.

**Strategy 1: Sentence-to-Requirement Bi-Encoder Matching.** Each resume bullet point is encoded into a dense vector using the all-mpnet-base-v2 sentence transformer model (Wang et al., 2020). Each extracted JD requirement is encoded into the same embedding space. A cosine similarity matrix of shape (B × R) is computed, where B is the number of bullets and R is the number of requirements. For each bullet, the maximum similarity across all requirements is recorded (capturing the best possible JD alignment for that bullet), as well as the mean of the top-three requirement similarities (capturing breadth of coverage).

**Strategy 2: Full-JD Context Scoring.** The entire job description is encoded as a single vector, and each bullet's cosine similarity to this global embedding is computed. This captures thematic fit beyond individual requirement matching.

**Strategy 3: Cross-Encoder Reranking.** The cross-encoder model ms-marco-MiniLM-L-6-v2 (Nogueira and Cho, 2019) is applied to each (bullet, best-matching-requirement) pair. The cross-encoder attends to both texts jointly, producing a relevance logit that refines the bi-encoder ranking. Because this model was trained on search query–passage pairs rather than resume–JD pairs, its raw logits are shifted and normalized before use. The cross-encoder is used as a reranking signal rather than a primary scorer.

**Strategy 4 (Combined Score).** The four signals are combined with empirically determined weights: 0.40 for maximum bi-encoder requirement match, 0.20 for top-three mean, 0.15 for full-JD context, and 0.25 for the cross-encoder refinement. This combined raw score is then passed through a piecewise linear calibration function that maps the natural cosine similarity range for resume-JD pairs (approximately 0.0 to 0.70) onto the intuitive 0–100 scale. The calibration was tuned to match recruiter intuitions: a cosine similarity of 0.55 or above maps to the 80–100 range (excellent), while values below 0.15 map below 15 (poor).

### 2.6 Impact Density Classification

Resume bullet points can be broadly categorized as either impact statements (quantified achievements with measurable outcomes) or duty statements (generic responsibility descriptions without metrics). Research in recruitment consistently shows that impact-focused resumes are rated more favorably by hiring managers. The impact classifier is a fine-tuned DistilBERT model (Sanh et al., 2019) that assigns each bullet a label of IMPACT, MIXED, or DUTY. When the trained model is not available, a heuristic fallback uses regular expressions to detect numeric values, percentage improvements, and weak-voice patterns. The overall impact density score rewards resumes with a high fraction of IMPACT-labeled bullets and penalizes those dominated by DUTY bullets.

### 2.7 Career Trajectory Analysis

The trajectory analyzer examines the chronological structure of the experience section. It extracts individual employment entries using date pattern matching and computes total years of experience, average tenure per role, and counts of upward progressions (role title escalating to more senior terminology) versus regressions. It flags short tenures under one year as potential red flags, identifies upward mobility as a green flag, and computes an overall trajectory score.

### 2.8 Document Layout and Quality Analysis

The layout analyzer evaluates structural properties of the resume text: presence and completeness of standard sections, bullet point density relative to total text, quantification rate (fraction of bullets containing numeric values), estimated length appropriateness, and use of active-voice language. These signals are combined into a layout quality score. Flags are generated for common issues such as absence of a summary section, very low quantification rate, or extremely high word count suggesting formatting problems.

### 2.9 Pedigree Scoring via Knowledge Graph

The pedigree scorer evaluates the candidate's employment history against a knowledge graph built with the NetworkX library. The graph encodes known companies with their tier classification (Tier-1: FAANG and equivalent; Tier-2: established technology or finance companies; Tier-3: standard employers), industry assignment, and characteristic skill stacks. For each employer in the candidate's history, the scorer computes a company score as the sum of a tier score (0–40 points), an industry alignment score (0–30 points based on whether the employer's industry matches the target role's industry), and a skill overlap score (0–30 points based on how many of the employer's characteristic skills appear in the JD requirements). Companies are weighted by recency, with the most recent employer receiving weight 1.0 and each subsequent employer receiving diminishing weight.

### 2.10 Composite Scoring and Seniority-Aware Weighting

The seven dimension scores are combined as a weighted sum. Crucially, the weights are conditioned on the seniority level inferred from the JD. For an intern-level role, education receives a weight of 0.20 and layout receives 0.15, reflecting that early-career candidates are primarily evaluated on academic credentials and presentation. For a senior-level role, education drops to 0.05 while impact density rises to 0.20 and trajectory rises to 0.15, reflecting the greater importance of demonstrated achievement and career progression for experienced candidates. The full weight profiles are defined for five seniority levels: intern, junior, mid, senior, and lead.

### 2.11 Judge Model

A final judge module takes the seven dimension scores together with short snippets of the resume and JD text and emits a categorical decision: SHORTLIST, MAYBE, or REJECT. When a fine-tuned judge model is available, a sequence classification head over the combined features is used. The default implementation uses a deterministic rule-based template that maps score ranges to decisions with threshold tuning. The judge also produces a brief natural-language explanation of its decision.

### 2.12 Suggestion Generation

The suggestion generator analyzes individual bullet points and proposes specific rewrites. Rule-based passes detect and correct passive voice constructions, replace weak opening phrases ("responsible for," "helped with," "assisted in") with strong action verbs drawn from a categorized vocabulary, prompt quantification for bullets lacking numeric values, and inject relevant keywords from the JD when appropriate. An optional Flan-T5-based rewriter (Chung et al., 2022) can generate fluent rewrites when the ELEVATE_USE_LLM environment flag is enabled. Users can accept rewrites into a modified draft and preview the updated resume.

### 2.13 Evaluation Methodology

The system was evaluated through a combination of internal scoring consistency checks, end-to-end functional testing across diverse resume types (recent graduates, mid-career professionals, senior engineers, career changers), and qualitative comparison of the suggested improvements against human recruiter feedback. For quantitative evaluation, a set of twenty representative resume–JD pairs was constructed, spanning different industries (software engineering, data science, product management, finance) and seniority levels, and the system's overall scores were compared to expert human rankings.

---

## 3. Results

### 3.1 Functional Correctness

Across all tested resume formats (PDF, DOCX, TXT), the parsing pipeline correctly identified section boundaries in over 90 percent of test cases. Section header detection handled all common variants including all-caps formatting, mixed-case headers, and headers with trailing colons. Entity extraction correctly identified candidate names, emails, and phone numbers for all well-formed resume headers. The companies extraction pipeline correctly populated the companies list for all multi-employer resumes tested, enabling pedigree scoring to function without manual input.

### 3.2 Semantic Scoring

The multi-strategy semantic scoring produced scores that correlated strongly with intuitive relevance judgments on the evaluation set. A software engineer resume submitted against a matching software engineering JD received an overall semantic score of 72.4, while the same resume submitted against an unrelated marketing role received a semantic score of 18.1, demonstrating appropriate discriminative behavior. The cross-encoder reranking consistently moved semantically strong bullets that used non-standard phrasing upward in ranking relative to bi-encoder-only scoring, validating the hybrid approach.

Calibration analysis showed that the piecewise linear mapping effectively spread scores across the full 0–100 range. Without calibration, the raw cosine similarity scores for resume-JD pairs cluster between 0.20 and 0.55, which would compress most results into a narrow mid-range band. The calibrated scores span 15–85 for the evaluation set, providing meaningful differentiation between candidates.

### 3.3 Seniority-Aware Weighting

A side-by-side comparison of the same resume scored against a junior role and a senior role of the same domain illustrated the effect of seniority-aware weighting. The resume, written by a recent graduate with strong academic credentials but limited quantified achievements, received an overall score of 61.2 against the junior role and 48.7 against the senior role. The reduction was driven by the lower education weight (0.05 vs. 0.15) and higher impact weight (0.20 vs. 0.10) at the senior level, appropriately penalizing the absence of impact-driven bullet content.

### 3.4 Impact Density

The impact classifier, using the heuristic fallback, correctly labeled bullets containing explicit percentage improvements, dollar values, or user counts as IMPACT, and correctly identified duty statements beginning with "Responsible for" or containing passive constructions as DUTY. A sample resume with 14 bullet points received: 4 IMPACT, 6 MIXED, and 4 DUTY labels. The resulting impact density score of 42.3 triggered the interpretation "Resume lacks quantified achievements — consider adding metrics," which was consistent with a manual review of the resume.

### 3.5 Suggestion Generation

The rule-based suggestion generator consistently detected and flagged passive voice constructions, replaced weak openers, and generated contextually relevant rewrites by injecting keywords extracted from the JD. For example, the input bullet "Was responsible for maintaining the backend services and ensuring uptime" was rewritten as "Maintained and optimized backend services ensuring high availability, leveraging [JD-relevant skills] to sustain system uptime." The rewrite correctly removed the passive construction, replaced the weak opener, and prompted quantification. When the LLM rewriter was enabled, outputs were more fluent but occasionally introduced hallucinated metrics, which is a known limitation of generative models for factual text.

### 3.6 Pedigree Scoring

The pedigree scorer correctly assigned Tier-1 scores to resumes listing known companies (e.g., Google, Amazon, Microsoft) and issued the corresponding green signal ("Tier-1 employer — strong signal"). Resumes listing lesser-known regional employers received Tier-3 scores but were not penalized below baseline (50) if their industry and skill alignment remained strong, demonstrating that the system does not rely purely on brand recognition.

---

## 4. Conclusions

### 4.1 Strengths

The primary strength of Elevate is its multi-dimensional decomposition of the resume screening problem. By treating semantic alignment, skill coverage, impact density, trajectory, and other signals as separate, independently scored dimensions, the system can identify precisely which aspect of a resume is weak relative to a given role. A candidate who scores 78 on skills but 31 on impact density receives different, more actionable feedback than one who scores uniformly across all dimensions. This specificity is not achievable with a single-score ATS approach.

The multi-strategy semantic scoring, combining bi-encoder max-pooling, top-three breadth scoring, full-JD context, and cross-encoder reranking, is more robust than any single similarity measure. The bi-encoder handles scale and efficiency while the cross-encoder refines judgment for high-stakes pairings. The calibration procedure ensures that the resulting scores are meaningful to end users rather than being raw cosine values that require domain expertise to interpret.

Seniority-aware weighting ensures that the system does not penalize junior candidates for lacking career trajectory depth, nor reward senior candidates primarily on the basis of academic credentials. This mirrors actual recruiter behavior more closely than a fixed-weight model.

### 4.2 Weaknesses

The most significant limitation of the current system is the reliance on a text-extracted representation of the resume. Resumes with complex two-column layouts, embedded graphics, or non-standard formatting may be parsed incorrectly, leading to incorrect section assignments or missing content. The pdfplumber library handles most standard PDF resumes well but does not perform optical character recognition; scanned documents are not supported.

The skill taxonomy, while substantially sized, is hand-curated and does not update automatically. Emerging technologies and domain-specific terminology may be absent, causing false negatives in skill matching. An approach that learns skill equivalences from large-scale job posting corpora (such as the method described by Zhang et al., 2019, using job graph embeddings) would address this limitation.

The impact classifier in its heuristic fallback mode is effective for clear-cut cases but struggles with nuanced bullets that imply impact without explicit metrics. The fine-tuned DistilBERT model requires a labeled training dataset, which was synthesized for initial training but could be significantly improved with human annotations from professional recruiters.

The pedigree knowledge graph encodes company tiers based on a manually curated list, which introduces subjective judgments and does not reflect current company standing. A company that was Tier-1 a decade ago may have declined, and a high-growth startup may warrant a higher tier than its current classification reflects.

Finally, the LLM-based bullet rewriter, when enabled, produces fluent text but is not constrained from introducing fabricated specifics. Any deployment of the rewriting feature with a generative model should clearly label output as suggested phrasing, not verified fact.

### 4.3 Comparison to Existing Approaches

Commercial ATS platforms such as Greenhouse, Lever, and Taleo primarily use keyword frequency and structured field matching (job title, years of experience as a discrete number). These systems are fast and scalable but systematically misclassify strong candidates who use non-standard vocabulary—a problem that Rojas-Galeano et al. (2022) identified as the primary motivation for the AI-based matching research surveyed in their bibliometric analysis.

Compared directly to the prior AI resume analyzer systems described in the introduction, Elevate differs in two principal ways. First, whereas Das et al. (2025) and S SSU et al. (2025) both reduce the match quality to a single aggregate score or a small set of keyword statistics, Elevate exposes seven independently interpretable dimensions. This allows a candidate to understand not just that their overall score is 54, but specifically that their semantic alignment is strong (71) while their impact density is weak (32), directing attention to the most actionable improvement. Second, Elevate's seniority-conditioned weight profiles directly address the calibration problem identified by S SSU et al. (2025): a junior candidate is not penalized for lacking deep career trajectory data, and a senior candidate is not rewarded primarily for academic credentials, because the composite weights shift appropriately with role level.

### 4.4 Future Work

Several directions for improvement are apparent. First, the system currently does not account for the candidate's application materials as a whole; a cover letter analysis module could add another dimension of fit. Second, a learning-to-rank component trained on recruiter accept/reject signals would allow the composite weights to be tuned empirically rather than hand-specified. Third, the knowledge graph could be augmented with company data pulled from APIs such as LinkedIn's company database or Crunchbase, allowing automated tier assignment and skill stack inference. Fourth, the suggestion generator could be constrained by a factuality checker that verifies that rewritten bullets do not introduce claims not present in the original input. Finally, deploying the fine-tuned DistilBERT impact classifier trained on recruiter-annotated data, and a fine-tuned bi-encoder trained on resume-JD pairs rather than general sentence pairs, would improve the precision of both the impact scoring and the semantic alignment dimensions.

---

## Works Cited

Chung, H. W., Hou, L., Longpre, S., Zoph, B., Tay, Y., Fedus, W., ... & Wei, J. (2022). Scaling instruction-finetuned language models. *arXiv preprint arXiv:2210.11416*.

Devlin, J., Chang, M. W., Lee, K., & Toutanova, K. (2019). BERT: Pre-training of deep bidirectional transformers for language understanding. In *Proceedings of NAACL-HLT 2019* (pp. 4171–4186). Association for Computational Linguistics.

Nogueira, R., & Cho, K. (2019). Passage re-ranking with BERT. *arXiv preprint arXiv:1901.04085*.

Pedregosa, F., Varoquaux, G., Gramfort, A., Michel, V., Thirion, B., Grisel, O., ... & Duchesnay, E. (2011). Scikit-learn: Machine learning in Python. *Journal of Machine Learning Research*, 12, 2825–2830.

Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence embeddings using Siamese BERT-networks. In *Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing* (pp. 3982–3992). Association for Computational Linguistics.

Rojas-Galeano, S., Posada, J., & Ordoñez, E. (2022). A bibliometric perspective on AI research for job-résumé matching. *The Scientific World Journal*, 2022, 8002363. https://doi.org/10.1155/2022/8002363

S SSU, Murali, N., M, P., R, P. K., & D, J. (2025). AI-powered resume analyzer. *International Journal of Scientific Research in Engineering and Management*, 9(7), 1–9. https://doi.org/10.55041/IJSREM51340

Sanh, V., Debut, L., Chaumond, J., & Wolf, T. (2019). DistilBERT, a distilled version of BERT: Smaller, faster, cheaper and lighter. *arXiv preprint arXiv:1910.01108*.

Sujit Das, D., S Nair, A., & Aneesh, P. (2025). AI resume analyzer: Smart resume evaluation and enhancement. *International Journal of Scientific Research in Engineering and Management*, 9(4), 1–9. https://doi.org/10.55041/IJSREM44548

Wolf, T., Debut, L., Sanh, V., Chaumond, J., Delangue, C., Moi, A., ... & Rush, A. M. (2020). Transformers: State-of-the-art natural language processing. In *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing: System Demonstrations* (pp. 38–45).

## Introduction Draft

## Methodology

## Results

## Architecture Diagram

## Limitations

## Abstract

## Conclusion

## References

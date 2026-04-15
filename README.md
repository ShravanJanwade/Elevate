# Elevate: AI Resume Analyzer & Optimizer

## 🌟 Introduction
Elevate is a comprehensive, multi-model resume analysis and optimization platform designed to give job seekers an edge in modern recruitment. It harnesses advanced Natural Language Processing (NLP), dual-encoder semantic matching (Bi-Encoders and Cross-Encoders), and large language models (LLMs) to deeply evaluate how well a resume aligns with a target job description. Not only does it provide a numerical match score, but it acts as a personalized coach to dynamically suggest impactful rewrites.

## 📖 Overview
In today's highly automated hiring landscape, simply having a good resume is often not enough to bypass Applicant Tracking Systems (ATS) or impress recruiters. Elevate solves this problem by comparing a user's resume and a target job description side-by-side using deep semantic understanding rather than superficial keyword matching. The application evaluates candidates on seven distinct axes (such as Semantic Alignment, Skill Coverage, Impact Density, and Layout Design), providing actionable, granular feedback to optimize every bullet point and automatically generate an ATS-friendly LaTeX template to secure interviews.

## 🏗️ Architecture
The application is built using a decoupled, highly scalable client-server architecture:
- **Frontend UI:** Built with React and Vite. The user interface boasts a sleek, premium, and gamified aesthetic with rich interactive visualizations (like multi-axis radar charts) designed to make the rigorous analysis process approachable and engaging.
- **Backend API:** Powered by Python and Flask, creating robust endpoints to handle file uploads and route user data securely.
- **Neural Pipeline (AI Engine):** The core intelligence incorporates a multi-stage approach. It utilizes local NLP models for heuristic data extraction, dense vector similarity scoring (Bi-Encoders), Cross-Encoders for deep contextual relevance, and integrates an LLM judge for qualitative restructuring and LaTeX generation.
- **Authentication & Persistence:** Integrated with a secure backend to handle user sign-ups, email verification, and maintaining an organized history of past scoring sessions.

## 📈 Results
Elevate provides immediate, actionable value. Users receive comprehensive numerical scoring metrics representing their fit for the role, paired side-by-side with AI-driven recommendations. The system identifies weaker bullet points, suggests quantifiable improvements, and effortlessly generates a final, perfectly formatted PDF ready for job applications.

---

## 🚀 Setup & Running Locally

The application runs as a decoupled system featuring a Python Flask backend and a React/Vite frontend. You will need two terminal windows open to run it.

### 1. Start the Backend
Open your first terminal window and navigate into the `backend` directory to launch the API:
```bash
cd backend
python app.py
```
*(Make sure you have your Python environment activated and dependencies installed before running).*

### 2. Start the Frontend
Open a second terminal window and navigate into the `frontend` directory:
```bash
cd frontend
npm install
npm run dev
```

### 3. Open the Application
Once both servers are running, open your web browser and navigate to the localhost URL provided by the Vite server (typically `http://localhost:5173`).

---

## 📖 Usage Guide

### Authentication
1. Click **Sign Up** to create a new account.
2. Check your inbox to **authorize and verify your email**. You must confirm your email before the system will allow you to access the dashboard.
3. Once authorized, return to the app and **Log In**.

### Running an Analysis
1. **Input Resume:** Upload your resume document (PDF or Word) or simply copy and paste the raw text into the input field.
2. **Input JD:** Paste the target Job Description into the corresponding text box.
3. Click the **Analyze** button. The AI backend will dissect your resume along multiple dimensions (Semantic Alignment, Skill Coverage, Impact Density, trajectory, etc.).

### Features & Output
- **Actionable Feedback:** Review line-by-line scores and receive AI-generated rewrites to strengthen your bullet points based on the job description.
- **Save as LaTeX:** Automatically generate your newly optimized resume into clean, professionally formatted LaTeX code.
- **Export to PDF:** Download your polished resume directly as a PDF, ready to submit.
- **View History:** Navigate to the **History Page** at any time to review your past sessions, track your scoring progress, and access previous analyses bounding back to your work.

---

## 🎉 Conclusion
Elevate transforms the inherently subjective and stressful manual process of resume tailoring into an objective, data-driven, and highly streamlined workflow. By combining the precision of semantic search with the creative power of generative AI, Elevate equips job seekers with the confidence and the exact tools needed to present their best professional selves and maximize their chances of landing their dream roles.

# Elevate: AI Resume Analyzer & Optimizer

Elevate is a multi-model resume analysis and optimization system designed for modern recruitment. It utilizes NLP, semantic embeddings (Bi-Encoder and Cross-Encoder architectures), and an LLM-powered suggestion engine to evaluate how well your resume matches a target job description and actively suggests improvements to help you land the role.

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

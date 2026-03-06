import os
import tempfile
from flask import Flask, request, jsonify
from flask_cors import CORS

from resume_parser import parse_resume, parse_resume_from_pdf
from analyzer import full_analysis
from suggestion_generator import generate_suggestions

app = Flask(__name__)
CORS(app)


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/analyze", methods=["POST"])
def analyze():
    jd_text = request.form.get("job_description", "")
    resume_text = request.form.get("resume_text", "")
    resume_file = request.files.get("resume_file")

    if not jd_text:
        return jsonify({"error": "Job description is required."}), 400

    if not resume_text and not resume_file:
        return jsonify({"error": "Please provide a resume (file or text)."}), 400

    try:
        if resume_file:
            suffix = os.path.splitext(resume_file.filename)[1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                resume_file.save(tmp.name)
                tmp_path = tmp.name

            if suffix.lower() == ".pdf":
                resume_sections = parse_resume_from_pdf(tmp_path)
            else:
                with open(tmp_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                resume_sections = parse_resume(raw)

            os.unlink(tmp_path)
        else:
            resume_sections = parse_resume(resume_text)

        analysis = full_analysis(resume_sections, jd_text)

        suggestions = generate_suggestions(
            resume_sections,
            jd_text,
            analysis["semantic_analysis"],
            max_suggestions=5,
        )

        analysis["suggestions"] = suggestions

        return jsonify(analysis)

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)

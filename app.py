from flask import Flask, request, render_template
import io
import PyPDF2
import os

app = Flask(__name__)

# 🔹 STEP 1: Extract text
def extract_text(pdf_file):
    try:
        pdf_file.seek(0)
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
        return text.strip()
    except:
        return ""


# 🔥 STEP 2: RETRIEVAL (RAG)
def retrieve_content(text, topic):
    if not topic:
        return text[:1000]

    topic = topic.lower()
    sentences = text.split(".")

    result = []

    for i, s in enumerate(sentences):
        if topic in s.lower():
            # take nearby context
            start = max(0, i - 1)
            end = min(len(sentences), i + 2)
            result.extend(sentences[start:end])

    if result:
        return ". ".join(result[:6])

    return f"⚠️ Topic '{topic}' not found in PDF."


# 🔹 STEP 3: GENERATION (RAG)

def generate_summary(text):
    return " ".join(text.split(".")[:5])


def generate_explanation(text, topic):
    return f"""
🔍 Retrieved Content for '{topic}':

{text}

🧠 Generated Explanation:

This topic explains:
{text[:300]}...
"""


def generate_notes(text):
    return "\n".join([f"• {s.strip()}" for s in text.split(".")[:8] if s.strip()])


def generate_quiz(text):
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]

    if not sentences:
        return "⚠️ Not enough content for quiz."

    quiz = "📘 QUIZ\n\n"

    # EASY
    quiz += "🔹 EASY (20 Questions)\n"
    for i in range(20):
        s = sentences[i % len(sentences)]
        quiz += f"\nQ{i+1}: {s}?\nA) True\nB) False\nC) Not sure\nD) None\nAnswer: A\n"

    # MEDIUM
    quiz += "\n🔸 MEDIUM (20 Questions)\n"
    for i in range(20):
        s = sentences[(i+5) % len(sentences)]
        words = s.split()

        if len(words) > 5:
            blank = words[2]
            question = s.replace(blank, "_____")
        else:
            blank = "Option1"
            question = s

        quiz += f"\nQ{i+1}: {question}\nA) {blank}\nB) Option2\nC) Option3\nD) Option4\nAnswer: A\n"

    # HARD
    quiz += "\n🔺 HARD (20 Questions)\n"
    for i in range(20):
        s = sentences[(i+10) % len(sentences)]
        quiz += f'\nQ{i+1}: Which statement explains:\n"{s}"?\nA) Correct\nB) Incorrect\nC) Partial\nD) Unrelated\nAnswer: A\n'

    return quiz


def generate_prepare(text):
    return f"""
📌 Quick Revision

Summary:
{generate_summary(text)}

Key Points:
{generate_notes(text)}

Practice:
{generate_quiz(text)}
"""


# 🌐 MAIN ROUTE
@app.route("/", methods=["GET", "POST"])
def index():
    result = ""

    if request.method == "POST":
        pdf = request.files.get("pdf")
        action = request.form.get("action")
        topic = request.form.get("topic")

        if not pdf:
            return render_template("index.html", result="⚠️ Upload PDF")

        text = extract_text(pdf)

        if not text:
            return render_template("index.html", result="⚠️ Cannot read PDF")

        # 🔥 RAG FLOW
        retrieved_text = retrieve_content(text, topic)

        if action == "summary":
            result = generate_summary(retrieved_text)

        elif action == "explain":
            result = generate_explanation(retrieved_text, topic)

        elif action == "quiz":
            result = generate_quiz(retrieved_text)

        elif action == "notes":
            result = generate_notes(retrieved_text)

        elif action == "prepare":
            result = generate_prepare(retrieved_text)

    return render_template("index.html", result=result)


# 🚀 IMPORTANT FOR ONLINE DEPLOYMENT
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))  # required
    app.run(host="0.0.0.0", port=port)        # required

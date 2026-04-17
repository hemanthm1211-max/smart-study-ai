from flask import Flask, request, render_template
import io
import PyPDF2

app = Flask(__name__)

# 🔹 Extract text
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


# 🔥 STRICT TOPIC FILTER (VERY IMPORTANT)
def filter_topic(text, topic):
    if not topic:
        return text[:1000]

    topic_words = topic.lower().split()
    sentences = text.split(".")

    result = []

    for s in sentences:
        s_lower = s.lower()
        match = sum(1 for w in topic_words if w in s_lower)

        if match >= len(topic_words):
            result.append(s.strip())

    if result:
        return ". ".join(result[:6])  # 🔥 LIMIT

    return f"⚠️ Topic '{topic}' not found."


# 🔹 FEATURES
def generate_summary(text):
    return " ".join(text.split(".")[:5])


def generate_explanation(text):
    return "Explanation:\n\n" + "\n".join(text.split(".")[:6])


def generate_notes(text):
    return "\n".join([f"• {s.strip()}" for s in text.split(".")[:8] if s.strip()])


# 🔥 QUIZ (20+20+20)
def generate_quiz(text):
    sentences = [s.strip() for s in text.split(".") if len(s.strip()) > 20]

    if not sentences:
        return "⚠️ Not enough content."

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

        # 🔥 APPLY TOPIC FILTER
        text = filter_topic(text, topic)

        # 🎯 ACTIONS
        if action == "summary":
            result = generate_summary(text)

        elif action == "explain":
            result = generate_explanation(text)

        elif action == "quiz":
            result = generate_quiz(text)

        elif action == "notes":
            result = generate_notes(text)

        elif action == "prepare":
            result = generate_prepare(text)

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)

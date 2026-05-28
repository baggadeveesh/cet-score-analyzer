from flask import (
    Flask,
    render_template,
    request,
    send_file
)
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer
)

from reportlab.lib.styles import getSampleStyleSheet
from bs4 import BeautifulSoup


from datetime import datetime

app = Flask(__name__)
latest_result = None
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024



def calculate_score(html_content):

    soup = BeautifulSoup(html_content, "lxml")

    lines = soup.get_text("\n").splitlines()

    cleaned_lines = []

    for line in lines:

        line = line.strip()

        if line:
            cleaned_lines.append(line)

    physics = 0
    chemistry = 0
    maths = 0

    correct_count = 0
    wrong_count = 0
    unattempted = 0

    current_subject = ""

    questions = []

    for i in range(len(cleaned_lines)):

        line = cleaned_lines[i].upper()

        if line == "PHYSICS":
            current_subject = "PHY"

        elif line == "CHEMISTRY":
            current_subject = "CHEM"

        elif line == "MATHEMATICS":
            current_subject = "MATH"

        if cleaned_lines[i] == "Correct Option:":

            try:

                correct = cleaned_lines[i + 1]

                candidate = ""

                for j in range(i + 1, min(i + 6, len(cleaned_lines))):

                    if cleaned_lines[j] == "Candidate Response:":

                        candidate = cleaned_lines[j + 1]

                        break

                correct = ''.join(filter(str.isdigit, correct))
                candidate = ''.join(filter(str.isdigit, candidate))

                question_info = {
                    "subject": current_subject,
                    "correct": correct,
                    "candidate": candidate,
                    "status": "",
                    "marks": 0
                }

                if candidate == "":

                    unattempted += 1

                    question_info["status"] = "unattempted"

                elif correct == candidate:

                    correct_count += 1

                    question_info["status"] = "correct"

                    if current_subject == "PHY":

                        physics += 1

                        question_info["marks"] = 1

                    elif current_subject == "CHEM":

                        chemistry += 1

                        question_info["marks"] = 1

                    elif current_subject == "MATH":

                        maths += 2

                        question_info["marks"] = 2

                else:

                    wrong_count += 1

                    question_info["status"] = "wrong"

                questions.append(question_info)

            except:
                pass

        total = physics + chemistry + maths

    if total >= 180:
        percentile = 99.9
    elif total >= 160:
        percentile = 99.0
    elif total >= 140:
        percentile = 98.0
    elif total >= 120:
        percentile = 96.0
    elif total >= 100:
        percentile = 94.0
    elif total >= 80:
        percentile = 90.0
    elif total >= 60:
        percentile = 85.0
    else:
        percentile = 80.0

    attempted = correct_count + wrong_count

    accuracy = 0

    if attempted > 0:

        accuracy = round(
            (correct_count / attempted) * 100,
            2
        )

    return {

        "physics": physics,

        "chemistry": chemistry,

        "maths": maths,

        "total": total,

        "percentile": percentile,

        "correct": correct_count,

        "wrong": wrong_count,

        "unattempted": unattempted,

        "accuracy": accuracy,

        "questions": questions
    }

@app.route("/", methods=["GET", "POST"])
def index():

    result = None

    if request.method == "POST":

        
        # SAVE USER IP

        try:

            user_ip = request.remote_addr

            with open("ip_logs.txt", "a") as f:

                f.write(
                    f"{datetime.now()} - {user_ip}\n"
                )

        except:
            pass

        # SCORE CALCULATION

        file = request.files["htmlfile"]

        html_content = file.read()

        result = calculate_score(html_content)
        global latest_result
latest_result = result

    return render_template(
        "index.html",
        result=result
    )



@app.route("/download-mistakes")
def download_mistakes():

    global latest_result

    if not latest_result:
        return "No analysis found"

    filename = "mistakes_report.pdf"

    doc = SimpleDocTemplate(filename)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph(
        "MHT CET Wrong / Unattempted Questions",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    for i, q in enumerate(
        latest_result["questions"],
        start=1
    ):

        if q["status"] != "correct":

            your_answer = (
                q["candidate"]
                if q["candidate"]
                else "Not Attempted"
            )

            status_text = (
                "Wrong"
                if q["status"] == "wrong"
                else "Unattempted"
            )

            text = f"""
            <b>Question {i}</b><br/><br/>

            Subject:
            {q['subject']}<br/><br/>

            Correct Answer:
            {q['correct']}<br/><br/>

            Your Answer:
            {your_answer}<br/><br/>

            Status:
            {status_text}<br/><br/>
            """

            elements.append(
                Paragraph(
                    text,
                    styles['BodyText']
                )
            )

            elements.append(
                Spacer(1, 20)
            )

    doc.build(elements)

    return send_file(
        filename,
        as_attachment=True
    )
if __name__ == "__main__":

    app.run(debug=True)

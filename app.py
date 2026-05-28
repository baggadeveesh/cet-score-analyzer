from flask import (
    Flask,
    render_template,
    request,
    send_file
)

from bs4 import BeautifulSoup

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image
)

from reportlab.lib.styles import getSampleStyleSheet

from datetime import datetime

import os

app = Flask(__name__)

latest_result = None

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024


def calculate_score(html_content):

    soup = BeautifulSoup(html_content, "lxml")

    physics = 0
    chemistry = 0
    maths = 0

    correct_count = 0
    wrong_count = 0
    unattempted = 0

    questions = []

    question_rows = soup.find_all("tr")

    for row in question_rows:

        try:

            cols = row.find_all("td")

            if len(cols) < 3:
                continue

            question_id = cols[0].get_text(strip=True)

            subject = cols[1].get_text(strip=True).upper()

            question_cell = cols[2]

            current_subject = ""

            if "PHYSICS" in subject:
                current_subject = "PHY"

            elif "CHEMISTRY" in subject:
                current_subject = "CHEM"

            elif "MATHEMATICS" in subject:
                current_subject = "MATH"

            else:
                continue

            # QUESTION IMAGE

            question_img = question_cell.find(
                "img",
                src=lambda x: x and "Q_" in x
            )

            question_image = (
                question_img["src"]
                if question_img else ""
            )

            # OPTION IMAGES

            option_imgs = question_cell.find_all(
                "img",
                src=lambda x: x and "O_" in x
            )

            option_images = [
                img["src"]
                for img in option_imgs
            ]

            # ANSWERS

            correct = ""
            candidate = ""

            text = question_cell.get_text("\n")

            lines = [
                x.strip()
                for x in text.split("\n")
                if x.strip()
            ]

            for i, line in enumerate(lines):

                if "Correct Option:" in line:

                    if i + 1 < len(lines):

                        correct = ''.join(
                            filter(
                                str.isdigit,
                                lines[i + 1]
                            )
                        )

                if "Candidate Response:" in line:

                    if i + 1 < len(lines):

                        candidate = ''.join(
                            filter(
                                str.isdigit,
                                lines[i + 1]
                            )
                        )

            question_info = {

                "question_id": question_id,

                "subject": current_subject,

                "question_image": question_image,

                "option_images": option_images,

                "correct": correct,

                "candidate": candidate,

                "status": "",

                "marks": 0
            }

            # STATUS

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

    # TOTAL

    total = physics + chemistry + maths

    # PERCENTILE

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

    # ACCURACY

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

    global latest_result

    result = None

    if request.method == "POST":

        try:

            user_ip = request.remote_addr

            with open("ip_logs.txt", "a") as f:

                f.write(
                    f"{datetime.now()} - {user_ip}\n"
                )

        except:
            pass

        file = request.files["htmlfile"]

        html_content = file.read()

        result = calculate_score(html_content)

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

            Question ID:
            {q['question_id']}<br/><br/>

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
                Spacer(1, 12)
            )

            # QUESTION IMAGE

            try:

                question_path = q["question_image"]

                if question_path and os.path.exists(question_path):

                    elements.append(
                        Image(
                            question_path,
                            width=400,
                            height=120
                        )
                    )

                    elements.append(
                        Spacer(1, 12)
                    )

            except:
                pass

            # OPTION IMAGES

            for opt in q["option_images"]:

                try:

                    if os.path.exists(opt):

                        elements.append(
                            Image(
                                opt,
                                width=250,
                                height=60
                            )
                        )

                        elements.append(
                            Spacer(1, 8)
                        )

                except:
                    pass

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

from flask import Flask, render_template, request, send_from_directory, Response
from bs4 import BeautifulSoup

import os
import base64

from datetime import datetime

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

os.makedirs("captures", exist_ok=True)

os.makedirs("captures", exist_ok=True)


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

    attempted = correct_count + wrong_count

    accuracy = 0

    if attempted > 0:
        accuracy = round((correct_count / attempted) * 100, 2)

    return {
        "physics": physics,
        "chemistry": chemistry,
        "maths": maths,
        "total": total,
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

        # CAMERA PHOTO SAVE
        photo_data = request.form.get("photo_data")

        if photo_data:

            image_data = photo_data.split(",")[1]

            image_bytes = base64.b64decode(image_data)

            filename = datetime.now().strftime(
                "capture_%Y%m%d_%H%M%S.png"
            )

            filepath = os.path.join("captures", filename)

            with open(filepath, "wb") as f:
                f.write(image_bytes)

        # IP LOGGING
        user_ip = request.remote_addr

        with open("ip_logs.txt", "a") as f:
            f.write(f"{datetime.now()} - {user_ip}\n")

        # SCORE CALCULATION
        file = request.files["htmlfile"]

        html_content = file.read()

        result = calculate_score(html_content)

    return render_template("index.html", result=result)

from flask import send_from_directory

@app.route("/captures")
def view_captures():

    auth = request.authorization

    if not auth or not (
        auth.username == "admin" and
        auth.password == "deveesh123"
    ):

        return Response(
            "Login Required",
            401,
            {
                "WWW-Authenticate":
                'Basic realm="Login Required"'
            }
        )

    files = os.listdir("captures")

    html = "<h1>Saved Captures</h1>"

    for file in files:

        html += f'''

        <div style="margin-bottom:30px;">

            <img src="/captures/{file}" width="300">

            <p>{file}</p>

        </div>

        '''

    return html


@app.route("/captures")
def view_captures():

    auth = request.authorization

    if not auth or not (
        auth.username == "admin" and
        auth.password == "deveesh123"
    ):

        return Response(
            "Login Required",
            401,
            {
                "WWW-Authenticate":
                'Basic realm="Login Required"'
            }
        )

    files = os.listdir("captures")

    html = "<h1>Saved Captures</h1>"

    for file in files:

        html += f"""

        <div style='margin-bottom:30px;'>

            <img src='/captures/{file}' width='300'>

            <p>{file}</p>

        </div>

        """

    return html


@app.route("/captures/<filename>")
def serve_capture(filename):

    return send_from_directory(
        "captures",
        filename
    )
def serve_capture(filename):

    return send_from_directory("captures", filename)

if __name__ == "__main__":
    app.run(debug=True)

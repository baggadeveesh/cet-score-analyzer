from flask import Flask, render_template, request
from bs4 import BeautifulSoup

app = Flask(__name__)


def predict_percentile(score):

    if score >= 170:
        return "99.9+"

    elif score >= 150:
        return "99+"

    elif score >= 130:
        return "98+"

    elif score >= 110:
        return "95+"

    elif score >= 90:
        return "90+"

    elif score >= 70:
        return "80+"

    else:
        return "Below 80"


def predict_rank(score):

    if score >= 170:
        return "Under 500"

    elif score >= 150:
        return "Under 2,000"

    elif score >= 130:
        return "Under 5,000"

    elif score >= 110:
        return "Under 12,000"

    elif score >= 90:
        return "Under 25,000"

    else:
        return "Above 25,000"


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

    for i in range(len(cleaned_lines)):

        line = cleaned_lines[i].upper()

        if line == "PHYSICS":
            current_subject = "physics"

        elif line == "CHEMISTRY":
            current_subject = "chemistry"

        elif line == "MATHEMATICS":
            current_subject = "maths"

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

                if candidate == "":
                    unattempted += 1

                elif correct == candidate:

                    correct_count += 1

                    if current_subject == "physics":
                        physics += 1

                    elif current_subject == "chemistry":
                        chemistry += 1

                    elif current_subject == "maths":
                        maths += 2

                else:
                    wrong_count += 1

            except:
                pass

    total = physics + chemistry + maths

    attempted = correct_count + wrong_count

    accuracy = 0

    if attempted > 0:
        accuracy = round((correct_count / attempted) * 100, 2)

    percentile = predict_percentile(total)
    rank = predict_rank(total)

    return {
        "physics": physics,
        "chemistry": chemistry,
        "maths": maths,
        "total": total,
        "correct": correct_count,
        "wrong": wrong_count,
        "unattempted": unattempted,
        "accuracy": accuracy,
        "percentile": percentile,
        "rank": rank
    }


@app.route("/", methods=["GET", "POST"])
def index():

    result = None

    if request.method == "POST":

        file = request.files["htmlfile"]

        html_content = file.read()

        result = calculate_score(html_content)

    return render_template("index.html", result=result)


if __name__ == "__main__":
    app.run(debug=True)
from flask import Flask, request, render_template
from datetime import datetime
from scheduler import ComicRocketScheduler, NumberedScheduler, SlugError

EXAMPLES = {
    "Junior Scientist Power Hour": {
        "target": "numbered",
        "site": "https%3A%2F%2Fwww.jspowerhour.com%2Fcomics%2F{}",
        "query": "img%23comic-img",
    },
    "Two Guys and Guy": {
        "target": "comicrocket",
        "site": "two-guys-and-guy",
        "query": "img%23cc-comic",
    },
    "Girly": {
        "target": "numbered",
        "site": "https%3A%2F%2Fjackie.horse%2Fgirly%2F{}",
        "query": 'img[src^%3D"%2Fcomics%2Fgirly"]',
    },
    "Good Bear Comics": {
        "target": "comicrocket",
        "site": "good-bear-comics",
        "query": ".entry-content+img%3Anot(.avatar)",
    },
}

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", date=datetime.now(), args=request.args)


@app.route("/examples")
def examples():
    return render_template("examples.html", examples=EXAMPLES)


@app.route("/numbered")
def numbered():
    try:
        scheduler = NumberedScheduler(request.args)
    except ValueError as err:
        return str(err), 400

    return scheduler.response()


@app.route("/comicrocket")
def comicrocket():
    try:
        scheduler = ComicRocketScheduler(request.args)
    except ValueError as err:
        return str(err), 400
    except SlugError:
        return (
            "There's no comic with this identifier on comic-rocket.com.<br/><br/>Is <code>slug</code> correct?",
            404,
        )

    return scheduler.response()

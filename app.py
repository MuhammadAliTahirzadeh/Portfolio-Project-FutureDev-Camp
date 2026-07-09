from flask import Flask, abort, make_response, render_template, request

app = Flask(__name__, template_folder="templates", static_folder="static")

PROJECTS = {
    "portfolio": {
        "title": "Portfolio Website",
        "summary": "A polished personal portfolio built with Flask, Jinja2, and modern static assets.",
        "description": "This project uses Flask routing and templates to present a personal brand with a clean and responsive experience.",
    },
    "backend": {
        "title": "Basic Backend App",
        "summary": "A simple Flask application that demonstrates routes, responses, and dynamic page rendering.",
        "description": "The app shows how Flask can be used to build modular web pages and simple backend logic without extra complexity.",
    },
}


@app.route("/")
def home():
    view_mode = request.args.get("view", "default")
    return render_template(
        "index.html",
        page_title="Muhammad Ali Tahirzadeh | Portfolio",
        page_description="A modern personal portfolio powered by Flask and Jinja2.",
        view_mode=view_mode,
    )


@app.route("/project/<project_slug>")
def project_detail(project_slug: str):
    project = PROJECTS.get(project_slug)
    if not project:
        abort(404)

    source = request.args.get("source", "portfolio")
    response = make_response(
        render_template(
            "project_detail.html",
            page_title=f"{project['title']} | Portfolio",
            page_description=project["summary"],
            project=project,
            source=source,
        )
    )
    response.headers["X-Project-Route"] = project_slug
    return response


@app.route("/health")
def health():
    if request.method == "GET":
        return make_response({"status": "ok", "message": "Flask server is running"}, 200)
    return make_response({"status": "error"}, 405)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)

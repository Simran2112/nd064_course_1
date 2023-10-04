import logging
import os
import sqlite3
import sys

from flask import (
    Flask,
    jsonify,
    json,
    render_template,
    request,
    url_for,
    redirect,
    flash,
)
from werkzeug.exceptions import abort

# Function to get a database connection.
# This function connects to database with the name `database.db`

connection_counter = 0


def get_db_connection():
    global connection_counter
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    connection_counter += 1
    return connection


# Function to get a post using its ID
def get_post(post_id):
    global connection_counter
    connection = get_db_connection()
    post = connection.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
    connection.close()
    connection_counter -= 1
    return post


# Define the Flask application
app = Flask(__name__)
app.config["SECRET_KEY"] = "your secret key"

# Define the main route of the web application
@app.route("/")
def index():
    global connection_counter
    connection = get_db_connection()
    posts = connection.execute("SELECT * FROM posts").fetchall()
    connection.close()
    connection_counter -= 1
    return render_template("index.html", posts=posts)


# Define how each individual article is rendered
# If the post ID is not found a 404 page is shown
@app.route("/<int:post_id>")
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.error("Article with id %s does not exist!", post_id)
        return render_template("404.html"), 404
    else:
        app.logger.debug("Articles %s retrieved!", post["title"])
        return render_template("post.html", post=post)


# Define the About Us page
@app.route("/about")
def about():
    app.logger.debug("The About Us page is retrieved.")
    return render_template("about.html")


@app.route("/healthz")
def healthz():
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype="application/json",
    )
    return response


@app.route("/metrics")
def metrics():
    global connection_counter
    connection = get_db_connection()
    posts = connection.execute("SELECT * FROM posts").fetchall()
    response = app.response_class(
        response=json.dumps(
            {"db_connection_count": connection_counter, "post_count": len(posts)}
        ),
        status=200,
        mimetype="application/json",
    )
    connection_counter -= 1
    connection.close()
    return response


# Define the post creation functionality
@app.route("/create", methods=("GET", "POST"))
def create():
    global connection_counter
    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]

        if not title:
            flash("Title is required!")
        else:
            connection = get_db_connection()
            connection.execute(
                "INSERT INTO posts (title, content) VALUES (?, ?)", (title, content)
            )
            connection.commit()
            connection.close()
            connection_counter -= 1
            app.logger.info("Articles created %s", title)

            return redirect(url_for("index"))

    return render_template("create.html")


def initialize_logger():
    log_level_str = os.getenv("LOGLEVEL", "DEBUG").upper()

    if log_level_str not in ["DEBUG", "ERROR", "INFO"]:
        log_level_str = (
            "DEBUG"  # Set default log level to DEBUG if invalid level provided
        )

    log_level = getattr(logging, log_level_str)

    handlers = [
        logging.FileHandler("app.log"),  # Writes logs to app.log file
        logging.StreamHandler(sys.stdout),  # Writes logs to stdout
    ]

    logging.basicConfig(
        format="%(levelname)s:%(name)s:%(asctime)s, %(message)s",
        level=log_level,
        handlers=handlers,
    )


# start the application on port 3111
if __name__ == "__main__":
    initialize_logger()
    app.run(host="0.0.0.0", port="3111")

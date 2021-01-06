import json
import sys
from datetime import datetime

from docs import Documents
from docs import SQLDoc
from flask import Flask
from flask import Response
from flask import send_from_directory
from flask_wtf import FlaskForm
from hu import ObjectDict as OD
from jinja2 import ChoiceLoader
from jinja2 import Environment
from jinja2 import FileSystemLoader
from wtforms import StringField
from wtforms.validators import DataRequired

env = Environment(
    loader=ChoiceLoader(
        [FileSystemLoader("/Users/sholden/Projects/Python/blogAlexSteve/web")]
    )
)


app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.config["SECRET_KEY"] = b'_5#y2L"F4Q8z\n\xec]/'

item_vars = OD(
    {
        "heading": "This is the heading - independent of the item title?",
        "when_published": "just now",
        "reading_time": "5 min",
        "trailer_text": "This is the bit that entices you to read on ...",
        "link": "blog-post",
    }
)
post_vars = OD(
    {
        "title": "No title provided in this enviroment",
        "content": """<h3 class="mt-5 mb-3">This is a Heading!</h3>
        <p>It looks like no content was provided for this post by the code that generated it.</p>
        <p>This is test content, to show will look like.  Body text paragraphs not identified as code will be set
        in this font and spacing. Both bold and italic emphasis should work. For some reason it's easier to write code
        than this kind of boilerplate text, but even a coder must suffer for her art. In these trying times one can more
        easily engage a copywriter than to do this kind of writing oneself.</p>\n
        <p>The rest of this page shows the 'state of the art' in HTML production.</p>\n""",
        "when_published": item_vars.when_published,
    }
)

envars = OD({"item": item_vars, "post": post_vars})


@app.route("/")
def hello_world():
    data = dict(
        python=sys.version,
        author={"name": "Steve Holden", "email": "steve@holdenweb.com"},
        date_time=datetime.now().strftime("%A %d, %B %Y %H:%M:%S"),
    )
    return Response(json.dumps(data), mimetype="application/json")


@app.route("/page/<name>")
def show_page(name):
    template = env.get_template(f"{name}.html")
    result = template.render(**envars)
    return result


@app.route("/blog/<id>")
def blog_page_view(id):
    template = env.get_template("blog-post.html")
    envars = OD({"post": load_content(id), "item": item_vars})
    result = template.render(**envars)
    return result


def load_content(id):
    doc = SQLDoc(id)
    record = doc.load()
    return OD(
        {
            "content": record.html,
            "document": OD(json.loads(record.json)),
            "title": record.title,
        }
    )


@app.route("/assets/<path:path>")
def serve_asset(path):
    """Local testing hack - DO NOT USE IN PRODUCTION!"""
    return send_from_directory(
        "/Users/sholden/Projects/Python/blogAlexSteve/web/assets", path
    )


@app.route("/api/v1/articles")
def articles():
    d = Documents()
    return Response(
        json.dumps(list(d.list(fields="id, documentId, title, slug"))),
        mimetype="application/json",
    )


@app.route("/articles/list")
def list_articles():
    data = Documents().list(fields="id, documentID, title, slug")
    tbl_template = env.get_template("list_articles.html")
    content = tbl_template.render(data=data)
    template = env.get_template("blog-post.html")
    envars = OD({"post": {"title": "List of Articles", "content": content}})
    result = template.render(**envars)
    return result


class MyForm(FlaskForm):
    name = StringField("name", validators=[DataRequired()])
    doc_id = StringField("doc_id", validators=[DataRequired()])


@app.route("/forms/test", methods=["GET", "POST"])
def form_test():
    template = env.get_template("test-form.html")
    my_form = MyForm()
    content = template.render(form=my_form)
    print(content)
    template = env.get_template("blog-post.html")
    envars = OD({"post": content, "item": item_vars})  # load_content(id),
    result = template.render(**envars)
    return result


print("Flask app imported")

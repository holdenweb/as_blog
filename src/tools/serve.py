import json
import sys
from datetime import datetime

from docs import WebPage
from flask import Flask
from flask import redirect
from flask import Response
from flask import send_from_directory
from flask_wtf import FlaskForm
from hu import ObjectDict as OD
from jinja2 import ChoiceLoader
from jinja2 import Environment
from jinja2 import FileSystemLoader
from mongoengine import connect
from wtforms import StringField
from wtforms.validators import DataRequired

env = Environment(
    loader=ChoiceLoader(
        [FileSystemLoader("/Users/sholden/Projects/Python/blogAlexSteve/web")]
    )
)

web_db = connect("WebDB")

app = Flask(__name__)

# Set the secret key to some random bytes. Keep this really secret!
app.config["SECRET_KEY"] = b'_5#y2L"F4Q8z\n\xec]/'

item_vars = OD(
    {
        "heading": "This is the heading - independent of the item title?",
        "when_published": "[no publication date]",
        "reading_time": "[no reading time]",
        "trailer_text": "[no trailer text]",
        "link": "[no link]",
    }
)
post_vars = OD(
    {
        "title": "No title provided in this enviroment",
        "content": """<h3 class="mt-5 mb-3">Warning!</h3>
        <p>No content was provided in this environment.</p>\n""",
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


@app.route("/blog/<id>/delete")
def delete_page(id):
    doc = SQLDoc(id)
    doc.delete()
    return redirect("/articles/list")


#
# What's supposed to be the difference between a post and an item?
# Is either of them the same thing as an article? Sloppy work here.
#
@app.route("/blog/<id>")
def blog_page_view(id):
    template = env.get_template("blog-post.html")
    envars = OD({"post": WebPage.objects(documentId=id).to_json(), "item": item_vars})
    result = template.render(**envars)
    return result


def load_content(id):
    doc = SQLDoc(id)
    record = WebPage.objects(document_id=id)
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
    d = WebPage.objects.all()
    return Response(
        json.dumps([(r.id, r.documentId, r.title, r.slug) for r in d]),
        mimetype="application/json",
    )


@app.route("/articles/list")
def list_articles():
    data = WebPage.objects.all()
    data = [(r.id, r.documentId, r.title, r.slug) for r in data]
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

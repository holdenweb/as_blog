import datetime
import json
import sys
from urllib.parse import urlparse

from docs import pull
from docs import WebPage
from flask import flash
from flask import Flask
from flask import redirect
from flask import render_template
from flask import Response
from flask import send_from_directory
from flask import url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from hu import ObjectDict as OD
from jinja2 import ChoiceLoader
from jinja2 import FileSystemLoader
from jinja2 import PackageLoader
from mongoengine import connect
from wtforms import StringField
from wtforms.validators import DataRequired
from wtforms.validators import ValidationError

my_loader = ChoiceLoader(
    [
        FileSystemLoader("/Users/sholden/Projects/Python/blogAlexSteve/web"),
        PackageLoader("flask_bootstrap", package_path="templates", encoding="utf-8"),
    ]
)

web_db = connect("WebDB")

app = Flask(__name__)
app.config["SECRET_KEY"] = b'_5#y2L"F4Q8z\n\xec]/'
app.jinja_loader = my_loader
csrf = CSRFProtect(app)
bstrap = Bootstrap(app)

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
    WebPage.objects(documentId=id).delete()
    return redirect("/articles/list")


#
# What's supposed to be the difference between a post and an item?
# Is either of them the same thing as an article? Sloppy work here.
#
@app.route("/blog/<id>")
def blog_page_view(id):
    template = env.get_template("blog-post.html")
    web_page = WebPage.objects(documentId=id).first()
    envars = OD(
        {
            "post": {
                "title": "There's a Title!",
                "when_published": "Just this minute!",
                "content": web_page.html,
            },
            "item": item_vars,
        }
    )
    result = template.render(**envars)
    return result


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
    envars = OD({"post": {"title": "List of Articles"}})
    result = render_template("list_articles.html", data=data, **envars)
    return result


class MyForm(FlaskForm):
    documentId = StringField(
        "Document ID/URL", validators=[DataRequired()], id="DropTarget1"
    )

    def validate_documentId(form, field):
        """
        This input should either be the 33-character Id of a document,
        or alternatively the URL of a document, which is validated
        by parsing and looking for a 33-character element in the path.
        """
        ID_LENGTH = 33
        if len(field.data) == ID_LENGTH:
            return  # Good enough!
        try:
            up = urlparse(field.data)
        except Exception:
            raise ValidationError("Not a valid document URL or Id [3]")
        if up.scheme != "https":
            raise ValidationError("Not a valid document URL or Id [1]")
        words = up.path.split("/")
        for word in words:
            if len(word) == ID_LENGTH:
                field.data = word
                return
        else:
            raise ValidationError("Not a valid document URL or Id [2]")


@app.route("/document/pull/", methods=["GET", "POST"])
def document_pull():
    form = MyForm()
    if form.validate_on_submit():
        input_string = form.documentId.data
        pull([input_string])
        load([input_string])
        return redirect(url_for(".list_articles"))
    envars = OD(
        {
            "post": {
                "content": "CONTENT",
                "title": "Yes, there IS a title!",
            },
            "item": item_vars,
        }
    )  # load_content(id),
    result = render_template("test-form.html", form=form, **envars)
    return result


if __name__ == "__main__":
    import os

    if "WINGDB_ACTIVE" in os.environ:
        app.debug = False
    app.run(use_reloader=True)
else:
    print("Flask app imported")

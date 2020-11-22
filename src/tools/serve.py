from flask import Flask
from flask import send_from_directory
from hu import ObjectDict as OD
from jinja2 import Environment
from jinja2 import FileSystemLoader


env = Environment(
    loader=FileSystemLoader("/Users/sholden/Projects/Python/blogAlexSteve/web")
)

app = Flask(__name__)

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
        "title": "Well, I Guess Titles Work?!",
        "content": """<h3 class="mt-5 mb-3">This is a Heading!</h3>
        <p>This is what most content paragraphs will look like.  Body text paragraphs not identified as code will be set
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
    return "Hello, World!"


@app.route("/page/<name>")
def show_page(name):
    template = env.get_template(f"{name}.html")
    result = template.render(**envars)
    return result


@app.route("/blog/<id>")
def blog_page_view(id):
    template = env.get_template("blog-post.html")
    with open(f"/Users/sholden/.docs_cache/html/{id}.html") as h_file:
        envars.post.content = h_file.read()
    result = template.render(**envars)
    return result


@app.route("/assets/<path:path>")
def serve_asset(path):
    import os

    print(os.getcwd())
    return send_from_directory(
        "/Users/sholden/Projects/Python/blogAlexSteve/web/assets", path
    )

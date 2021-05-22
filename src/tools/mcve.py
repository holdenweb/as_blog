from flask import Flask
from flask import render_template
from flask_bootstrap import Bootstrap
from jinja2 import ChoiceLoader
from jinja2 import Environment
from jinja2 import FileSystemLoader
from jinja2 import PackageLoader

template_file = """\
{% extends "bootstrap/base.html" %}
{% block title %}This is an example page{% endblock %}

{% block navbar %}
<div class="navbar navbar-fixed-top">
  <!-- ... -->
</div>
{% endblock %}

{% block content %}
  <h1>Hello, Bootstrap</h1>
{% endblock %}
"""

with open("dammit.html", "w") as tf:
    tf.write(template_file)

env = Environment(
    loader=ChoiceLoader(
        [
            FileSystemLoader("."),
            PackageLoader(
                "flask_bootstrap", package_path="templates", encoding="utf-8"
            ),
        ]
    )
)

app = Flask(__name__, template_folder="/tmp")
app.config["SECRET_KEY"] = b'_5#y2L"F4Q8z\n\xec]/'
bstrap = Bootstrap(app)


@app.route("/")
def dammit():
    #    template = env.get_template('dammit.html')
    return render_template("dammit.html")


if __name__ == "__main__":
    import os

    if "WINGDB_ACTIVE" in os.environ:
        app.debug = False
    app.run(use_reloader=True)
else:
    print("Flask app imported")

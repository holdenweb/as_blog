import json
import os
import pickle
import sqlite3 as db
import sys

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from hu import ObjectDict as OD
from slugify import slugify

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

DEBUG_FEATURE_FLAGS = {"final"}
CACHE_DIRECTORY = os.path.expanduser("~/.docs_cache")


def debug(debug_class, *arg, **kw):
    if debug_class in DEBUG_FEATURE_FLAGS or "all" in DEBUG_FEATURE_FLAGS:
        print(*arg, **kw)


class Doc:
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.cached_path = f"{CACHE_DIRECTORY}/{document_id}.json"

    def cached(self):
        return os.path.exists(self.cached_path)

    def pull(self):
        """
        Retrieve the subject document in its current form from Docs.
        """
        creds = authenticate()
        service = build("docs", "v1", credentials=creds)

        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=self.document_id).execute()
        self.save(OD(document))

    def save(self, document):
        with open(self.cached_path, "w") as file_pointer:
            print("Writing to cache", file=sys.stderr)
            json.dump(document, file_pointer)


def open_db():
    if not open_db.conn:
        open_db.conn = db.connect("docs.db")
        open_db.curs = open_db.conn.cursor()
        open_db.curs.execute(
            """
            CREATE TABLE IF NOT EXISTS documents (
                id integer primary key autoincrement,
                documentId varchar,
                json varchar,
                html varchar,
                title varchar,
                slug varchar,
                status varchar,
                when_published datetime
            )"""
        )
    return open_db.conn, open_db.curs


open_db.conn = open_db.curs = None


class Documents:
    def __init__(self):
        self.conn, self.curs = open_db()

    def list(self, order_by=None, fields="*"):
        sql = f"""SELECT {fields} FROM documents"""
        if order_by:
            sql = f"{sql} ORDER BY {order_by}"
        self.curs.execute(sql)
        yield from self.curs.fetchall()


class SQLDoc(Doc):
    field_list = "id, documentId, json, html, title, slug, status"
    fields = field_list.split(", ")

    def __init__(self, document_id):
        super().__init__(document_id)
        self.open_db()

    def open_db(self):
        self.conn, self.curs = open_db()

    def cached(self):
        self.curs.execute(
            """SELECT count(*) FROM documents as d WHERE d.documentId=?""",
            (self.document_id,),
        )
        result = self.curs.fetchall()
        return result == [(1,)]

    def delete(self):
        self.curs.execute(
            """DELETE FROM documents as d WHERE d.documentId=?""", (self.document_id,)
        )
        self.conn.commit()

    def load(self) -> OD:
        self.curs.execute(
            f"""SELECT {self.field_list} FROM documents WHERE documentId=?""",
            (self.document_id,),
        )
        return OD(dict(zip(self.fields, self.curs.fetchone())))

    def save(self, document):
        self.curs.execute(
            f"""SELECT {self.field_list} FROM documents WHERE documentId=?""",
            (document.documentId,),
        )
        rows = self.curs.fetchall()
        title = (
            document.title
            if "title" in document and document.title
            else "++ NO TITLE ++"
        )
        slug = slugify(title)
        if not rows:
            self.curs.execute(
                """INSERT INTO documents (documentId, title, json, slug) VALUES (?, ?, ?, ?)""",
                (self.document_id, title, json.dumps(document), slug),
            )
        else:
            self.curs.execute(
                """UPDATE documents SET title=?, json=?, slug=? WHERE documentId=?""",
                (document.title, json.dumps(document), slug, document.documentId),
            )
        self.conn.commit()

    def set_html(self, html, title="** NO TITLE **"):
        self.curs.execute(
            """UPDATE documents SET html=?, title=? WHERE documentId=?""",
            (html, title, self.document_id),
        )
        self.conn.commit()


def authenticate():
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return creds


def main(args=sys.argv):
    print("ARGS:", args)
    print("Pulling", sys.argv[1])
    doc_file = SQLDoc(document_id=args[1])
    doc_file.pull()


if __name__ == "__main__":
    main()

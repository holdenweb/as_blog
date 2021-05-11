import json
import os
import pickle
import sqlite3 as db
import sys
from typing import Optional

from dataclasses import dataclass
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from hu import ObjectDict as OD
from mongoengine import connect
from mongoengine import DictField
from mongoengine import disconnect
from mongoengine import Document
from mongoengine import EmbeddedDocument
from mongoengine import StringField
from slugify import slugify

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

DEBUG_FEATURE_FLAGS = {"final"}
CACHE_DIRECTORY = os.path.expanduser("~/.docs_cache")

#
# Should we connect to the MongoDB on import?     🤷
#


def debug(debug_class, *arg, **kw):
    if debug_class in DEBUG_FEATURE_FLAGS or "all" in DEBUG_FEATURE_FLAGS:
        print(*arg, **kw)


class WebPage(Document):
    documentId: str = StringField(required=True, primary_key=True)
    json: str = DictField(required=False)
    html: str = StringField(required=False)
    title: str = StringField(required=False)
    slug: str = StringField(required=False)
    status: str = StringField(required=False)

    #    field_list = "id, documentId, json, html, title, slug, status"

    @property
    def cached_path(self):
        return f"{CACHE_DIRECTORY}/{self.documentId}.json"

    def cached(self):
        return os.path.exists(self.cached_path)


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


def pull(args=sys.argv):
    web_db = connect("WebDB")
    documentId = args[1]
    print("Pulling", documentId)
    creds = authenticate()
    service = build("docs", "v1", credentials=creds)

    # Retrieve the document's contents from the Docs service.
    document = service.documents().get(documentId=documentId).execute()
    document = OD(document)
    title = (
        document.title
        if "title" in document and document.title
        else "+++ NO TITLE! +++"
    )
    slug = slugify(title)
    record = WebPage(documentId=documentId, title=title, json=document, slug=slug)
    record.save()


# if __name__ == "__main__":
# main()

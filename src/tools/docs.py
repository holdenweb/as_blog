import json
import os
import pickle
import sys

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

# If modifying these scopes, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/documents.readonly"]

DEBUG_FEATURE_FLAGS = {"final"}
CACHE_DIRECTORY = os.path.expanduser("~/.docs_cache")


def debug(debug_class, *arg, **kw):
    if debug_class in DEBUG_FEATURE_FLAGS or "all" in DEBUG_FEATURE_FLAGS:
        print(*arg, **kw)


class DocsFile:
    def __init__(self, document_id: str):
        self.document_id = document_id
        self.cached_path = f"{CACHE_DIRECTORY}/{document_id}.json"

    def cached(self):
        return os.path.exists(self.cached_path)

    def open(self):
        if not self.cached():  # Could check mod date and commit new version?
            print("Cacheing file", file=sys.stderr)
            self.retrieve()
        return open(self.cached_path)

    def retrieve(self):
        """
        Shows basic usage of the Docs API.
        """
        creds = authenticate()
        service = build("docs", "v1", credentials=creds)

        # Retrieve the documents contents from the Docs service.
        document = service.documents().get(documentId=self.document_id).execute()
        with open(self.cached_path, "w") as file_pointer:
            print("Writing to cache", file=sys.stderr)
            json.dump(document, file_pointer)


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
    DocsFile(document_id=args[1]).retrieve()


if __name__ == "__main__":
    main()

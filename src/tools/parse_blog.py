import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

# The ID of a sample document.
DOCUMENT_ID = '1jALRWW76qjrcl12e-umDm-ZbGlm8HcGuaA2jGdl1Zro'

class MyDoc():
    """
    This is a general framework to handle Google documents, allowing their
    processing into blog entries in a relatively automated way.
    """
    def parse(self, parseable, container='document', containing_part_name='Unidentifed', part_names=None):
        """
        General parser for any parseable object_dict, whose parts are handled in the
        order their names appear in part_names. At present unrecognised part names
        are reported and skipped from the parse. This may become tedious as we descend
        down the heirachy in top-down fashion.
        """
        print("Parsing", ", ".join(part_names), "in", containing_part_name)
        for part_name in part_names:
            if not container or part_name in container:
                print(f"Found {part_name}")
                method = getattr(self, f"parse_{part_name}", self.parse_unrecognised_part_name)
                part = parseable.get(part_name)
                print("Attempting to handle", part_name)
                method(parseable, part_name, part, containing_part_name=containing_part_name)

    def parse_body(self, content, part_name, body, containing_part_name="document"):
        part_names = ('content', )
        return self.parse(body, container=content, part_names=part_names, containing_part_name='body')

    def parse_content(self, body, elements, containing_part_name="body"):
        """
        elements is a sequence of structuralElement objects, some of which should
        be parsed to access publishable content.
        """
        print("Content elements count:", len(elements))
        for element in elements:
            self.parse_structural_element(body, 'structuralElement', element, containing_part_name="content")

    def parse_document(self, document, containing_part_name="document"):
        part_names = ('title', 'body', 'footnotes', 'documentStyle', 'namedStyles',
                      'revisionId', 'suggestionsViewMode', 'documentId')
        return self.parse(document, part_names=part_names, containing_part_name=containing_part_name)

    def parse_sectionBreak(self, paragraph, part, containing_part_name= None):
        print("sectionBreak:", part)

    def parse_structural_element(self, container, part, containing_part_name=None):
        part_names = ('sectionBreak', 'tableOfContents', 'table', 'paragraph')
        return self.parse(container, element, 'structuralElement', part_names=part_names)

    def parse_title(self, document, part_name, title, containing_part_name='document'):
        self.title = document.get('title')

    def parse_unrecognised_part_name(self, container, part_name, part, containing_part_name="Not provided"):
        print(f"Cannot handle {part_name} in {containing_part_name}")


def main():
    """Shows basic usage of the Docs API.
    Begins attempt to create parser allowing transformation
    into chosen publishing format.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('docs', 'v1', credentials=creds)

    # Retrieve the documents contents from the Docs service.
    document = service.documents().get(documentId=DOCUMENT_ID).execute()
    parser = MyDoc()
    parser.parse_document(document)

    print(f'The title of document {DOCUMENT_ID} is: {document.get("title")!r}')
    print(f'  The parser says:', parser.title)


if __name__ == '__main__':
    main()

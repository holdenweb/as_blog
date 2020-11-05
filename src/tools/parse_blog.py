import json
import pickle
import os.path

from styles import StyleStack
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/documents.readonly']

#
# Next steps: add paragraphStyle handler to action formatting
# changes, and paragraphElement.footnoteReference handler to
# ensure that the footnotes are included.
#
# The ID of a sample document.
DOCUMENT_ID = '1jALRWW76qjrcl12e-umDm-ZbGlm8HcGuaA2jGdl1Zro'

DEBUG_FEATURE_FLAGS = {"tr", "ts", "ps"}

def debug(debug_class, *arg, **kw):
    if debug_class in DEBUG_FEATURE_FLAGS:
        print(*arg, **kw)

class MyDoc():
    """
    This is a general framework to handle Google documents, allowing their
    processing into blog entries in a relatively automated way.
    """
    def __init__(self):
        self.content = []
        self.p_styles = StyleStack('paragraph')
        self.t_styles = StyleStack('text')

    def parse(self, element, element_name, item_names, ancestors):
        """
        Parses the given document element by recursively parsing
        the content of each item.
        """
        debug("parse", f"Parsing", ".".join(ancestors+[element_name]))
        for item_name in item_names:
            if item_name in element:
                method = getattr(self, f"parse_{item_name}", self.parse_unrecognised_part_name)
                item = element[item_name]
                debug("parse", "Handling", ".".join(ancestors+[element_name, item_name]))
                method(element=item, element_name=item_name, ancestors=ancestors+[element_name])
        debug("parse", f"Parse of", ".".join(ancestors+[element_name]), 'complete')

    def parse_body(self, element, element_name, ancestors):
        item_names = ('content', )
        return self.parse(element, element_name='content', item_names=item_names, ancestors=ancestors)

    def parse_content(self, element, element_name, ancestors):
        """
        elements is a sequence of structuralElement objects, some of which should
        be parsed to access publishable content.
        """
        debug("content", "Content elements count:", len(element))
        for item in element:
            self.parse_structuralElement(item, 'structuralElement', ancestors=ancestors)

    def parse_document(self, element, ancestors=[]):
        item_names = ('title', 'body', 'footnotes', 'documentStyle', 'namedStyles',
                      'revisionId', 'suggestionsViewMode', 'documentId')
        return self.parse(element=element, element_name="document", item_names=item_names, ancestors=ancestors)

    def parse_documentId(self, element, element_name, ancestors):
        self.documentId = element

    def parse_elements(self, element, element_name, ancestors):
        for item in element:
            self.parse_element(item, 'paragraphElement', ancestors)

    def parse_element(self, element, element_name, ancestors):
        item_names = ('textRun', 'autoText', 'pageBreak', 'columnBreak', 'footnoteReference', 'horizontalRule', 'equation', 'inlineOPbnjectElement')
        debug("element", f"Range: {element['startIndex']}-{element['endIndex']}")
        self.parse(element, element_name, item_names, ancestors)

    def parse_paragraph(self, element, element_name, ancestors):
        item_names = ('paragraphStyle', 'bullet', 'elements')
        return self.parse(element, element_name, item_names, ancestors)

    def parse_paragraphStyle(self, element, element_name, ancestors):
        self.p_styles.push(element)
        debug("ps", f"Pushed {element_name} {element!r}")
        debug("ps", "Style now:")
        for key, value in sorted(self.p_styles.to_dict().items()):
            if value:
                debug("ps", f":::{key!r}: {value!r}")
        assert self.p_styles.pop() == element

    def parse_textStyle(self, element, element_name, ancestors):
        self.t_styles.push(element)
        debug("ts", f"Pushed {element_name} {element!r}")
        debug("ts", "Style now:")
        for key, value in sorted(self.p_styles.to_dict().items()):
            debug("ts", f"...{key!r}: {value!r}")
        assert self.t_styles.pop() == element

    def parse_sectionBreak(self, element, element_name, ancestors):
        debug("sb", "sectionBreak:", element)

    def parse_structuralElement(self, element, element_name, ancestors):
        part_names = ('sectionBreak', 'tableOfContents', 'table', 'paragraph')
        return self.parse(element, element_name='structuralElement', item_names=part_names, ancestors=ancestors)

    def parse_textRun(self, element, element_name, ancestors):
        style = element.get('textStyle', "")
        self.content.append((style, element['content']))
        debug("tr", "tStyle:", style if style else "UNSTYLED CONTENT")
        debug("tr", element['content'], end="|")

    def parse_title(self, element, element_name, ancestors):
        self.title = element
        debug("t", ".".join(ancestors+[element_name]), "is", element)

    def parse_unrecognised_part_name(self, element, element_name, ancestors):
        debug("upn", "Didn't handle", '.'.join(ancestors+[element_name]))


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
    with open(f"{DOCUMENT_ID}.json", "w") as fp:
        json.dump(document, fp)
    parser = MyDoc()
    parser.parse_document(element=document, ancestors=[])

    debug("main", f'The title of document {DOCUMENT_ID} is: {document.get("title")!r}')
    debug("main", f'  The parser says:', parser.title)
    debug("main", f'                  ', parser.documentId)

    from itertools import groupby
    current_style = None
    ci = iter(parser.content)
    for style, para in ci:
        if style != current_style:
            current_style = style
            debug(f"\n:::::::: Style: {style} ::::::::")
        debug(para, sep="", end='')



if __name__ == '__main__':
    main()

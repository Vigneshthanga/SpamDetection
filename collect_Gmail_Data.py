from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from apiclient import errors
import base64
import email
import mailparser
from string import punctuation
import string
import re
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer


# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def clean_text(text):
    # remove urls
    text = re.sub(r'http\S+', ' ', text)

    # replace email address with word emailaddress
    text = re.sub('[^\s]+@[^\s]+', ' ', text)

    # remove html tags
    text = re.sub('<[^<>]+>', ' ', text)
    # remove new lines
    text = text.replace('\\n', ' ')
    text = text.replace('\\r', ' ')
    text = text.replace('\\t', ' ')
    # remove punctuations
    text = text.translate(str.maketrans(' ', ' ', string.punctuation))
    text = text.lower()
    return text


def GetMessage(service, user_id, msg_id):
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id).execute()

    return message
  except errors.HttpError:
    print('An error occurred: ')


def GetMimeMessage(service, user_id, msg_id, idx):
  try:
    message = service.users().messages().get(userId=user_id, id=msg_id,
                                             format='raw').execute()

    msg_str = base64.urlsafe_b64decode(message['raw'].encode('ASCII'))
    mail = mailparser.parse_from_bytes(msg_str)

    msg_str = str(mail.text_plain)
    msg_str = msg_str.strip("")
    msg_str = clean_text(msg_str)

  except errors.HttpError:
    print('An error occurred:')

  try:
    met = service.users().messages().get(userId=user_id, id=msg_id, format='metadata').execute()

    pay = met['payload']
    head = pay['headers']
    sub=""
    for h in head:
      if (h['name'] == 'Subject'):
        sub = "Subject: "+str(h['value'])
  except errors.HttpError:
    print('An error occurred:')
  filename = "./ham/email"
  file_extension = ".txt"
  new_fname = "{}-{}{}".format(filename, idx, file_extension)
  f= open(new_fname,"w+")
  f.write(sub+"\n")
  f.write(msg_str)
  f.close()

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
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

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().labels().list(userId='me').execute()
    labels = results.get('labels', [])

    if not labels:
        print('No labels found.')
    else:
        print('Labels:')
        for label in labels:
            print(label['name'])
    path = "./ham"
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed" % path)
    else:
        print ("Successfully created the directory %s " % path)

    messages = []
    messages = ListMessagesMatchingQuery(service, 'me', 'in:inbox')
    idx = 0
    for message in messages:
      GetMimeMessage(service, 'me', message['id'], idx)
      idx+=1


  try:
    response = service.users().messages().list(userId=user_id,
                                               q=query).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id, q=query,
                                         pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError:
    print("An error occurred")


def ListMessagesWithLabels(service, user_id, label_ids=[]):

  try:
    response = service.users().messages().list(userId=user_id,
                                               labelIds=label_ids).execute()
    messages = []
    if 'messages' in response:
      messages.extend(response['messages'])

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = service.users().messages().list(userId=user_id,
                                                 labelIds=label_ids,
                                                 pageToken=page_token).execute()
      messages.extend(response['messages'])

    return messages
  except errors.HttpError:
    print("An error occurred")

if __name__ == '__main__':
    main()

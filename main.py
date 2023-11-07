import json
import os
import pandas as pd
import requests
import datetime

# Set the API version
api = '/rest/api/2'


# Utils - simple logging
def log(message, type="INFO"):
    with open('logs/logs.txt', 'a') as appendfile:
        appendfile.write(f'{datetime.datetime.now()} - {type} - ' + message + '\n')


# Import the Configuration
with open('config.json') as configfile:
    config = json.load(configfile)
    sc = config['source']
    tc = config['target']


class Jira:
    headers = {'Accept': 'application/json'}
    params = {'notifyUsers': False}

    uploaded = {}  # issuekey : [att names]

    def __init__(self, creds, url):
        self.creds = creds
        self.url = url

    def get(self, url, params={}):
        return requests.get(url, params=params, headers=self.headers, auth=self.creds)

    def get_attachments_per_issue(self, key):
        try:
            return self.get(self.url + api + f'/issue/{key}?fields=attachment', params={}).json()['fields'][
                'attachment']
        except:
            return []

    def download_attachments(self, issuekey):
        print(f' :: Downloading attachments for {issuekey}')
        # check if the issuekey was not iterated before
        if issuekey not in os.listdir('attachments'):
            filenames = []
            attachments = self.get_attachments_per_issue(issuekey)

            if len(attachments) > 0:

                if not os.path.exists(f'attachments/{issuekey}'):
                    os.mkdir(f'attachments/{issuekey}')

                for att in attachments:
                    get_attachment_content_url = self.url + f'/rest/api/2/attachment/content/{att["id"]}'
                    attachment_data = self.get(get_attachment_content_url, {}).content
                    with open(f'attachments/{issuekey}/' + att['filename'], 'wb') as file:
                        file.write(attachment_data)
                        filenames.append(att['filename'])
                        log(f'Downloaded attachment {att["filename"]} for issue {issuekey}')

            print(filenames)
            return filenames

        else:
            print(issuekey, 'has no attachments')

    def upload_attachment(self, issuekey, filename):

        headers = {
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check"
        }

        if issuekey not in self.uploaded.keys():
            self.uploaded[issuekey] = []

        if filename not in self.uploaded[issuekey]:
            r = requests.post(
                self.url + api + f'/issue/{issuekey}/attachments',
                headers=headers,
                auth=self.creds,
                files={
                    "file": (filename.replace(f'attachments/{issuekey}/', ''), open(filename, "rb"), "application-type")
                }
            )

            if r.status_code == 200:
                log(f'Attachment {filename} uploaded to {issuekey}')
            else:
                log(f'Problem uploading attachment {filename} to {issuekey} - {r.status_code} / {r.content}')

            # To avoid duplicates
            self.uploaded[issuekey].append(filename)


source = Jira((sc['email'], sc['token']), sc['url'])
target = Jira((tc['email'], tc['token']), tc['url'])

issuemapping = pd.read_csv('src/att-issue-mapping.csv')

for _, row in issuemapping.iterrows():

    source_issue_key = row['source_issue_key']
    target_issue_key = row['target_issue_key']

    filenames = source.download_attachments(source_issue_key)

    for filename in filenames:
        target.upload_attachment(target_issue_key, f'attachments/{source_issue_key}/{filename}')

    print(f"Uploaded attachments from source ({source}) to target ({target}).")

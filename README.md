# Migrate attachments from an instance to another

Requirements
`pip install -r requirements.txt`

The only required libraries here are pandas and requests.

1. open config.json and add your credentials from source/target and url.
2. edit the file under src/att-issue-mapping.csv and add your issue mappings (it works for either issue ids or issue keys). 
3. execute main.py

ps. The mapping can be interpreted as "the attachments from source will go to the target issuekey".
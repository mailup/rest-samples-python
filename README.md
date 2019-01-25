Python Rest API Client 
================
Python REST API integration/implementation samples

Requirements
------------------------
* Python 3 and PIP installed
* A valid MailUp account ( trial accounts allowed )
* API application keys ( required only for final deployments )

notes : 
* For further API information, please visit [MailUp REST API Help] [1] 
* For MailUp trial account activation please go to [MailUp web site] [2] 

  [1]: http://help.mailup.com/display/mailupapi/REST+API        "MailUp REST API Help"
  [2]: http://www.mailup.com/p/pc/mailup-free-trial-d44.htm        "MailUp web site"

How to run this project
------------------------
* pip install -r ./requirements.txt
* python3 ./app.py
  
Samples overview 
------------------------
This project encloses a short list of pre definied samples describing some of the most common processes within MailUp.

* Sample 1   - Importing recipients into a new group
* Sample 2   - Unsubscribing a recipient from a group
* Sample 3   - Updating a recipient information
* Sample 4   - Creating a message from a custom template ( at least one template must be saved on list 1 )
* Sample 5   - Building a message with images and attachments
* Sample 6   - Tagging an email message
* Sample 7   - Sending an email message
* Sample 8   - Displaying statistics with regards to message created in sample 4 or 5 and/or sent out in sample 7

Debugging tool 
------------------------


Notes
------------------------
We highly recommend to make use of the application API keys for test purposes and when running on staging environments only.
If the code enclosed in the samples should ever run in production environments instead, we'd love you to get your personal free API keys.

If you're interested to claim your API keys, please read more at the page [MailUp REST API Keys and endpoints] [3] 

  [3]: http://help.mailup.com/display/mailupapi/All+API+Keys+and+Endpoints+in+one+page        "MailUp REST API Keys and endpoints"

Revision history
------------------------

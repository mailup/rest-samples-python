import pycurl
import json
import base64
import time
import requests
from urllib.parse import quote_plus
from io import BytesIO
from flask import jsonify


class MailUpException(Exception):
    def __init__(self, code=None, error=None):
        super().__init__(error)
        self.code = code
        self.error = error


class MailUpClient:
    def __init__(self, config):
        self.list_id = config.get('ID_LIST', 1)
        self.logon_endpoint = config.get('LOGON_URI', None)
        self.authorization_endpoint = config.get('AUTH_URI', None)
        self.token_endpoint = config.get('TOKEN_URI', None)
        self.console_endpoint = config.get('CONSOLE_URI', None)
        self.mail_statistics_endpoint = config.get('MAIL_STATS_URI', None)

        self.client_id = config.get('CLIENT_ID', None)
        self.client_secret = config.get('CLIENT_SECRET', None)
        self.callback_uri = config.get('CALLBACK_URI', None)

        self.error_url = None

        self.access_token = None
        self.refresh_token = None
        self.token_time = 0

    def clear_tokens(self):
        self.access_token = None
        self.refresh_token = None
        self.token_time = 0

    def save_token(self, result):
        self.access_token = result.get('access_token', None)
        self.refresh_token = result.get('refresh_token', None)
        self.token_time = time.time() + result.get('expires_in', 0)

    def load_token(self, cookies):
        self.access_token = cookies.get('access_token', None)
        self.refresh_token = cookies.get('refresh_token', None)
        self.token_time = cookies.get('token_time', 0)

    def get_token_time(self):
        return max(0, int(float(self.token_time) - time.time()))

    def get_logon_uri(self):
        return f'{self.logon_endpoint}?client_id={self.client_id}' \
               f'&client_secret={self.client_secret}&response_type=code' \
               f'&redirect_uri={self.callback_uri}'

    def logon(self):
        response = jsonify()
        response.headers['Location'] = self.get_logon_uri()
        return response, 302

    def retrieve_access_token_with_code(self, code):
        url = f'{self.token_endpoint}?code={code}&grant_type=authorization_code'
        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.SSL_VERIFYPEER, False)
        c.setopt(c.SSL_VERIFYHOST, False)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        code = c.getinfo(c.HTTP_CODE)
        body = buffer.getvalue()
        c.close()

        if code != 200 and code != 302:
            raise MailUpException(code=code, error="Authorization error")

        result = json.loads(body)

        self.save_token(result)

    def retrieve_access_token(self, login, password):
        url = self.token_endpoint

        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.SSL_VERIFYPEER, False)
        c.setopt(c.SSL_VERIFYHOST, False)
        c.setopt(c.POST, 1)

        body = f'grant_type=password&username={quote_plus(login)}' \
               f'&password={quote_plus(password)}' \
               f'&client_id={self.client_id}&client_secret={self.client_secret}'

        headers = dict()
        headers['Content-length'] = len(body)
        headers["Accept"] = 'application/json'
        headers["Authorization"] = 'Basic ' + \
                                   base64.b64encode(
                                       (self.client_id + ':' + self.client_secret).encode()
                                   ).decode('ascii')
        c.setopt(c.HTTPHEADER, [f'{x}: {headers[x]}' for x in headers.keys()])

        c.setopt(c.POSTFIELDS, body)
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        code = c.getinfo(c.HTTP_CODE)
        body = buffer.getvalue()
        c.close()

        if code != 200 and code != 302:
            raise MailUpException(code=code, error="Authorization error")

        result = json.loads(body)

        self.save_token(result)

    def refresh_access_token(self):
        url = self.token_endpoint

        body = f'client_id={self.client_id}&client_secret={self.client_secret}' \
               f'&refresh_token={self.refresh_token}&grant_type=refresh_token'

        buffer = BytesIO()
        c = pycurl.Curl()
        c.setopt(c.URL, url)
        c.setopt(c.SSL_VERIFYPEER, False)
        c.setopt(c.SSL_VERIFYHOST, False)
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, body)
        c.setopt(c.HTTPHEADER,
                 ["Content-type: application/x-www-form-urlencoded",
                  f"Content-length: {len(body)}"])

        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        code = c.getinfo(c.HTTP_CODE)
        body = buffer.getvalue()
        c.close()

        if code != 200 and code != 302:
            raise MailUpException(code=code, error="Authorization error")

        result = json.loads(body)

        self.save_token(result)

    def call_method(self, url, method, body='', content_type='JSON', refresh=True):
        ctype = 'application/xml' if content_type == 'XML' else 'application/json'
        buffer = BytesIO()
        c = pycurl.Curl()

        c.setopt(c.URL, url)
        c.setopt(c.WRITEDATA, buffer)
        c.setopt(c.SSL_VERIFYPEER, False)
        c.setopt(c.SSL_VERIFYHOST, False)
        # c.setopt(c.VERBOSE, 1)
        if method == 'POST':
            c.setopt(c.POST, 1)
            c.setopt(c.POSTFIELDS, body)
            c.setopt(c.HTTPHEADER, [
                f'Content-type: {ctype}',
                f'Content-length: {len(body)}',
                f'Accept: {ctype}',
                f'Authorization: Bearer {self.access_token}',
                ]
            )
        elif method == 'PUT':
            c.setopt(c.CUSTOMREQUEST, method)
            c.setopt(c.POSTFIELDS, body)
            c.setopt(c.HTTPHEADER, [
                f'Content-type: {ctype}',
                f'Content-length: {len(body)}',
                f'Accept: {ctype}',
                f'Authorization: Bearer {self.access_token}',
                ]
            )
        elif method == 'DELETE':
            c.setopt(c.CUSTOMREQUEST, method)
            c.setopt(c.HTTPHEADER, [
                f'Content-type: {ctype}',
                'Content-length: 0',
                f'Accept: {ctype}',
                f'Authorization: Bearer {self.access_token}',
                ]
            )
        else:
            c.setopt(c.HTTPHEADER, [
                f'Content-type: {ctype}',
                'Content-length: 0',
                f'Accept: {ctype}',
                f'Authorization: Bearer {self.access_token}',
                ]
            )
        c.setopt(c.WRITEDATA, buffer)
        c.perform()
        code = c.getinfo(c.HTTP_CODE)
        body = buffer.getvalue()
        c.close()

        result = None

        if body:
            result = json.loads(body) \
                if content_type == 'JSON' else body.decode("utf-8")

        if code == 401 and refresh:
            self.refresh_access_token()
            return self.call_method(url, method, body, content_type, False)
        elif code == 401 and not refresh:
            raise MailUpException(code=code, error="Authorization error")
        elif code != 200 and code != 302:
            raise MailUpException(code=code, error="Unknown error")

        return result

    def get_result(self, method, content_type, body, env, endpoint, text):
        result = dict()
        url = self.console_endpoint \
            if env == 'Console' else self.mail_statistics_endpoint
        url = url + endpoint
        self.error_url = url
        result['res_body'] = self.call_method(
            method=method,
            content_type=content_type,
            url=url,
            body=body,
        )
        result['url'] = env
        result['content_type'] = content_type
        result['method'] = method
        result['endpoint'] = endpoint
        result['text'] = text
        result['req_body'] = body

        return result

    def get_example_group_id(self):
        result = self.get_result(
            method='GET',
            content_type='JSON',
            body=None,
            env='Console',
            endpoint=f'/Console/List/{self.list_id}/Groups',
            text=f'Given a default list id (use idList = {self.list_id}), request '
                 f'for user visible groups',
        )

        group_id = None
        items = result['res_body'].get('Items', None)
        if items:
            for item in items:
                if item.get('Name', '') == 'test import':
                    group_id = item.get('idGroup', None)

        return result, group_id

    def example_1(self):
        results = []

        result, group_id = self.get_example_group_id()

        results.append(result)

        result = self.get_result(
            method='GET',
            content_type='JSON',
            body=None,
            env='Console',
            endpoint='/Console/Recipient/DynamicFields',
            text='Request for dynamic fields to map recipient name and surname',
        )

        results.append(result)

        if group_id:
            result = self.get_result(
                method='POST',
                content_type='JSON',
                body=json.dumps(
                    [
                        {
                            "Email": "test@test.test",
                            "Fields": [
                                {
                                    "Description": "String description",
                                    "Id": 1,
                                    "Value": "String value",
                                }
                            ],
                            "MobileNumber": "",
                            "MobilePrefix": "",
                            "Name": "John Smith",
                        }
                    ]
                ),
                env='Console',
                endpoint=f'/Console/Group/{group_id}/Recipients',
                text='Import recipients to group',
            )

            results.append(result)

            import_id = result['res_body']

            if import_id:
                result = self.get_result(
                    method='GET',
                    content_type='JSON',
                    body=None,
                    env='Console',
                    endpoint=f'/Console/Import/{import_id}',
                    text='Check the import result',
                )

                results.append(result)

        return results

    def example_2(self):
        results = []

        result, group_id = self.get_example_group_id()

        results.append(result)

        if group_id:
            result = self.get_result(
                method='GET',
                content_type='JSON',
                body=None,
                env='Console',
                endpoint=f'/Console/Group/{group_id}/Recipients',
                text='Request for recipient in a group',
            )

            results.append(result)

            items = result['res_body'].get('Items', None)
            if items:
                first_item = next(iter(items), None)
                if first_item:
                    recipient_id = first_item['idRecipient']
                    if recipient_id:
                        result = self.get_result(
                            method='DELETE',
                            content_type='JSON',
                            body=None,
                            env='Console',
                            endpoint=f'/Console/Group/{group_id}/Unsubscribe/{recipient_id}',
                            text='Pick up a recipient and unsubscribe it',
                        )

                        results.append(result)

        return results

    def example_3(self):
        results = []

        result = self.get_result(
            method='GET',
            content_type='JSON',
            body=None,
            env='Console',
            endpoint=f'/Console/List/{self.list_id}/Recipients/Subscribed',
            text='Request for existing subscribed recipients',
        )

        results.append(result)

        items = result['res_body'].get('Items', None)
        if items:
            items[0]['Fields'][0] = {"Description": "", "Id": 1, "Value": "Updated value"}

            result = self.get_result(
                method='PUT',
                content_type='JSON',
                body=json.dumps(items[0]),
                env='Console',
                endpoint='/Console/Recipient/Detail',
                text='Update the modified recipient',
            )

            results.append(result)

        return results

    def example_4(self):
        results = []

        result = self.get_result(
            method='GET',
            content_type='JSON',
            body=None,
            env='Console',
            endpoint=f'/Console/List/{self.list_id}/Templates',
            text='Get the available template list',
        )

        results.append(result)

        template_id = 1

        items = result['res_body'].get('Items', None)
        if items:
            template_id = items[1]['Id']

        result = self.get_result(
            method='POST',
            content_type='JSON',
            body='',
            env='Console',
            endpoint=f'/Console/List/{self.list_id}/Email/Template/{template_id}',
            text='Create the new message',
        )

        results.append(result)

        email_id = result['res_body'].get('idMessage', None)

        if email_id:
            result = self.get_result(
                method='GET',
                content_type='JSON',
                body=None,
                env='Console',
                endpoint=f'/Console/List/{self.list_id}/Emails',
                text='Request for messages list',
            )

            results.append(result)

        return results

    def example_5(self):
        results = []

        url = 'https://www.mailup.it/risorse/logo/512x512.png'
        r = requests.get(url)

        img = base64.b64encode(r.content).decode('ascii')

        body = '{"Base64Data": "' + img + '","Name": "Avatar"}'

        result = self.get_result(
            method='POST',
            content_type='JSON',
            body=body,
            env='Console',
            endpoint=f'/Console/List/{self.list_id}/Images',
            text='Upload an image',
        )

        results.append(result)

        result = self.get_result(
            method='GET',
            content_type='JSON',
            body=None,
            env='Console',
            endpoint='/Console/Images',
            text='Get the images available',
        )

        results.append(result)

        img_src = ''

        if len(result['res_body']) > 0:
            img_src = result['res_body'][0]

        if img_src:
            message = f'<html><body><p>Hello</p><img src="{img_src}" /></body></html>'

            email = {
                "Subject": "Test Message Python",
                "idList": self.list_id,
                "Content": message,
                "Embed": True,
                "IsConfirmation": True,
                "Fields": [],
                "Notes": "Some notes",
                "Tags": [],
                "TrackingInfo": {
                    "CustomParams": "",
                    "Enabled": True,
                    "Protocols": ['http'],
                }
            }

            result = self.get_result(
                method='POST',
                content_type='JSON',
                body=json.dumps(email),
                env='Console',
                endpoint=f'/Console/List/{self.list_id}/Email',
                text='Create and save "hello" message',
            )

            results.append(result)

            email_id = result['res_body'].get('idMessage', None)

            if email_id:
                attachment = "QmFzZSA2NCBTdHJlYW0=";
                body = {
                    "Base64Data": attachment,
                    "Name": "TestFile.txt",
                    "Slot": 1,
                    "idList": 1,
                    "idMessage": email_id,
                }

                result = self.get_result(
                    method='POST',
                    content_type='JSON',
                    body=json.dumps(body),
                    env='Console',
                    endpoint=f'/Console/List/{self.list_id}/Email/{email_id}/Attachment/1',
                    text='Add an attachment',
                )

                results.append(result)

                result = self.get_result(
                    method='GET',
                    content_type='JSON',
                    body=None,
                    env='Console',
                    endpoint=f'/Console/List/{self.list_id}/Email/{email_id}',
                    text='Retrieve message detail',
                )

                results.append(result)

        return results

    def get_example_email_id(self):
        email_id = None

        result = self.get_result(
            method='GET',
            content_type='JSON',
            body=None,
            env='Console',
            endpoint=f'/Console/List/{self.list_id}/Emails',
            text='Get all emails',
        )

        items = result['res_body'].get('Items', None)
        for item in items:
            if item.get('Subject', '') == 'Test Message Python':
                email_id = item['idMessage']
                break

        return email_id, result

    def example_6(self):
        results = []

        email_id, _ = self.get_example_email_id()

        if email_id:
            result = self.get_result(
                method='POST',
                content_type='JSON',
                body='test tag',
                env='Console',
                endpoint=f'/Console/List/{self.list_id}/Tag',
                text='Create a new tag',
            )

            results.append(result)

            tag_id = result['res_body'].get('Id', 1)

            result = self.get_result(
                method='GET',
                content_type='JSON',
                body=None,
                env='Console',
                endpoint=f'/Console/List/{self.list_id}/Email/{email_id}',
                text='Pick up a message and retrieve detailed information',
            )

            results.append(result)

            tags = [
                {
                    "Id": tag_id,
                    "Enabled": True,
                    "Name": "test tag",
                }
            ]

            body = result['res_body']
            body['Tags'] = tags

            result = self.get_result(
                method='PUT',
                content_type='JSON',
                body=json.dumps(body),
                env='Console',
                endpoint=f'/Console/List/{self.list_id}/Email/{email_id}',
                text='Add the tag to the message details and save',
            )

            results.append(result)

        return results

    def example_7(self):
        results = []

        email_id, result = self.get_example_email_id()

        if email_id:
            results.append(result)

            result = self.get_result(
                method='POST',
                content_type='JSON',
                body='',
                env='Console',
                endpoint=f'/Console/List/{self.list_id}/Email/{email_id}/Send',
                text='Send email to all recipients in the list',
            )

            results.append(result)

        return results

    def example_8(self):
        results = []

        email_id, result = self.get_example_email_id()

        if email_id:
            results.append(result)

            result = self.get_result(
                method='GET',
                content_type='JSON',
                body=None,
                env='MailStatistics',
                endpoint=f'/Message/{email_id}/List/Views?pageSize=5&pageNum=0',
                text='Request (to MailStatisticsService.svc) for paged message '
                     'views list for the previously sent message',
            )

            results.append(result)

        return results


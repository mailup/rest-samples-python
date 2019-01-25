import os
from flask import Flask, render_template, request, make_response
from mail_up_client import MailUpClient, MailUpException
from examples import example_names

app = Flask(__name__)
app.config.from_object(os.environ.get('APP_SETTINGS', 'config.Config'))
mail_up = MailUpClient(config=app.config)
example_results = [None for x in range(len(example_names))]
example_errors = [None for x in range(len(example_names))]


def login():
    global example_errors, example_results
    username = request.form.get('username')
    password = request.form.get('password')
    try:
        mail_up.retrieve_access_token(username, password)
        example_results = [None for x in range(len(example_names))]
        example_errors = [None for x in range(len(example_names))]
    except MailUpException:
        pass


def login_with_code():
    global example_errors, example_results
    code = request.args.get('code')
    try:
        mail_up.retrieve_access_token_with_code(code)
        example_results = [None for x in range(len(example_names))]
        example_errors = [None for x in range(len(example_names))]
    except MailUpException:
        pass


def refresh_token():
    mail_up.refresh_access_token()


@app.before_request
def before_request():
    mail_up.load_token(cookies=request.cookies)
    if mail_up.get_token_time() <= 0:
        mail_up.clear_tokens()


@app.after_request
def after_request(response):
    if mail_up.access_token:
        response.set_cookie('access_token', mail_up.access_token)
        response.set_cookie('refresh_token', mail_up.refresh_token)
        response.set_cookie('token_time', str(mail_up.token_time))

    return response


@app.route('/', methods=['GET', 'POST'])
def index():
    execute_result = None

    if request.form.get('logon_by_password'):
        login()
    elif request.args.get('code'):
        login_with_code()
    elif request.form.get('refresh_token'):
        refresh_token()
    elif request.form.get('logon_by_key'):
        return mail_up.logon()
    elif request.form.get('execute_request'):
        uri = request.form.get('url') + request.form.get('endpoint')
        try:
            execute_result = mail_up.call_method(
                method=request.form.get('method'),
                content_type=request.form.get('content_type'),
                url=uri,
                body=request.form.get('body'),
            )
        except MailUpException as e:
            pass

    for number, name in enumerate(example_names):
        if request.form.get(f'run_example_{number + 1}'):
            method_to_call = getattr(mail_up, f'example_{number + 1}')
            example_results[number] = [True]
            try:
                example_results[number] = method_to_call()
            except MailUpException as e:
                example_errors[number] = dict()
                example_errors[number]['code'] = e.code
                example_errors[number]['message'] = e.error
                example_errors[number]['url'] = mail_up.error_url

    authorization_status = 'Authorized' if mail_up.access_token else 'Unauthorized'

    resp = make_response(
        render_template(
            'index.html',
            authorization_status=authorization_status,
            access_token=mail_up.access_token,
            token_time=mail_up.get_token_time(),
            execute_result=execute_result,
            example_results=example_results,
            example_errors=example_errors,
            endpoints={
                'Console': mail_up.console_endpoint,
                'MailStatistics': mail_up.mail_statistics_endpoint,
            },
            examples=example_names,
        )
    )

    return resp


if __name__ == '__main__':
    app.run()


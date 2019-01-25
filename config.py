class Config(object):
    ID_LIST = 1
    CLIENT_ID = '<YOUR_CLIENTID>'
    CLIENT_SECRET = '<YOUR_CLIENTSECRET>'
    CALLBACK_URI = 'http://127.0.0.1:5000/'

    BASE_URI = 'https://services.mailup.com'
    LOGON_URI = f'{BASE_URI}/Authorization/OAuth/LogOn'
    AUTH_URI = f'{BASE_URI}/Authorization/OAuth/Authorization'
    TOKEN_URI = f'{BASE_URI}/Authorization/OAuth/Token'
    CONSOLE_URI = f'{BASE_URI}/API/v1.1/Rest/ConsoleService.svc'
    MAIL_STATS_URI = f'{BASE_URI}/API/v1.1/Rest/MailStatisticsService.svc'

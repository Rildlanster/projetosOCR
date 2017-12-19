# -*- coding: utf-8 -*-
'''
Created on 8 de nov de 2017

@author: Rodrigo Nogueira
'''
import os
import yaml
import logging.config
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Ambiente em que a aplicação está rodando.
_localLogger = None
application = None

#Setup do log com o arquivo de configuração
def _setup_Flask_logging():
    MYDIR = os.path.dirname(__file__)
    with open(os.path.join(MYDIR, 'logging.yaml'), 'rt') as f:
        config = yaml.safe_load(f.read())
        logging.config.dictConfig(config)
        logger = logging.getLogger(__name__)  
        logger.debug("Logger configurado. Ambiente Flask server.")
        global _localLogger
        _localLogger = logging.getLogger(__name__)

def _setup_Gunicorn_logging():
    global _localLogger, application
    gunicorn_error_logger = logging.getLogger('gunicorn.error')
    application.logger.handlers.extend(gunicorn_error_logger.handlers)
    application.logger.setLevel(application.config.get("APP_LOG_LEVEL"))
    _localLogger = application.logger
    _localLogger.info('Inicialização do logger para o Gunicorn.')

_serverEnvName = None
#Configura o logger apropriado com o tipo de ambiente em que a aplicação está rodando.
def setup_logging(envName):
    global _serverEnvName
    _serverEnvName = envName
    if envName == "Gunicorn":
        _setup_Gunicorn_logging()
    else: 
        _setup_Flask_logging()

def getLogger(moduleName):
    global _serverEnvName, _localLogger
    if _serverEnvName == "Gunicorn":
        return _localLogger
    return logging.getLogger(moduleName)

FROM_MAIL = 'prfdiasi@gmail.com'
MAIL_PASS = 'prf123diasi'
TO_MAIL = 'prfdiasi@gmail.com'

def sendMail(title, body):
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(FROM_MAIL, MAIL_PASS)
    msg = MIMEMultipart()
    msg['From'] = FROM_MAIL
    msg['To'] = TO_MAIL
    msg['Subject'] = title
    msg.attach(MIMEText(body, 'plain'))
    text = msg.as_string()
    server.sendmail(FROM_MAIL, TO_MAIL, text)
    server.quit()

if __name__ == "__main__":
    sendMail("Titulo do email", "Texto do email\nlalalala\n\n*** FIM ***")
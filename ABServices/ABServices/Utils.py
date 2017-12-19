# -*- coding: utf-8 -*-
'''
Created on Aug 12, 2017

Funções utilitárias

@author: Rodrigo Nogueira
'''
import threading
import os
import errno
import logging.config
from posix import strerror
import datetime
import yaml
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

#Ambiente em que a aplicação está rodando.
_localLogger = None
application = None

#Definição de anotação para funções que devem ser synchronized.
def synchronized(func):
    func.__lock__ = threading.Lock()
        
    def synced_func(*args, **kws):
        with func.__lock__:
            return func(*args, **kws)

    return synced_func

#Sincronizacao de métodos de uma classe.
def synchronized_with_attr(lock_name):
    
    def decorator(method):
            
        def synced_method(self, *args, **kws):
            lock = getattr(self, lock_name)
            with lock:
                return method(self, *args, **kws)
                
        return synced_method
        
    return decorator

def getAppConf(confName):
    return application.config.get(confName)

#Cria arquivo e diretórios, caso não existam.
@synchronized
def fileCheckOrCreate(fileFullName):    
    if not os.path.isfile(fileFullName): 
        try:
            if not os.path.exists(os.path.dirname(fileFullName)):
                os.makedirs(os.path.dirname(fileFullName))
            (open(fileFullName, "w")).close() #cria o arquivo
        except OSError as exc: 
            if exc.errno != errno.EEXIST:
                _localLogger.fatal(str(os.getpid()) + "I/O error({0}): {1}".format(errno, strerror))
                raise

def valiDate(dateText, dateFormat):
    try:
        return datetime.datetime.strptime(dateText, dateFormat)
    except ValueError:
        return datetime.datetime(2000, 01, 01, 00, 00, 00)

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
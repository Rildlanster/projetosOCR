# -*- coding: utf-8 -*-
'''
Created on 8 de nov de 2017

@author: Rodrigo Nogueira
'''
import os
import yaml
import logging.config

_localLogger = None
application = None

#Extensões aceitas como imagens para o OCR.
ALLOWED_EXTENSIONS = set(['bmp' , 'jpg', 'jpeg', 'webp'])
def allowed_OCR_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

def getAppConf(confName):
    return application.config.get(confName)

# -*- coding: utf-8 -*-
'''
Created on 12 de out de 2017

Configurações para a aplicação.

@author: Rodrigo Nogueira
'''
import logging

class Config(object):
    SERVER_PORT = 8020
    APP_LOG_LEVEL = logging.INFO
    
class ProdConfig(Config):
    APP_LOG_LEVEL = logging.INFO

class DevConfig(Config):
    APP_LOG_LEVEL = logging.DEBUG
    SERVER_PORT = 8002
    

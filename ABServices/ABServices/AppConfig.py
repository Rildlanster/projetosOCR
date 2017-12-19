# -*- coding: utf-8 -*-
'''
Created on 12 de out de 2017

Configurações para a aplicação.

@author: Rodrigo Nogueira
'''
import logging

class Config(object):
    SERVER_PORT = 8000
    APP_LOG_LEVEL = logging.INFO
    
    #Configurações serviços CSV
    #Diretório para armazenamento dos arquivos CSV disponíveis para processamento.
    CSV_STORAGE_DIR = "/data/csv/consolidado/"
    #Diretório de trabalho dos arquivos CSV
    CSV_WORKING_DIR = "/opt/data/ws_csv/"
    #Arquivo de controle de informações gerais sobre o processamento do arquivo CSV no diretório de trabalho.
    CONTROL_CSV_FILE_NAME = CSV_WORKING_DIR + ".control_ab"
    #Tempo em segundos a partir do qual um arquivo CSV de trabalho é disponibilizado para processamento.
    TIME_TO_ROTATE_FILE_S = 60
    #Tempo em segundos máximo que uma informação fica em memória. A partir desse tempo os dados devem ser persistidos em disco.
    TIME_FLUSH_S = 10

class ProdConfig(Config):
    APP_LOG_LEVEL = logging.DEBUG

class DevConfig(Config):
    APP_LOG_LEVEL = logging.DEBUG
    SERVER_PORT = 8001
    CSV_STORAGE_DIR = "/opt/data/testing/ws_csv/consolidado/"
    CSV_WORKING_DIR = "/opt/data/testing/ws_csv/"
    CONTROL_CSV_FILE_NAME = CSV_WORKING_DIR + ".control_ab"
    

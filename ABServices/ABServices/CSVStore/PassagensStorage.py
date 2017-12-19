# -*- coding: utf-8 -*-
'''
Created on 01 de out de 2017

Controla a maipulação dos arquivos CSV.

@author: Rodrigo Nogueira
'''
import threading
from ABServices.CSVStore.CSVManager import CSVFile
import PassagensConfig
from datetime import datetime
import multiprocessing
import shutil
from ABServices import Utils
import atexit
from ABServices.Utils import synchronized_with_attr

#Este lock deve estar compartilhado entre processo diferentes. No gunicorn usar opção --preload.
_storageLockProc = multiprocessing.Lock()
logger = Utils.getLogger(__name__)  

class PassagensStorage(object):
    _instance = None
    ENTITY_NAME = "passagem"
        
    #Somente uma instância da classe por processo.
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(PassagensStorage, cls).__new__(cls, *args, **kwargs)
            cls._instance._created = False
        return cls._instance
    
    def __init__(self):    
        if not self._created:
            self.lock = threading.Lock()
            #Array com elementos informados pelo serviço web.
            self._rows = []
            #Sinaliza se existem elementos no CSV para movimentação para arquivo definitivo.
            self.WORKING_CSV_FILE = Utils.getAppConf("CSV_WORKING_DIR") + self.ENTITY_NAME + ".csv"
            _scheduleFileRotation()
            self._created = True
            logger.debug("*** PassagensStorage iniciado!!! ***")
            
    @property
    def rows(self):
        return self._rows
    
    def appendRow(self, row):
        self._rows.append(row)
    
    def cleanup(self):
        self._rows = list()
    
    #Valida o JSON e adiciona na lista de registros.
    @synchronized_with_attr("lock")
    def validateAndInsert(self, jsonContent):
#         logger.debug("validateAndInsert: Recebido request para inserção em memória.\n")
        if jsonContent.get(self.ENTITY_NAME, "null") == "null":
            return -1
        row = []
        for key in PassagensConfig.passagem:
            row.append(jsonContent[self.ENTITY_NAME].get(key, "null"))
        self.appendRow(row)
            
    #Descarrega a memória no arquivo CSV de trabalho.
    #Lock (de thread) necessário, pois o processo de recebimento pode tentar escrever na
    #passagensMemStorage.rows após/durante inserção no CSV e antes do cleanup.
    @synchronized_with_attr("lock")
    def flushRowsToCSV(self):
        if len(self.rows) <= 0:
            return
        logger.debug("Rodando flush de dados para CSV.")
        csvFile = CSVFile(self.WORKING_CSV_FILE)
        if csvFile.isStartingEmptyFile():
            csvFile.appendFile(PassagensConfig.passagem)
        csvFile.appendManyFile(self.rows)
        self.cleanup()
        logger.debug("Flush realizado com sucesso para arquivo de trabalho.")
        
    #Copia CSV para arquivo definitivo que será disponibilizado para processamento.
    @synchronized_with_attr("lock")
    def copyCSV(self, newCSVFileName):
        csvFile = CSVFile(self.WORKING_CSV_FILE)
        shutil.copyfile(csvFile.csvFullFileName, newCSVFileName)
        logger.info("Novo arquivo CSV gerado " + newCSVFileName)
        #Limpa o arquivo e grava o header do CSV.
        csvFile.cleanup()
        csvFile.appendFile(PassagensConfig.passagem)
        
#Sinaliza que a thread de flush pode avançar sem a restrição do tempo mínimo definido.
#Isso será feito qdo o processo receber o sinal para terminar.
_thFreeToFlushOnFinish = False
_lastCSVTime = datetime.now()

#Informa a thread de flush se uma nova versão de arquivo CSV pode ser gerada.
#Se o fim do processo foi sinalizado, verifica se o arquivo de trabalho tem mais de uma linha para
#que possa ser gerado novo CSV.
#Esta função deve ser chamada dentro do lock _storageLockProc.
def _canGenerateNewCSVVersion():
    global _thFreeToFlushOnFinish, _lastCSVTime
    if not _thFreeToFlushOnFinish:
        #Faz primeiro a verificação do _lastCSVTime local para economizar abertura do arquivo de controle.
        if (datetime.now() - _lastCSVTime).total_seconds() < Utils.getAppConf("TIME_TO_ROTATE_FILE_S"):
#             logger.debug("Intervalo mínimo de tempo não atingido para geração do arquivo.")
            return False
        #Se passou na verificação anterior, verifica o arquivo de controle.
        with open(Utils.getAppConf("CONTROL_CSV_FILE_NAME"), "r") as f:
            _lastCSVTime = Utils.valiDate(f.readline(), "%Y-%m-%dT%H:%M:%S")
        if (datetime.now() - _lastCSVTime).total_seconds() < Utils.getAppConf("TIME_TO_ROTATE_FILE_S"):
            logger.debug("_lastCSVTime atualizado a partir do arquivo, mas intervalo mínimo de tempo não atingido para geração do arquivo.")
            return False
    passagensMemStorage = PassagensStorage()
    csvFile = CSVFile(passagensMemStorage.WORKING_CSV_FILE, True)
    rowsCount = csvFile.count()
    logger.debug("Intervalo para geração do arquivo CSV atingido. Número de elementos no CSV: " + str(rowsCount))
    #Abre o arquivo de controle para atualizar a data da última verificação de geração do CSV.
    Utils.fileCheckOrCreate(Utils.getAppConf("CONTROL_CSV_FILE_NAME"))
    with open(Utils.getAppConf("CONTROL_CSV_FILE_NAME"), "w") as f:
        _lastCSVTime = datetime.now()
        f.write(_lastCSVTime.strftime("%Y-%m-%dT%H:%M:%S"))
    return rowsCount > 0

#Controle do flush das informações em arquivo.
def _flush():
    _scheduleFileRotation()
    global _thFreeToFlushOnFinish, _lastCSVTime
    with _storageLockProc:
        passagensMemStorage = PassagensStorage()
        passagensMemStorage.flushRowsToCSV()
        if not _canGenerateNewCSVVersion(): return
        passagensMemStorage.copyCSV(Utils.getAppConf("CSV_STORAGE_DIR") + 
                    passagensMemStorage.ENTITY_NAME + datetime.now().strftime("%Y%m%dT%H%M%S") + ".csv")
        logger.debug("CSV gerado e arquivo de controle atualizado com data " + _lastCSVTime.strftime("%Y-%m-%dT%H:%M:%S") + ". Yay!")
        
#Registra thread para próxima execução.
def _scheduleFileRotation():
    global _thFreeToFlushOnFinish
    if not _thFreeToFlushOnFinish:
        _timedThread = threading.Timer(Utils.getAppConf("TIME_FLUSH_S") + 1, _flush).start()

@atexit.register
def theEndIsNear():
    logger.info("Finalizando processo...")
    global _thFreeToFlushOnFinish
    _thFreeToFlushOnFinish = True
    _flush()
    logger.info("See ya!")

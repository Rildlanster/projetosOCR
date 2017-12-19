# -*- coding: utf-8 -*-
'''
Created on Aug 13, 2017

Utilitários para arquivo CSV.

@author: Rodrigo Nogueira
'''
import errno
from posix import strerror
import unicodecsv as csv
from ABServices.Utils import synchronized_with_attr
from ABServices import Utils
import threading
import logging

logger = logging.getLogger(__name__)  

class CSVFile(object):        
    
    #Construtor recebe o nome do arquivo CSV e o mode de abertura do arquivo.
    #São possíveis read e append.
    def __init__(self, csvFullFileName, loadOnOpen = False, fileOpt = "r"):
        self.lockCSV = threading.Lock()
        self.csvFullFileName = csvFullFileName
        self.csvReader = []
        Utils.fileCheckOrCreate(self.csvFullFileName)
        self.startingEmptyFile = len(open(self.csvFullFileName, "r").readline().strip(' \t\n\r')) == 0
        if self.startingEmptyFile:
            self.cleanup()
        #Se a opção de abertura for r ou a, o arquivo precisa existir.
        if fileOpt not in "ra+":
            raise ValueError("O arquivo informado já existe e só pode ser aberto com as opções 'ra'.")
        if loadOnOpen:
            try:
                with open(self.csvFullFileName, fileOpt, -1) as csvFile:
                    self.csvReader = [row for row in csv.reader(csvFile, delimiter=',', quotechar='"')] 
                    logger.info("CSV %s contem %u elemento(s)." % (self.csvFullFileName, len(self.csvReader) - 1))
            except IOError as err:
                logger.fatal("I/O error({0}): {1}".format(errno, strerror))
                raise err
        #Indice para a leitura sequencial do arquivo CSV, controlada pelo metodo readNextLine
        self.restartReadingIndex()
        
    def restartReadingIndex(self):
        self.readingIndex = 0

    #Informa apenas se o arquivo foi aberto vazio no momento da criação deste objeto.
    def isStartingEmptyFile(self):
        return self.startingEmptyFile

    #Prover a leitura de modo sequencial
    @synchronized_with_attr("lockCSV")
    def readNextLine(self):
        if(self.readingIndex >= len(self.csvReader) - 1):
            return None
        self.readingIndex += 1
        return self.csvReader[self.readingIndex]

    #Adiciona uma linha ao arquivo CSV com as informacoes em row
    @synchronized_with_attr("lockCSV")
    def count(self):
        if len(self.csvReader) == 1:
            return 0
        return len(self.csvReader) - 1

    #Adiciona uma linha ao arquivo CSV com as informacoes em row
    @synchronized_with_attr("lockCSV")
    def appendFile(self, row):
        with open(self.csvFullFileName, 'a') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, encoding='utf-8')
            writer.writerow(row)
    
    #Adiciona mais de uma linha ao arquivo CSV
    @synchronized_with_attr("lockCSV")
    def appendManyFile(self, rows):
        with open(self.csvFullFileName, 'a') as f:
            writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, encoding='utf-8')
            for row in rows:
                writer.writerow(row)
    
    #Exclui do CSV em memoria os valores ja existentes
    def filter_data(self, values):
        if(len(values) <= 1): return 
        self.restartReadingIndex()
        # Linha abaixo nao funciona para grande volume de dados
        #self.csvReader = filter((lambda row: row not in values[1:]), self.csvReader)
        removedElem = 0
        for rowCheck in values[1:]:
            self.csvReader.remove(rowCheck)
            removedElem += 1
            if removedElem % 1000 == 0:
                logger.info("Removidos %u elementos." %removedElem)
        
    #Exclui todas linhas do arquivo, exceto a primeira (header).        
    @synchronized_with_attr("lockCSV")
    def truncateFromHeader(self):
        self.restartReadingIndex()
        self.csvReader = []
        with open(self.csvFullFileName, 'a') as f:
            f.readline() #lê o header para mover o cursor para a próxima linha.
            f.truncate()
        
    @synchronized_with_attr("lockCSV")
    def cleanup(self):
        (open(self.csvFullFileName, "w")).close() #limpa arquivo

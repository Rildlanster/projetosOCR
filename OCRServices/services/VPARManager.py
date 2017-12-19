# -*- coding: utf-8 -*-
'''
Created on 15 de dez de 2017

@author: Rodrigo Nogueira
'''
import random
import os
from services import OCRUtils
import errno
from posix import strerror

#Essa classe grava um arquivo de imagem para processamento OCR e lê o resultado
#do arquivo de saída gerado.
class VPARManager(object):        
    _instance = None #singleton para o processo
    _TIMEOUT_SEC = 10

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(VPARManager, cls).__new__(cls, *args, **kwargs)
            cls._instance._created = False
        return cls._instance
    
    def __init__(self):    
        if not self._created:
            self._created = True
            self._randFileNameGen = random.Random()
            self._randFileNameGen.seed(os.getpid())
            self.OCR_UPLOAD_FOLDER = OCRUtils.getAppConf("OCR_UPLOAD_FOLDER")
            self.OCR_RESULTS_FOLDER = OCRUtils.getAppConf("OCR_RESULTS_FOLDER")
            OCRUtils.getLogger(__name__).debug("Criado VPARManager do processo " + str(os.getpid()))

    #Gera um nome (numérico) aleatório para o arquivo da imagem.
    #O nome do arquivo é retornado como um código para posterior recuperação do 
    #resultado da leitura OCR.
    def submitImage(self, imgExt, imgData):
        submissionCode = str(self._randFileNameGen.randint(1,99999999999999999999)).zfill(20)
        imageFileName = self.OCR_UPLOAD_FOLDER + submissionCode + "." + imgExt
        try:
            with open(imageFileName, "wb", -1) as imageFile:
                imageFile.write(imgData.decode('base64'))
            return submissionCode
        except IOError as err:
            OCRUtils.getLogger(__name__).fatal("I/O error({0}): {1}".format(errno, strerror))
            raise err
        
    #A partir do código numérico gerado pelo método submitImage, busca o resultado da leitura OCR.
    def getOCRResult(self, submissionCode):
        outputFileName = self.OCR_RESULTS_FOLDER + submissionCode + ".txt"
        if os.path.isfile(outputFileName):
            ocrResultVars = {}
            with open(outputFileName, "r") as resultFile:
                for line in resultFile:
                    name, var = line.partition(":")[::2]
                    ocrResultVars[name.strip()] = var.strip()
            os.remove(outputFileName)
            OCRUtils.getLogger(__name__).info("Resultados do arquivo " + outputFileName + ": Placa " + ocrResultVars["placa"])
            return ocrResultVars

        OCRUtils.getLogger(__name__).info("Arquivo de saída *" + str(outputFileName) + "* não encontrado.")
        return None
    
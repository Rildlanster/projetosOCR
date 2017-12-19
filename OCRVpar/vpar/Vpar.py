#!/usr/bin/env python
'''
Created on Aug 2, 2017

@author: Rodrigo Nogueira
'''
from __future__ import print_function

import atexit
from ctypes import CDLL, byref, POINTER, c_long, CFUNCTYPE
import sys

from vpar.VparStruct import tRecognitionEngineSettings, tResults, MAX_STEPS
from multiprocessing import BoundedSemaphore

#Funcao de callback para uso do VPAR de modo assincrono. Nao esta sendo usada
#dessa forma, ja que o servico eh sincrono.
def callback(code, result):
    pass

#Configuracoes para o motor VPAR
def engineSettingsConfig(engSettings):
    engSettings.lMiliseconds = 0;
    engSettings.bAplicarCorreccion = False;
    engSettings.fDistance = 0;
    engSettings.fVerticalCoeff = 0;
    engSettings.fHorizontalCoeff = 0;
    engSettings.fAngle = 0;
    engSettings.fRadialCoeff = 0;
    engSettings.fVerticalSkew = 0;
    engSettings.fHorizontalSkew = 0;
    engSettings.lNumSteps = 0;
    engSettings.vlSteps = (c_long * MAX_STEPS)()
    engSettings.vlSteps[0] = 20;
    engSettings.vlSteps[1] = 60;
    engSettings.vlSteps[2] = 35;
    engSettings.vlSteps[3] = 40;
    engSettings.vlSteps[4] = 45;
    engSettings.vlSteps[5] = 50;
    engSettings.vlSteps[6] = 55;
    engSettings.vlSteps[7] = 60;
    engSettings.lLeft = 0;
    engSettings.lTop = 0;
    engSettings.lWidth = 0;
    engSettings.lHeight = 0;
    engSettings.fScale = 1;
    engSettings.CharacterRectangle = False;
    engSettings.SlantDetection = 1;
    engSettings.KillerShadow= 0;

#Numero de cores licenciados
licensedCores = 0
#Semaforo para controle do acesso ao VPAR
vparSemaphore = None
#Configuracao para os metodos do motor VPAR
engSettings = None
#Lib do VPAR
lib_vpar = None
#Contador de requests de teste
requestCounter = 0
 
def vparInit():
    #Define o ponteiro para funcao de callback
    CLBKFUNC = CFUNCTYPE(c_long, c_long, POINTER(tResults))
    clbk_func = CLBKFUNC(callback)
    #Carrega a dll do VPAR multithread
    global lib_vpar
    lib_vpar = CDLL("vparmt.so")
    #Inicializa o VPAR
    ret = lib_vpar.vparmtInit(clbk_func, 101, -1, 0, 0, 0, 1);
    if ret == 1:
        print("VPAR INIT OK")
    else:
        print ("ERRO AO INICIAR LIB VPAR: codigo %u" % ret)
        sys.exit()
    
    global licensedCores
    licensedCores = lib_vpar.NumLicenseCores() 
    print("Cores disponiveis = %u" % licensedCores)
    global vparSemaphore
    vparSemaphore = BoundedSemaphore(value = licensedCores)
 
    #Cria a configuracao para os metodos do motor VPAR
    global engSettings
    engSettings = tRecognitionEngineSettings()
    engineSettingsConfig(engSettings)

def ocrReadImg(imgPath):
    global requestCounter, vparSemaphore, engSettings

    result = tResults()
    freeCoresVPAR = lib_vpar.FreeCores()
    print("Cores livres/Total cores = %u/%u" % (freeCoresVPAR, licensedCores))
    if freeCoresVPAR == 0:
        print("Descansando um poukinho, nenhum core disponivel")
        
#     vparSemaphore.acquire()
#     lib_vpar.ActiveLog(True)
    ret = lib_vpar.vparmtReadBMP_sync(byref(engSettings), imgPath, byref(result))
    requestCounter += 1 #Pode nao contar corretamente, pois seria necessario um semaforo
    print ("Request no %u" % requestCounter)
    vparSemaphore.release()
    
    if ret != 1 or result.lNumberOfPlates <= 0:
        if ret != 1: 
            print("Erro VPAR: Erro ao tentar ler a imagem")
            #Tratar o erro de core bloqueado do VPAR. Provavelmente reiniciar o VPAR.
        return None
    return result

@atexit.register
def cleanup():
    print("Adios!")
    lib_vpar.vparmtEnd()   

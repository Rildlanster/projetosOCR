'''
Created on Aug 4, 2017

Definicao das estruturas usadas pelo OCR VPAR.

@author: Rodrigo Nogueira
'''
from ctypes import Structure, c_long, c_float, c_bool, c_void_p, c_char
from _ctypes import POINTER

MAX_STEPS = 8
MAX_PLATES = 8
MAX_CHARACTERS = 10
MAX_FILE_PATH = 200

SERVICE_RESULT_SUCCESS = 1000
SERVICE_RESULT_VPAR_NO_LP_FOUND = 1001
SERVICE_RESULT_VPAR_ERROR = 1002
SERVICE_RESULT_VPAR_UNAVAILABLE_RESOURCES = 1003
  
class tRecognitionEngineSettings(Structure):
    _fields_ = [
        ('miliseconds', c_long),
        ('bApplyCorrection', c_long),
        ('fDistance', c_float),
        ('fVerticalCoeff', c_float),
        ('fHorizontalCoeff', c_float),
        ('fAngle', c_float),
        ('fRadialCoeff', c_float),
        ('fVerticalScrew', c_float),
        ('fHorizontalScrew', c_float),
        ('lNumSteps', c_long),
        ('vlSteps', c_long * MAX_STEPS),
        ('lLeft', c_long),
        ('lTop', c_long),
        ('lWidth', c_long),
        ('lHeight', c_long),
        ('fScale', c_float),
        ('lUserParam1', POINTER(c_void_p)),
        ('lUserParam2', POINTER(c_void_p)),
        ('lUserParam3', POINTER(c_void_p)),
        ('SlantDetection', c_long),
        ('KillerShadow', c_long),
        ('CharacterRectangle', c_bool)
    ]
  
class tResults(Structure):
    _fields_ = [
        ('lRes', c_long),
        ('lNumberOfPlates', c_long),
        ('strResult', c_char * MAX_PLATES * MAX_CHARACTERS),
        ('vlNumbersOfCharacters', c_long * MAX_PLATES),
        ('vlGlobalConfidence', c_float * MAX_PLATES),
        ('vfAverageCharacterHeight', c_float * MAX_PLATES),
        ('vfCharacterConfidence', c_float * MAX_PLATES * MAX_CHARACTERS),
        ('vlLeft', c_long * MAX_PLATES),
        ('vlTop', c_long * MAX_PLATES),
        ('vlRight', c_long * MAX_PLATES),
        ('vlBottom', c_long * MAX_PLATES),
        ('lProcessingTime', c_long),
        ('vlFormat', c_long * MAX_PLATES),
        ('lUserParam1', POINTER(c_void_p)),
        ('lUserParam2', POINTER(c_void_p)),
        ('lUserParam3', POINTER(c_void_p)),
        ('lUserParam4', POINTER(c_void_p)),
        ('EliminateShadow', POINTER(c_void_p)),
        ('strPathCorrectedImage', c_char * MAX_FILE_PATH),
        ('vlCharacterPosition', c_long * MAX_PLATES * MAX_CHARACTERS * 4)
    ]
    
# Agrega a estrutura tResults e um codigo para o servico REST.
class ServiceResult(Structure):
    _fields_ = [
        ('returnCode', c_long),
        ('tResults', tResults)
    ]
# -*- coding: utf-8 -*-
'''
Created on Aug 15, 2017

Consulta o servico de dados do WSO2, onde se obtem a placa referendada
a partir do nome da imagem.

@author: Rodrigo Nogueira
'''
import requests
import json
from threading import Thread
from ABServices.Utils import sendMail
from ABServices.CSVStore.CSVManager import CSVFile

URLMPIR = 'http://10.0.170.131:9764/services/MPIRQueryPlate/mpir/placaReferendada/'
URLOCR = 'http://localhost:8001/getProcessedImg/'
CSV_PROCESSABLE_FILES = "/media/sf_sharedVM/imgOCR/imgProcessable.csv"
THREADS_NUM = 10
csvFileImgProcessable = CSVFile("/media/sf_sharedVM/imgOCR/imgProcessable.csv")
# Arquivo com caminhos das imagens processaveis, leitura do OCR e referencia MPIR.
csvFileImgReadings = CSVFile("/media/sf_sharedVM/imgOCR/imgLPMpirProcessed.csv")
qtde_sucesso = 0
qtde_total = 0
readingsMatch = 0

csvFileImgProcessable.filter_data(csvFileImgReadings.csvReader)

def getValidatedLPFromMPIRDB(imageName):
    response = requests.get(URLMPIR + imageName, headers={"Accept":"application/json"})
    if(response.status_code == 200): 
        jsonContent = json.loads(response.content)["entry"]
        if(jsonContent):
            return jsonContent["placa"]
    return None

class Th(Thread):
    def run(self):
        row = csvFileImgProcessable.readNextLine()
        while(row != None):
            global qtde_sucesso, qtde_total, readingsMatch
            qtde_total += 1
            response = requests.get(URLOCR + row[1][1:])
            mpirLPReading = getValidatedLPFromMPIRDB(row[1])
            if(response.status_code != 200 or mpirLPReading == None):
                print("********** Erro **********\nImagem: %s\nHTTP OCR: %u" 
                      %(row[0], response.status_code))      
                continue      
            ocrLPReading = json.loads(response.content)["placa"]
            print("Placas MPIR=%s, OCR=%s" %(mpirLPReading, ocrLPReading))
            qtde_sucesso += 1
            rowReadings = [row[0], row[1], mpirLPReading, ocrLPReading]
            csvFileImgReadings.appendFile(rowReadings)
            if(qtde_sucesso % 10000 == 0):
                sendMail("Processing checkpoint", "Sucesso / total = " + str(qtde_sucesso) + " / " + str(qtde_total))
            row = csvFileImgProcessable.readNextLine()

#Cria THREADS_NUM threads para enviar os requests
threads_list = []    
for thread_number in range(THREADS_NUM):
    request_thread = Th()
    threads_list.append(request_thread)
    request_thread.start()
   
#Aguarda o termino de todas as threads
joined_thread = 0
for t in threads_list: # threads.enumerate() considera a thread do pydev e, por isso, trava o join
    joined_thread += 1
    print("Threads joined = %u" % joined_thread)
    t.join()

print("Qtde de leituras realizadas: %u" %qtde_sucesso)
sendMail("Processamento imagens MPIR", "Qtde de leituras realizadas: " + str(qtde_sucesso))

if __name__ == "__main__":
    SAMPLE1 = '00027035410189560034371C1020120161025471073313ESRBA007060060060073O000000006032015.jpg'
    SAMPLE2 = '01083291911611071071838D1130120161128559876543FXRSP229100080080090O000000022092015.JPG'
    getValidatedLPFromMPIRDB(SAMPLE1)
    getValidatedLPFromMPIRDB(SAMPLE2)
    
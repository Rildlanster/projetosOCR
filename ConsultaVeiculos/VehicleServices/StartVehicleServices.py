# -*- coding: utf-8 -*-
'''
Created on 10 de nov de 2017

@author: Rodrigo Nogueira
'''
import logging

from flask import Flask
from flask.wrappers import Response
from flask_restful import Api
from flask_restful import Resource
import requests
import datetime

from VehicleServices import VSUtils
from VehicleServices.AppConfig import DevConfig
from multiprocessing import BoundedSemaphore
import json
from VehicleServices.VSUtils import sendMail
from requests.exceptions import ConnectionError

VehicleServicesApp = Flask("VehicleServicesApp")
_api = Api(VehicleServicesApp)
MOTORBR_MAX_CONCURRENCY = 2 # Máximo de consultas paralelas que podem executar.
MOTORBR_VEHICLE_URL_CONSTANT = "http://motorprod1.producao1.datacenter1:8080/MotorConsultas/consulta?matricula=1481190&cpf=09994423762&objeto=VEICULO&campo=PLACA&sistema=22&chave="
MOTORBR_TIMEOUT_SEC = 5 #Tempo em segundos do timeout do barramento ao chamar a consulta de veículos implementada aqui.
semaphoreMotorBR = BoundedSemaphore(value = MOTORBR_MAX_CONCURRENCY)
VSUtils.getLogger(__name__).info("*** START APLICAÇÃO CONSULTA MOTORBR ***")

class VehicleServices(Resource):        

    def __init__(self, *args, **kwargs):
        super(VehicleServices, self).__init__(*args, **kwargs)
        
    # Busca um veículo no motor pela placa.
    def get(self, licensePlate):
        global semaphoreMotorBR
        if(semaphoreMotorBR.acquire(block=False) == False):
            VSUtils.getLogger(__name__).info("*** Limite de consultas simultâneas excedido ***")
            return Response(status = 429) #429 Too Many Requests
        try:
            wait4MotorTimeStart = datetime.datetime.now()
            responseMotor = requests.get(MOTORBR_VEHICLE_URL_CONSTANT + licensePlate)
            wait4MotorTimeEnd = datetime.datetime.now()
            elapsedTime = wait4MotorTimeEnd - wait4MotorTimeStart
            VSUtils.getLogger(__name__).info("Consulta da placa %s demorou %u,%u seg." %(licensePlate, elapsedTime.total_seconds(), elapsedTime.microseconds / 1000))
            if elapsedTime.total_seconds() > MOTORBR_TIMEOUT_SEC:
                VSUtils.getLogger(__name__).info("*** TIMEOUT NO BARRAMENTO, POIS O MOTOR DEMOROU A RESPONDER ***")
        except ConnectionError as ex:
            template = "*** ERRO DE CONEXÃO. ConnectionError. Argumentos:\n{1!r} ***"
            message = template.format(ex.args)            
            VSUtils.getLogger(__name__).info(message)
            return Response(status = 500)
        except Exception as ex:
            template = "Exceção {0}. Argumentos:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)            
            sendMail("Nova exceção identificada", message)
        finally:
            semaphoreMotorBR.release()
        if responseMotor.status_code == 200:
            jsonContent = responseMotor.json()
            if(jsonContent):
                try: 
                    if jsonContent["ocorrencias"][0]["statusConexao"].lower() == "timeout":
                        return Response(status = 504) #504 Gateway Timeout
                    if jsonContent["placa"] == None:
                        return Response(status = 404)
                except IndexError: #Qdo nao vem ocorrencias no JSON.
                    pass
                except KeyError: #Chave do json incorreta.
                    pass
            return Response(json.dumps(responseMotor.json()), content_type = "application/json", status = 200)
        return Response(status = 500)

def main():
    VSUtils.application = VehicleServicesApp

    _api.add_resource(
        VehicleServices,
        '/motorBR/veiculos/<licensePlate>'
    )
    
#Se este arquivo é executado, roda o servidor do Flask. Para rodar no Gunicorn, basta
#iniciar o arquivo correspondente com o ABServicesAPP.run executando no contexto do Gunicorn.
if __name__ == "__main__":
    main()
    VehicleServicesApp.config.from_object(DevConfig)
    VSUtils.setup_logging("Flask")
    # Host e porta do servidor
    SERVER_HOST = '0.0.0.0'
    SERVER_PORT = VehicleServicesApp.config.get("SERVER_PORT")
    DEBUG = VehicleServicesApp.config.get("APP_LOG_LEVEL") == logging.DEBUG
    VehicleServicesApp.run(debug=DEBUG, threaded=True, host=SERVER_HOST, port=SERVER_PORT)

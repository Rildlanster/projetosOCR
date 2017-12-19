# -*- coding: utf-8 -*-
'''
Created on 20 de ago de 2017

@author: Rodrigo Nogueira
'''
import logging

from flask import Flask, request
from flask.wrappers import Response
from flask_restful import Api
from flask_restful import Resource

from ABServices import Utils
from ABServices.AppConfig import DevConfig
from ABServices.CSVStore.PassagensStorage import PassagensStorage

ABServicesAPP = Flask("ABServices")
_api = Api(ABServicesAPP)

class ABCSVServices(Resource):        
    def __init__(self, *args, **kwargs):
        super(ABCSVServices, self).__init__(*args, **kwargs)
        self.logger = logging.getLogger(__name__)  
        
    def post(self):
#         Utils.getLogger(__name__).debug("Request recebido /csvServices/storePassagem. Header: " + request.headers['Content-Type'])
        if request.headers['Content-Type'] != "application/json":
            return Response(status = 415) #Unsupported Media Type 
        jsonContent = request.json
        if(jsonContent):
            passagensStorage = PassagensStorage()
            passagensStorage.validateAndInsert(jsonContent)
            resp = Response(status = 201) #Created
            resp.headers['Content-Type'] = 'application/json'
            return resp
        return Response(status = 422) #Unprocessable Entity

@ABServicesAPP.route("/")
def welcome():
    Utils.getLogger(__name__).debug('Welcome Sir!')
    return "Serviços de gravação de dados em arquivo CSV e validação OCR de imagens."
        
def main():
    Utils.application = ABServicesAPP

    _api.add_resource(
        ABCSVServices,
        '/csvServices/storePassagem'
    )
    
#Se este arquivo é executado, roda o servidor do Flask. Para rodar no Gunicorn, basta
#iniciar o arquivo correspondente com o ABServicesAPP.run executando no contexto do Gunicorn.
if __name__ == "__main__":
    main()
    ABServicesAPP.config.from_object(DevConfig)
    Utils.setup_logging("Flask")
    # Host e porta do servidor
    SERVER_HOST = '0.0.0.0'
    SERVER_PORT = ABServicesAPP.config.get("SERVER_PORT")
    DEBUG = ABServicesAPP.config.get("APP_LOG_LEVEL") == logging.DEBUG
    ABServicesAPP.run(debug=DEBUG, threaded=True, host=SERVER_HOST, port=SERVER_PORT)

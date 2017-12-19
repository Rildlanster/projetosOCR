# -*- coding: utf-8 -*-
'''
Created on 20 de ago de 2017

@author: Rodrigo Nogueira
'''
import logging

from flask import Flask, request
from flask.json import jsonify
from flask.wrappers import Response
from flask_restful import Api
from flask_restful import Resource

from services import OCRUtils
from services.AppConfig import DevConfig
from services.VPARManager import VPARManager

ABOCRServicesAPP = Flask("OCRServices")
_api = Api(ABOCRServicesAPP)

#Serviços para OCR
class ABOCRServices(Resource):        

    def __init__(self, *args, **kwargs):
        super(ABOCRServices, self).__init__(*args, **kwargs)
        self.vparManager = VPARManager()
        
    #Submissão da imagem a ser lida pelo OCR. Retorna um código de submissão para
    #recuperação do resultado da leitura.
    def post(self):
        jsonContent = request.json
        #Verifica se o json tem o nome do arquivo e dados.
        if not((jsonContent) and jsonContent.get("extArquivo") and jsonContent.get("dadosArquivo")):
            return Response(status = 400)
        try:
            submissionCode = self.vparManager.submitImage(jsonContent.get("extArquivo"), jsonContent.get("dadosArquivo"))
            return jsonify(codigoLeituraOCR = submissionCode)
        except:
            OCRUtils.getLogger(__name__).debug('*** Exceção no método POST de ABOCRServices ***')
            return Response(status = 500)
          
    #Obtém o resultado do OCR, a partir do código da submissão.  
    def get(self, codigoLeituraOCR):
        if len(codigoLeituraOCR) <= 15: #o tamanho do código é maior que 15.
            return Response(status = 422)
        try:
            ocrResultVars = self.vparManager.getOCRResult(codigoLeituraOCR)
            if ocrResultVars == None:
                return Response(status = 400)
            if ocrResultVars["placa"] == "0":
                return Response(status = 404)
            return jsonify(placa = ocrResultVars["placa"], 
                    tempoProcessamento = ocrResultVars["tempoProcessamento"],
                    confiancaGlobal = ocrResultVars["confiancaGlobal"],
                    alturaMediaChar = ocrResultVars["alturaMediaChar"],
                    placaRetEsq = ocrResultVars["placaRetEsq"],
                    placaRetTopo = ocrResultVars["placaRetTopo"],
                    placaRetDir = ocrResultVars["placaRetDir"],
                    placaRetBase = ocrResultVars["placaRetBase"])
        except:
            OCRUtils.getLogger(__name__).debug('*** Exceção no método GET de ABOCRServices ***')
            return Response(status = 500)
            
@ABOCRServicesAPP.route("/")
def welcome():
    OCRUtils.getLogger(__name__).debug('Welcome Sir!')
    return "Serviços de OCR de imagens."
        
def main():
    OCRUtils.application = ABOCRServicesAPP
    ABOCRServicesAPP.config.from_object(DevConfig)
    
    #api resource routing
    _api.add_resource(
        ABOCRServices,
        '/ocr/imagens',
        '/ocr/leituras/<codigoLeituraOCR>'
    )

#Se este arquivo é executado, roda o servidor do Flask. Para rodar no Gunicorn, basta
#iniciar o arquivo correspondente com o ABServicesAPP.run executando no contexto do Gunicorn.
if __name__ == "__main__":
    main()
    OCRUtils.setup_logging("Flask")
    # Host e porta do servidor
    SERVER_HOST = '0.0.0.0'
    SERVER_PORT = ABOCRServicesAPP.config.get("SERVER_PORT")
    DEBUG = ABOCRServicesAPP.config.get("APP_LOG_LEVEL") == logging.DEBUG
    ABOCRServicesAPP.run(debug=DEBUG, threaded=True, host=SERVER_HOST, port=SERVER_PORT)

# -*- coding: utf-8 -*-
'''
Created on 9 de dez de 2017

@author: coint
'''
from ctypes import string_at
import logging
from vpar import Vpar, OCRUtils
from vpar.Vpar import vparInit
from flask.app import Flask
from flask_restful import Api, Resource
from flask.wrappers import Response
from flask.json import jsonify
from vpar.AppConfig import DevConfig

ABOCRServicesAPP = Flask("OCRServices")
_api = Api(ABOCRServicesAPP)

#Serviços para OCR
class ABOCRServices(Resource):        
    def __init__(self, *args, **kwargs):
        super(ABOCRServices, self).__init__(*args, **kwargs)
        
    # Metodo GET usado para teste do servico
    def get(self, imgPath = '/tmp/B0064GK.BMP'):  
        if(imgPath[0:1] != "/"):
            imgPath = "/" + str(imgPath)
        if(not OCRUtils.allowed_OCR_file(imgPath)):
            return Response(status = 400)
        else:
            print("Imagem = %s" % imgPath)     
        result = Vpar.ocrReadImg(imgPath)
        if result == None:
            return Response(status = 404)
        else:
            return jsonify(placa = string_at(result.strResult), 
                    tempoProcessamento = result.lProcessingTime,
                    confiancaGlobal = result.vlGlobalConfidence[0])

@ABOCRServicesAPP.route("/")
def welcome():
    OCRUtils.getLogger(__name__).debug('Welcome Sir!')
    return "Serviços de OCR de imagens."
        
def main():
    OCRUtils.application = ABOCRServicesAPP

    #api resource routing
    _api.add_resource(
        ABOCRServices,
        '/ocr/getProcessedImg',
        '/ocr/getProcessedImg/<path:imgPath>',
        '/ocr/processImage'
    )

    vparInit()
    result = Vpar.ocrReadImg('/tmp/B0064GK.BMP')
    print(result.strResult)
    
#Se este arquivo é executado, roda o servidor do Flask. Para rodar no Gunicorn, basta
#iniciar o arquivo correspondente com o ABServicesAPP.run executando no contexto do Gunicorn.
if __name__ == "__main__":
    main()
    ABOCRServicesAPP.config.from_object(DevConfig)
    OCRUtils.setup_logging("Flask")
    # Host e porta do servidor
    SERVER_HOST = '0.0.0.0'
    SERVER_PORT = ABOCRServicesAPP.config.get("SERVER_PORT")
    DEBUG = ABOCRServicesAPP.config.get("APP_LOG_LEVEL") == logging.DEBUG
    ABOCRServicesAPP.run(debug=DEBUG, threaded=True, host=SERVER_HOST, port=SERVER_PORT)

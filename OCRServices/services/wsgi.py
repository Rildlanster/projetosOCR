# -*- coding: utf-8 -*-
'''
Created on 01 de dez de 2017

@author: Rodrigo Nogueira
'''
from services import OCRUtils, AppConfig
from services.StartOCR import main, ABOCRServicesAPP as application

main()
application.config.from_object(AppConfig.DevConfig)
OCRUtils.setup_logging("Gunicorn")

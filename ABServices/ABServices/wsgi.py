# -*- coding: utf-8 -*-
'''
Created on 20 de out de 2017

@author: coint
'''
from ABServices.StartApp import main, ABServicesAPP as application
from ABServices import Utils
import ABServices

main()
application.config.from_object(ABServices.AppConfig.ProdConfig)
Utils.setup_logging("Gunicorn")

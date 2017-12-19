# -*- coding: utf-8 -*-
'''
Created on 01 de dez de 2017

@author: Rodrigo Nogueira
'''
from VehicleServices import VSUtils, AppConfig
from VehicleServices.StartVehicleServices import main, VehicleServicesApp as application

main()
application.config.from_object(AppConfig.DevConfig)
VSUtils.setup_logging("Gunicorn")

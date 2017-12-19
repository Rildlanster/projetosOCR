'''
Created on 20 de out de 2017

@author: coint
'''
from flask import Flask
from flask_restful import Api
application = Flask(__name__)
_api = Api(application)

@application.route("/")
def hello():
    return "<h1 style='color:blue'>Hello There! a</h1>"

if __name__ == "__main__":
    application.run(host='0.0.0.0')

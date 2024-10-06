# Every level/folder of a Python application has an __init__.py file. The purpose of this file is to connect the levels
# of the app to each other. 

from mongoengine import connect
from flask_login import LoginManager
from flask import Flask, session, request
import os
from flask_moment import Moment
import base64
import re
import certifi
import ssl
import jinja2
from urllib.parse import quote_plus


# because secretvars is not sent to git this will cause an error for any git clone
try:
    from app.utils.secretvars import setSecretVars
    setSecretVars()
except:
    pass

ca = certifi.where()

app = Flask(__name__)
#app.jinja_options['extensions'].append('jinja2.ext.do')
app.jinja_env.add_extension('jinja2.ext.do')
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY") or os.urandom(20)
# you must change the next line to be link to your database at mongodb.com
#connect("ccpa", host=f"{os.environ.get('mongodb_host')}/ccpa?retryWrites=true&w=majority", tlsCAFile=ca)
#connect("ccpa", host=f"{os.environ.get('mongodb_host')}/ccpa?retryWrites=true&w=majority", tls=True, tlsCertificateKeyFile="combined.pem")
connect("ccpa", host=f"{os.environ.get('mongodb_host')}/ccpa?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true", tlsCAFile=ca)

# Sandbox DB
# connect("otdatasb", host=f"{os.environ.get('mongodb_host')}/otdatasb?retryWrites=true&w=majority")

# User session management setup
# https://flask-login.readthedocs.io/en/latest
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

moment = Moment(app)

app.jinja_env.filters['quote_plus'] = lambda u: quote_plus(u)

def base64encode(img):

    image = base64.b64encode(img)
    image = image.decode('utf-8')
    return image

# Function to format phone numbers for UI
def formatphone(phnum):
    phnum = str(phnum)
    phnum = f"({phnum[0:3]}) {phnum[3:6]}-{phnum[6:]}"
    return phnum

# Function to format phone numbers to ints
def formatphonenums(phstr):
    phstr = re.sub("[^0-9]", "", phstr)

    return (phstr)




def typeerror(input):
    """Custom filter"""
    print("bob")
    return input.upper()

loader = jinja2.FileSystemLoader('/tmp')
env = jinja2.Environment(autoescape=True, loader=loader)
env.filters['typeerror'] = typeerror
# temp = env.get_template('template.html')
# temp.render(name="testing")

app.jinja_env.globals.update(base64encode=base64encode, formatphone=formatphone, formatphonenums=formatphonenums, typeerror=typeerror)


from .routes import *

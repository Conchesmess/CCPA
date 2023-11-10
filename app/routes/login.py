
# Python standard libraries
import json
from app import app, login_manager
from flask import redirect, request, url_for, flash, session, Markup
from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)
import requests
from app.classes.data import User
from app.utils.secrets import getSecrets
import mongoengine.errors
from .scopes import scopes_ousd
from .credentials import GOOGLE_CLIENT_CONFIG

import google.oauth2.credentials                
import google_auth_oauthlib.flow                
import googleapiclient.discovery   
from oauthlib.oauth2 import WebApplicationClient
from .portfolio import deletegfiles, createStudentFoldersFromReq


#get all the credentials for google
secrets = getSecrets()

admins = ["stephen.wright@ousd.org"]

crew = ["jerica.coffey@ousd.org","gina.chaulklin@ousd.org","ali.king@ousd.org","s_luis.cardenas@ousd.org","s_lorenzo.anthony@ousd.org","s_mehki.williamsmcgriff@ousd.org","s_alis.zuniga@ousd.org","s_adiel.zuniga@ousd.org"]

# OAuth2 client setup
client = WebApplicationClient(secrets['GOOGLE_CLIENT_ID'])

@app.before_request
def before_request():

    # this checks if the user requests http and if they did it changes it to https
    if not request.is_secure:
        url = request.url.replace("http://", "https://", 1)
        code = 301
        return redirect(url, code=code)

    # Create a list of all the paths that do not need authorization or are part of authorizing
    # so that each path this is *not* in this list requires an authorization check.
    # If you have urls that you want your user to be able to see without logging in add them here.
    # TODO create a decorator or something for this
    # TODO could just prefix the url with "/stu/" for studentpaths
    unauthPaths = ['/','/home','/authorize','/login','/static','/logout','/revoke','/msgreply','/msgstatus']   
    studentPaths = ['/portfolio','/my','/internship','/ontimeperc','/gclass','/project','/myprojects','/getgclasses','/comp/','/compborrow','/student','/breaks','/classdash','/assignments','/help','/breakstart','/postgrad','/cc','/plan','/profile','/editprofile','/addadult','/editadult','/deleteadult','/sendstudentemail','/checkin','/deletecheckin','/editgclass','/deletegclass','/gclasses','/missingassignmentsstu'] 
    # this is some tricky code designed to send the user to the page they requested even if they have to first go through
    # a authorization process.

    # find the first path argument in the URL
    reqPath = request.path
    basePath = reqPath.split('/')
    basePath = '/'+basePath[1]

    try: 
        session['return_URL']
    except:
        if basePath not in ['/login','/static','/authorize','/favicon.ico']:
            session['return_URL'] = reqPath
    else:
        if session['return_URL'] != reqPath and basePath not in ['/login','/static','/authorize']:
            session['return_URL'] = reqPath

    if basePath not in unauthPaths:
        if current_user.is_anonymous:
            return redirect(url_for('login'))
        elif current_user.role.lower() == "student" and basePath not in studentPaths:
            flash("Students are not authorized to see that page.")
            session['return_URL'] = "/"
            return redirect(url_for("index"))


# When a route is decorated with @login_required and fails this code is run
# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.unauthorized_handler
@login_manager.unauthorized_handler
def unauthorized():
    flash("You must be logged in to access that content.")
    return redirect(url_for('index'))

# Flask-Login helper to retrieve a user object from our db
# https://flask-login.readthedocs.io/en/latest/#flask_login.LoginManager.user_loader
@login_manager.user_loader
def load_user(id):
    try:
        return User.objects.get(pk=id)
    except mongoengine.errors.DoesNotExist:
        flash("Something strange has happened. This user doesn't exist. Please click logout.")
        return redirect(url_for('index'))

def get_google_provider_cfg():
    return requests.get(secrets['GOOGLE_DISCOVERY_URL']).json()

@app.route("/login")
def login():
    if current_user:
        logout_user()
    return redirect(url_for("authorize"))


@app.route("/login/callback")
def callback():
    session['code'] = request.args.get("code")
    flow = google_auth_oauthlib.flow.Flow.from_client_config(client_config=GOOGLE_CLIENT_CONFIG, scopes=scopes_ousd)
    flow.redirect_uri = url_for('callback', _external=True)
    authorization_response = request.url

    # TODO It breaks here on Google Cloud Run
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    session['credentials'] = credentials_to_dict(credentials)
    oauth2_client = googleapiclient.discovery.build('oauth2','v2',credentials=credentials)
    userinfo_response = oauth2_client.userinfo().get().execute()
    session['gdata'] = userinfo_response

    if userinfo_response['hd'] != "ousd.org":
        flash("You must have an ousd.org email account to access this site.")
        return redirect(url_for("index"))

    if userinfo_response['verified_email']:
        gid = userinfo_response['id']
        gmail = userinfo_response["email"]
        gprofile_pic = userinfo_response["picture"]
        gname = userinfo_response["name"]
        gfname = userinfo_response["given_name"]
        glname = userinfo_response["family_name"]
    else:
        flash("User email not available or not verified by Google.")
        return redirect(url_for('index'))

    
    # Get user from DB or create new user
    try:
        thisUser=User.objects.get(oemail=gmail)
    except mongoengine.errors.DoesNotExist:
        if userinfo_response['hd'] == "ousd.org":
            thisUser = User(
                gid=gid, 
                gname=gname, 
                oemail=gmail, 
                gprofile_pic=gprofile_pic,
                fname = gfname,
                lname = glname
            )
            thisUser.save()
            thisUser.reload()
        else:
            flash("You must have an ousd.org email to login to this site.")
            return redirect(url_for('index'))
    else:
        thisUser.update(
            gid=gid, 
            gname=gname, 
            gprofile_pic=gprofile_pic,
            fname = gfname,
            lname = glname
        )
    thisUser.reload()

    # Begin user session by logging the user in
    login_user(thisUser)

    if current_user.oemail[:2] == "s_":
        session['role'] = 'Student'
        if current_user.role != "Student":
            current_user.update(role = "Student")
    else:
        session['role'] = "Teacher"
        if current_user.role != "Teacher":
            current_user.update(role = "Teacher")

    if current_user.oemail == 'stephen.wright@ousd.org':
        response = deletegfiles()
        if response:
            flash(f'deleted: {response}')
        response = createStudentFoldersFromReq()
        if response:
            flash(f"folders created: {response}")
        
    # Send user back to homepage
    return redirect(session['return_URL'])
    # return redirect(url_for('index'))

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

# Do not edit anything in this route.  This is just for google authentication
@app.route('/revoke')
def revoke():
    if 'credentials' not in session:
        return redirect(url_for('authorize'))

    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    session['credentials'] = credentials_to_dict(credentials)

    revoke = requests.post('https://accounts.google.com/o/oauth2/revoke',
        params={'token': credentials.token},
        headers = {'content-type': 'application/x-www-form-urlencoded'})

    status_code = getattr(revoke, 'status_code')
    if status_code == 200:
        session['revokereq']=1
        flash(Markup(f"Revoke request has been processed. You can now <a href='/logout'>logout.</a>"))
        return redirect('/')
        #return redirect('/logout')
    else:
        flash('An error occurred when trying to revoke the privledges you granted to Google.')
        return redirect('/')

# Do not edit anything in this function.  This is just for google authentication
def credentials_to_dict(credentials):
    return {'token': credentials.token,
          'refresh_token': credentials.refresh_token,
          'token_uri': credentials.token_uri,
          'client_id': credentials.client_id,
          'client_secret': credentials.client_secret,
          'scopes': credentials.scopes
          }

@app.route('/authorize')
def authorize():
    # Intiiate login request
    flow = google_auth_oauthlib.flow.Flow.from_client_config(client_config=GOOGLE_CLIENT_CONFIG, scopes=scopes_ousd)
    flow.redirect_uri = url_for('callback', _external=True)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
    return redirect(authorization_url)
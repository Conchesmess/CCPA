from flask.helpers import url_for
from app import app
from flask import render_template, redirect, flash, session
from app.classes.data import CheckIn, User,Help,Role,College, Project
from mongoengine import Q
import requests
import time
import pandas as pd
from mongoengine.errors import NotUniqueError, DoesNotExist
from mongoengine import Q


@app.route('/projToRobotics')
def projToRobotics():
    projs = Project.objects()
    for proj in projs:
        proj.course = "Robotics DE"
        proj.save()
    return render_template('index.html')

@app.route('/setTSRolesAll')
def setTSRoles():
    users = User.objects()
    studentOBJ=Role.objects.get(name='student')
    teacherOBJ=Role.objects.get(name='teacher')

    t=len(users)
    
    for i,user in enumerate(users):
        if user.oemail[0:2]  == 's_':
            if not studentOBJ in user.roles:
                user.roles.append(studentOBJ)
                user.save()
                print(f's:{i}:{t}')
        else:
            if not teacherOBJ in user.roles:
                user.roles.append(teacherOBJ)
                user.save()
                print(f't:{i}:{t}')

    return render_template('index.html')

@app.route('/setadminrole/<email>')
def setAdminRole(email):
    adminOBJ=Role.objects.get(name='admin')
    user = User.objects.get(oemail=email)
    user.roles.append(adminOBJ)
    user.save()

    return render_template('index.html')

@app.route('/removerole/<name>/<email>')
def removeRole(name,email):
    OBJ=Role.objects.get(name=name)
    user = User.objects.get(oemail=email)
    user.roles.remove(OBJ)
    user.save()
    return render_template('index.html')


@app.route('/nolatlon')
def fixapt():
    users = User.objects(lat=None, ustreet__exists = True)
    total = len(users)
    for i,user in enumerate(users):
        print(f"{i}/{total} {user.ustreet} {user.ustreet2}")
    return render_template('index.html')

@app.route('/advlist')
def advlist():
    users = User.objects().order_by('advisor')
    for user in users:
        print(user.advisor,user.fname,user.lname)

    return render_template("index.html")

@app.route('/setrole')
def setrole():
    users = User.objects()
    nums = len(users)
    
    for i,user in enumerate(users):
        print(f"{i}/{nums}")
        if user.oemail[:2] == "s_":
            user.update(
                role="student"
            )
        else:
            user.update(
                role="teacher"
            )

    return render_template("index.html")


@app.route("/addadvisors")
def addadvisors():
    advsDF = pd.read_csv('./app/static/csv/stu-aeriesid-advisor-names-2024-25.csv', quotechar='"')
    advsDict = advsDF.to_dict('index')
    num = len(advsDict)
    for i,adv in enumerate(advsDict):
        adv = advsDict[adv]
        try:
            stu = User.objects.get(aeriesid = adv['aeriesid'])
        except:
            flash(f"Stu with id {adv['aeriesid']} does not exist")
        else:
            stu.update(
                advisor = str(adv['advisor'])
            )
        print(f"{i}/{num}")
    return render_template("index.html")


@app.route("/updateNewAlum")
def updateNewAlum():
    stus = User.objects(grade = 12)
    stuIDsDF = pd.read_csv("./app/static/csv/CCPAAllStus2023-24AeriesIDOnly.csv")
    stusDict = stuIDsDF.to_dict('index')
    currStusAeriesIDs = list(stusDict.values())
    currSrsList = []
    for item in currStusAeriesIDs:
        currSrsList.append(list(item.values())[0])
    for stu in stus:
        if not stu.aeriesid in currSrsList:
            stu.update(grade = 13)

    return render_template("index.html")


@app.route("/importusers")
def importusers():
    # Aeries Query: LIST STU FN LN ID NID GN GR CY ST ZC AD PG PEM FK TL FW MW 
    stusDF = pd.read_csv('./app/static/csv/D3Stus2024-25.csv', quotechar='"')
    stusDict = stusDF.to_dict('index')
    num = len(stusDict)
    for i,row in enumerate(stusDict):
        row = stusDict[row]
        print(f"{i}/{num}")
        try:
            stu = User.objects.get(oemail = row['oemail'])
        except:
            stu = User(
                oemail = row['oemail'],
                aeriesid = row['aeriesid'],
                afname = row['afname'],
                alname = row['alname'],
                fname = row['afname'],
                lname = row['alname'],
                aphone = str(row['aphone']),
                aadults = row['aadults'],
                aadultemail = str(row['aadultemail']),
                aadult1phone = str(row['aadult1phone']),
                aadult2phone = str(row['aadult2phone']),
                astreet = row['astreet'],
                acity = row['acity'],
                astate = row['astate'],
                azipcode = row['azipcode'],
                agender = row['agender'],
                afamkey = row['afamkey'],
                grade = row['grade']
            )
            stu.save()
        else:
            stu.update(
                aeriesid = row['aeriesid'],
                afname = row['afname'],
                alname = row['alname'],
                fname = row['afname'],
                lname = row['alname'],
                aphone = str(row['aphone']),
                aadults = row['aadults'],
                aadultemail = str(row['aadultemail']),
                aadult1phone = str(row['aadult1phone']),
                aadult2phone = str(row['aadult2phone']),
                astreet = row['astreet'],
                acity = row['acity'],
                astate = row['astate'],
                azipcode = row['azipcode'],
                agender = row['agender'],
                afamkey = row['afamkey'],
                grade = row['grade']
            )
    
    return render_template("index.html")


@app.route('/addlatlon')
def addlatlon():

    query = Q(astreet__exists=True) & Q(acity__exists=True) & Q(astate__exists=True) & Q(azipcode__exists=True)

    users = User.objects(query)
    total = len(users)
    for i,user in enumerate(users):

        if user.ustreet:
            street = user.ustreet
        else:
            street = user.astreet

        if user.ucity:
            city = user.ucity
        else:
            city = user.acity

        if user.ustate:
            state = user.ustate
        else:
            state = user.astate

        if user.uzipcode:
            zipcode = user.uzipcode
        else:
            zipcode = user.azipcode

        url = f"https://nominatim.openstreetmap.org/search?street={street}&city={city}&state={state}&postalcode={zipcode}&format=json&addressdetails=1&email=stephen.wright@ousd.org"
        r = requests.get(url)
        try:
            r = r.json()
        except:
            print(f"{i}/{total}: failed for {user.fname} {user.lname}")
        else:
            if len(r) != 0:
                user.lat = float(r[0]['lat'])
                user.lon = float(r[0]['lon'])
                user.save()
                print(f"{i}/{total}: {user.lat} {user.lon}")
                time.sleep(2)
            else:
                user.lat = 0
                user.lon = 0
                user.save()
                print(f"{i}/{total}: {user.lat} {user.lon}")
                time.sleep(2)
    return render_template("index.html")

@app.route('/importadvisors')
def importadvisors():
    advsDF = pd.read_csv('./app/static/csv/stu-aeriesid-advisor-names-2024-25.csv', quotechar='"')
    advsDict = advsDF.to_dict('index')
    num = len(advsDict)
    for i in range(num):
        row = advsDict[i]
        try:
            stu = User.objects.get(aeriesid = row['aeriesid'])
        except DoesNotExist:
            flash(f"{row['aeriesid']} does not exist")
        else:
            stu.update(
                advisor = row['tname']
            )
            print(f"{i}/{num}: {stu.fname} {stu.lname} {row['tname']}")

    return render_template('index.html')

@app.route('/removeadvisors')
def removeadvisors():
    advsDF = pd.read_csv('./app/static/csv/stu-aeriesid-advisor-names-2024-25.csv', quotechar='"')
    advsDict = advsDF.to_dict('index')
    num = len(advsDict)
    stus = User.objects()
    idsList = []
    for i in range(num):
        row = advsDict[i]
        idsList.append(row['aeriesid'])
    idsSet = set(idsList)
    for stu in stus:
        if stu.aeriesid not in idsSet:
            stu.advisor = ""
            try:
                if stu.grade < 13:
                    stu.grade = 0
            except:
                print(f"{stu.fname} {stu.lname} no grade.")
            else:
                stu.save()
                stu.reload()
                print(f"{stu.fname} {stu.lname}{stu.grade}")

    return render_template('index.html')

@app.route('/importcolleges')
def importcolleges():
    colsDF = pd.read_csv('./app/static/csv/uc-cs.csv', quotechar='"')
    colsDict = colsDF.to_dict('index')

    num = len(colsDict)
    for i,row in enumerate(colsDict):
        row = colsDict[row]
        print(f"{i}/{num}: {row['name']}")
        newColl = College(
            unitid = row['unitid'],
            coltype = row['coltype'],
            name = row['name'],
            street = row['street'],
            city = row['city'],
            state = "CA",
            zipcode = row['zipcode'],
            lat = row['lat'],
            lon = row['lon'],
            web = row['web'],
            pubpriv = "public",
            degree = row['degree']   
        )
        try:
            newColl.save()
        except NotUniqueError:
            flash(f"{row['name']} already exists.")
        except Exception as error:
            print(f"There was an error: {error}")

    return render_template('index.html')

@app.route('/coltypes')
def coltypes():
    cols = College.objects()
    types = []
    for col in cols:
        types.append(col.coltype)
    types = set(types)
    print(types)
    return render_template('index.html')

@app.route('/toCCC')
def toCCC():
    cols = College.objects(coltype = "ccc")
    for col in cols:
        col.update(coltype = "CCC")
    return render_template('index.html')

@app.route('/withdrawls')
def withdrawls():
    wds = User.objects(grade = 0)
    for stu in wds:
        if stu.has_role('student'):
            print(stu.fname)
    return render_template('index.html')


# @app.route('/deleteopenhelps')
# def deleteopenhelps():
#     statusList = ['asked','offered']
#     openHelps = Help.objects(status__in = statusList)
#     print(len(openHelps))
#     openHelps.delete()
#     openHelps = Help.objects(status__in = statusList)
#     print(len(openHelps))

#     return render_template('index.html')


# @app.route('/updategclasses')
# def updategclasses():
#     users = User.objects(gclasses__exists = True )
#     for j,user in enumerate(users):
#         print(f"{j}/{len(users)} {user.fname} {user.lname}")
#         changed = False
#         for i,otclass in enumerate(user.gclasses):
#             if otclass.gclassroom:
#                 print(f"{i}/{len(user.gclasses)} {otclass.gclassroom.gclassdict['name']}")
#                 if otclass.classname:
#                     tempName = otclass.classname
#                 else:
#                     tempName = otclass.gclassroom.gclassdict['name']
#                 #print(f"tempName: {tempName}")
#                 if otclass.status and otclass.status.lower() == "active":
#                     tempStatus = otclass.status
#                 else:
#                     tempStatus = "Inactive"
#                 #print(f"tempStatus: {tempStatus}")
#                 if not otclass.classname or not otclass.status:
#                     user.gclasses.filter(gclassid = otclass.gclassid).update(
#                         classname = tempName, 
#                         status = tempStatus
#                     )
#                     changed = True
#         if changed:
#             user.save()
#             print('saved')
#         else:
#             print('not saved')
#     return render_template('index.html')
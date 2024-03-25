from app import app
from app.utils.secrets import getSecrets
import requests
from flask import render_template, flash, redirect, url_for
import requests
from flask_login import current_user
from app.classes.data import User, Role, require_role, College, CollegeEnrollment
from app.classes.forms import AddressForm, CollegeForm
from flask_login import login_required
from mongoengine import Q
import datetime as dt
from bson import ObjectId
# pandas import read_csv

def getCollegeNames():
    colleges=College.objects()

    collegeNames = []

    for college in colleges:
        collegeNames.append(f"{college.name} ({college.unitid})")
    
    return collegeNames

def updateLatLon(address,user):
    # get your email address for the secrets file
    secrets=getSecrets()
    # call the maps API with the address
    url = f"https://nominatim.openstreetmap.org/search?street={address.streetAddress}&city={address.city}&state={address.state}&postalcode={address.zipcode}&format=json&addressdetails=1&email={secrets['MY_EMAIL_ADDRESS']}"
    # get the response from the API
    r = requests.get(url)
    # Find the lat/lon in the response
    try:
        r = r.json()
    except:
        flash("unable to retrieve lat/lon")
        return(address)
    else:
        if len(r) != 0:
            # update the database
            user.addresses.filter(oid=address.oid).update(
                lat = float(r[0]['lat']),
                lon = float(r[0]['lon'])
            )
            user.save()
            user.reload()
            flash(f"address lat/lon updated")
            return(user.addresses.get(oid=address.oid))
        else:
            flash('unable to retrieve lat/lon')
            return(address)


@app.route('/college/map')
@login_required
def alumniMap():

    alumObj = Role.objects.get(name="alum")
    studentObj = Role.objects.get(name="student")
    query = Q(roles__contains=alumObj) | Q(roles__contains=studentObj)
    students = User.objects(query)
    studentEnrollments = CollegeEnrollment.objects(student__in=students)    

    teacherObj = Role.objects.get(name="teacher")
    teachers = User.objects(roles__contains=teacherObj)
    teacherEnrollments = CollegeEnrollment.objects(student__in=teachers)
    
    ccc = College.objects(coltype="ccc")
    cc = College.objects(coltype="cc & Trade")
    csu = College.objects(coltype="csu")
    uc = College.objects(coltype="uc")
    other = College.objects(coltype="nan")

    return render_template('addresses/college_map.html',studentEnrollments=studentEnrollments,teacherEnrollments=teacherEnrollments,ccc=ccc,csu=csu,uc=uc,other=other,cc=cc)


@app.route('/college/new/<uid>',methods=['GET','POST'])
@app.route('/college/new',methods=['GET','POST'])
@login_required
def collegeNew(uid=None):
    if not uid:
        user = current_user
    elif current_user.has_role('admin'):
        user = User.objects.get(pk=uid)
    else:
        flash('You do not have the right role to add an address for a user that is not you.')
        return redirect(url_for('profile'))

    form = CollegeForm()

    collegeNames = getCollegeNames()
    
    if form.validate_on_submit():
        unitid = form.name.data[-7:-1]
        print(unitid)
        college = College.objects.get(unitid=unitid)
        CollegeEnrollment(
            college = college,
            student = user,
            grad_year = form.gradyear.data
        ).save()
        return redirect(url_for('profile'))

    collegeNames=getCollegeNames()
        
    return render_template('addresses/new_college_form.html',form=form, collegeNames=collegeNames, user=user)

@app.route('/college/delete/<ceid>')
def collegeEnrollmentDelete(ceid):
    ce = CollegeEnrollment.objects.get(pk=ceid)

    if current_user == ce.student or current_user.has_role('admin') :
        ce.delete()
        flash("The College Enrollment has been deleted.")

    else:
        flash('You do not have the right privleges to delete this college enrollment.')
    
    return redirect(url_for('profile'))


@app.route('/address/new/<uid>',methods=['GET','POST'])
@app.route('/address/new',methods=['GET','POST'])
@login_required
def address_new(uid=None):
    if not uid:
        user = current_user
    elif current_user.has_role('admin'):
        user = User.objects.get(pk=uid)
    else:
        flash('You do not have the right role to add an address for a user that is not you.')
        return redirect(url_for('profile'))

    form = AddressForm()

    if form.validate_on_submit():
        address = user.addresses.create(
            oid = ObjectId(),
            name = form.name.data,
            streetAddress = form.streetAddress.data,
            city = form.city.data,
            state = form.state.data,
            zipcode = form.zipcode.data,
            addresstype = form.addresstype.data
        )
        user.save()
        
        updateLatLon(address,user)

        return redirect(url_for('profile'))

        
    return render_template('addresses/address_form.html',form=form,user=user)

@app.route('/address/delete/<aid>/<uid>')
@app.route('/address/delete/<aid>')
def address_delete(aid,uid=None):
    if not uid:
        user = current_user
    elif current_user.has_role('admin'):
        user = User.objects.get(pk=uid)
    else:
        flash("You don't have the right role to delete another user's address.")
        return redirect(url_for('profile'))

    user.addresses.filter(oid=aid).delete()
    user.save()
    
    return redirect(url_for('profile'))


# @app.route("/importcolleges")
# def importcolleges():
#     colsDF = read_csv('./app/static/ccc.csv', quotechar='"')
#     colsDict = colsDF.to_dict('index')
#     num = len(colsDict)
#     for i,row in enumerate(colsDict):
#         row=colsDict[row]
#         editCol = College.objects.get(unitid=row['unitid'])
#         editCol.update(
#             coltype=row['coltype']
#         )

#         print(f"{i}/{num}")

#     return render_template("index.html")
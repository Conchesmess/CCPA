from app import app
from flask import render_template, redirect, flash, url_for
from app.classes.data import Internship, User, Internship_Timesheet, Internship_Timesheet_Day, Signature
from app.classes.forms import InternshipForm, TextAreaForm, TimeSheetForm, SignatureForm
from datetime import datetime as dt
from flask_login import current_user
import phonenumbers
import requests
from mongoengine.errors import NotUniqueError
from .login import crew, admins
import datetime as dt
import pytz
from bson.objectid import ObjectId

# TODO
# 1. Hide edit and delete links
# 2. remove crew list from login.py and use the crew list on the Internship
# 3. or better yet, install the roles and decorators
# 4. create a way for the contact to use their registered email address to "sign" a timesheet

# this is the route used by the signer
@app.route('/sig/<sigID>')
def getsigts(sigID):
    sig = Signature.objects.get(pk = sigID)
    pass

@app.route('/sig/new/<tsID>')
def signew(tsID):
    form = SignatureForm()
    ts = Internship_Timesheet.objects.get(pk = tsID)

    if ts.intern != current_user:
        flash("You can't create a signature request if you are not the intern.")
        return redirect(url_for('timesheet',tsID=tsID))

    if form.validate_on_submit():
        Signature(
            emailOut = form.emailOut.data,
            intern = current_user,
            timesheet = ts,
            status = "New"
        )

        return redirect(url_for('timesheet'), tsID=tsID)

    return render_template('internship/timesheetsig.html',form=form,ts=ts)

@app.route('/sig/send/<sigID>')
def sigsend(sigID):
    pass


@app.route('/internship/<intID>', methods=['GET', 'POST'])
def internship(intID):

    form = TextAreaForm()
    iship = Internship.objects.get(pk=intID)
    timesheets = Internship_Timesheet.objects(internship=iship)

    if form.validate_on_submit():
        if current_user.oemail in admins or current_user.oemail in crew:
            emails = form.csv.data.split(',')

            for email in emails:
                try:
                    student = User.objects.get(oemail=email.strip())
                except:
                    flash(f"{email} does not exist in the database")
                else:
                    if student not in iship.ccpa_students:
                        iship.ccpa_students.append(student)
                        iship.save()
            form.csv.data = ""
        else:
            flash("You can't enroll students")

    return render_template('internship/internship.html',internship=iship, form=form, timesheets=timesheets)

@app.route('/internship/unenrollstu/<stuID>/<intID>')
def unenrollstu(stuID,intID):
    if current_user.oemail in admins or current_user.oemail in crew:
        stu = User.objects.get(pk=stuID)
        iship = Internship.objects.get(pk=intID)
        try:
            ts = Internship_Timesheet.objects.get(intern=stu,internship=iship)
        except:
            iship.update(
                pull__ccpa_students=stu
            )
            flash(f"{stu.fname} {stu.lname} was removed from this internship")
        else:
            flash(f"{stu.fname} {stu.lname} cannot be removed while they have a timesheet associated with this internship.")
    else:
        flash("You don't have privleges to do that.")
    return redirect(url_for('internship',intID=intID))

@app.route('/internship/list')
def internships():
    internships = Internship.objects()
    return render_template('internship/internships.html',internships=internships)

@app.route('/internship/map')
def internshipmap():
    internships=Internship.objects()
    return render_template('internship/internshipmap.html',internships=internships)


@app.route('/internship/delete/<intID>')
def internship_delete(intID):

    if current_user.oemail not in admins and current_user.oemail not in crew: 
        flash("You don't have privleges to delete.")
        return redirect(url_for('internship',intID=intID))

    intDelete = Internship.objects.get(pk=intID)

    if len(intDelete.ccpa_students) > 0:
        flash("You can't delete an internship while students are enrolled.")
        return redirect(url_for('internship',intID=intID))
    else:
        timesheets = Internship_Timesheet.objects(internship=intDelete)
        if len(timesheets) > 0:
            flash("You can't delete an internship that has timesheets.")
            return redirect(url_for('internship',intID=intID))

    siteName = intDelete.site_name
    intDelete.delete()
    flash(f"{siteName} deleted.")
    
    return redirect(url_for('internships'))


def validate_phone(phone):
    phone=f"+1{phone}"
    try:
        p = phonenumbers.parse(phone)
    except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
        print("except",p)
        return ValidationError('Invalid phone number')
    else:
        if not phonenumbers.is_valid_number(p):
            flash("number is not valid")
            print(p)
            return None
        return str(p.national_number)

def int_lat_lon(internship):

    if internship.street and internship.city and internship.state and internship.zipcode:

        url = f"https://nominatim.openstreetmap.org/search?street={internship.street}&city={internship.city}&state={internship.state}&postalcode={internship.zipcode}&format=json&addressdetails=1&email=stephen.wright@ousd.org"
        r = requests.get(url)

        try:
            r = r.json()
        except:
            flash('could not get lat/lon')
            pass
        else:
            if len(r) != 0:
                internship.update(
                    lat = float(r[0]['lat']),
                    lon = float(r[0]['lon'])
                    )
                flash('Updated lat/lon')
            else:
                flash('Could not get lat/lon for mapping.')

@app.route('/internship/new', methods=['GET', 'POST'])
def new_internship():

    if current_user.oemail in admins or current_user.oemail in crew:        

        form = InternshipForm()

        if form.validate_on_submit():
            phone = f"{form.phone_areacode.data}{form.phone_prefix.data}{form.phone_suffix.data}"
            if len(phone) > 0:
                phone = validate_phone(phone)
            else:
                phone = None

            contact_phone = f"{form.contact_phone_areacode.data}{form.contact_phone_prefix.data}{form.contact_phone_suffix.data}"
            if len(contact_phone) > 0:
                contact_phone = validate_phone(contact_phone)
            else:
                contact_phone = None

            new_internship = Internship(
                site_name = form.site_name.data,
                contact_fname = form.contact_fname.data,
                contact_lname = form.contact_lname.data,
                contact_email = form.contact_email.data,
                notes = form.notes.data,
                street = form.street.data,
                city = form.city.data,
                state = form.state.data,
                zipcode = form.zipcode.data
            )

            new_internship.save()

            if contact_phone:
                new_internship.update(contact_phone=contact_phone)            
                
            if phone:
                new_internship.update(phone=phone)

            if form.ccpa_staff.data:
                try:
                    ccpa_staff = User.objects.get(oemail=form.ccpa_staff.data)
                except:
                    flash("That staff member does not have an account on this site yet.")
                else:
                    new_internship.update(ccpa_staff = ccpa_staff)

            int_lat_lon(new_internship)

            return redirect(url_for('internship',intID=new_internship.id))

        return render_template('internship/internshipform.html',form=form)
    else:
        flash("You can't create internships.")
        return redirect(url_for('internships'))


@app.route('/internship/edit/<intID>', methods=['GET', 'POST'])
def edit_internship(intID):
    if current_user.oemail in admins or current_user.oemail in crew:        

        form = InternshipForm()
        editInt = Internship.objects.get(pk=intID)
        if form.validate_on_submit():

            phone = f"{form.phone_areacode.data}{form.phone_prefix.data}{form.phone_suffix.data}"
            if len(phone) > 0:
                phone = validate_phone(phone)
            else:
                phone = None

            contact_phone = f"{form.contact_phone_areacode.data}{form.contact_phone_prefix.data}{form.contact_phone_suffix.data}"
            if len(contact_phone) > 0:
                contact_phone = validate_phone(contact_phone)
            else:
                contact_phone = None

            editInt.update(
                site_name = form.site_name.data,
                contact_fname = form.contact_fname.data,
                contact_lname = form.contact_lname.data,
                contact_email = form.contact_email.data,
                notes = form.notes.data,
                street = form.street.data,
                city = form.city.data,
                state = form.state.data,
                zipcode = form.zipcode.data
            )

            if contact_phone and contact_phone != editInt.contact_phone:
                flash("updated contact phone")
                editInt.update(contact_phone=contact_phone)            
                
            if phone and phone != editInt.phone:
                flash("updated site phone")
                editInt.update(phone=phone)

            if form.ccpa_staff.data:
                try:
                    ccpa_staff = User.objects.get(oemail=form.ccpa_staff.data)
                except:
                    flash("That staff member does not have an account on this site yet.")
                else:
                    editInt.update(ccpa_staff = ccpa_staff)

            editInt.reload()
            int_lat_lon(editInt)

            return redirect(url_for('internship',intID=editInt.id))

        form.site_name.data =  editInt.site_name
        form.contact_fname.data = editInt.contact_fname
        form.contact_lname.data = editInt.contact_lname
        form.contact_email.data = editInt.contact_email
        form.ccpa_staff.data = editInt.ccpa_staff.oemail
        if editInt.contact_phone:
            form.contact_phone_areacode.data = editInt.contact_phone[:3]
            form.contact_phone_prefix.data = editInt.contact_phone[3:6]
            form.contact_phone_suffix.data = editInt.contact_phone[6:]
        form.notes.data = editInt.notes
        if editInt.phone:
            form.phone_areacode.data = editInt.phone[:3]
            form.phone_prefix.data = editInt.phone[3:6]
            form.phone_suffix.data = editInt.phone[6:]
        form.street.data = editInt.street
        form.city.data = editInt.city
        form.state.data = editInt.state
        form.zipcode.data = editInt.zipcode

        return render_template('internship/internshipform.html',form=form)
    else:
        flash("You can't edit internships.")
        return redirect(url_for('internship',intID=editInt.id))

@app.route('/internship/newtimesheet/<intID>')
def newtimesheet(intID):
    iship = Internship.objects.get(pk=intID)

    newTS = Internship_Timesheet(
        internship = iship,
        intern = current_user
        )

    try:
        newTS.save()
    except NotUniqueError:
        flash("You already have a timesheet!")

    return redirect(url_for('internship',intID=intID))

@app.route('/internship/timesheet/<tsID>/<p>', methods=['GET', 'POST'])
@app.route('/internship/timesheet/<tsID>', methods=['GET', 'POST'])
def timesheet(tsID,p=''):
    ts = Internship_Timesheet.objects.get(pk=tsID)
    form = TimeSheetForm()
    if form.validate_on_submit() and current_user == ts.intern:

        if form.start_time_am_pm.data.lower() == "pm" and int(form.start_time_hr.data) < 12:
            start_hr = int(form.start_time_hr.data) + 12
        else:
            start_hr = int(form.start_time_hr.data)

        if form.end_time_am_pm.data.lower() == "pm" and int(form.end_time_hr.data) < 12:
            end_hr = int(form.end_time_hr.data) + 12
        else:
            end_hr = int(form.end_time_hr.data)

        start_datetime = dt.datetime(
            form.date.data.year,
            form.date.data.month,
            form.date.data.day,
            start_hr,
            int(form.start_time_min.data),
            0)

        start_datetime = pytz.timezone('America/Los_Angeles').localize(start_datetime)

        start_datetime = start_datetime.astimezone(pytz.utc)

        if start_datetime > dt.datetime.utcnow().astimezone(pytz.utc):
            flash("You can't add a date that is in the future!")
            return redirect(url_for('timesheet', tsID = tsID))

        end_datetime = dt.datetime(
            form.date.data.year,
            form.date.data.month,
            form.date.data.day,
            end_hr,
            int(form.end_time_min.data),
            0)

        end_datetime = pytz.timezone('America/Los_Angeles').localize(end_datetime)

        diff = end_datetime-start_datetime

        hrs = diff.total_seconds()/60/60
        
        if hrs <= 0:
            flash("You can't create a entry with zero or negative time.  Make sure the end time comes AFTER the start time!")
        else:
            ts.days.create(
                oid = ObjectId(),
                start_datetime = start_datetime,
                end_datetime = end_datetime,
                hrs=hrs,
                desc=form.desc.data
                )
            ts.save()

    totalHrs = 0
    for day in ts.days:
        totalHrs += day.hrs
    ts.update(totalHrs=totalHrs)
    ts.reload()

    if p == 'print':
        return render_template("internship/timesheetprint.html", ts=ts)
    else:
        return render_template("internship/timesheet.html", ts=ts, form=form)


@app.route('/internship/deletetsday/<tsID>/<dayOID>')
def deletetsday(tsID,dayOID):
    ts = Internship_Timesheet.objects.get(pk=tsID)
    days = ts.days.filter(oid=dayOID)
    if len(days) == 1:
        days.delete()
        ts.save()
    else:
        "There are more than one day with that OID.  That shouldn't happen!"

    return redirect(url_for('timesheet',tsID=tsID))

@app.route('/internship/tsdelete/<tsID>')
def tsdelete(tsID):
    ts = Internship_Timesheet.objects.get(pk=tsID)
    if len(ts.days) > 0:
        flash("You can't delete a timesheet that has data.")
        return redirect(url_for('internship',intID = ts.internship.id))
    else:
        ts.delete()
        flash("Timesheet Deleted.")
        return redirect(url_for('internship',intID = ts.internship.id))
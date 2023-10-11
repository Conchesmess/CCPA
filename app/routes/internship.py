from app import app
from flask import render_template, redirect, flash, url_for
from app.classes.data import Internship, User, Internship_Timesheet, Internship_Timesheet_Day
from app.classes.forms import InternshipForm, TextAreaForm, TimeSheetForm
from datetime import datetime as dt
from flask_login import current_user
import phonenumbers
import requests
from mongoengine.errors import NotUniqueError
from .login import crew, admins
import datetime as dt
from bson.objectid import ObjectId

# TODO
# 1. Hide edit and delete links
# 2. remove crew list from login.py and use the crew list on the Internship
# 3. or better yet, install the roles and decorators
# 4. create a way for the contact to use their registered email address to "sign" a timesheet
# 5. Make deleting an internship impossible if students are enrolled and timesheets are attached.

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
        iship.update(
            pull__ccpa_students=stu
        )
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
    if current_user.oemail in admins or current_user.oemail in crew:        
        intDelete = Internship.objects.get(pk=intID)
        flash(f"{intDelete.site_name} deleted.")
        intDelete.delete()
    else:
        flash("You don't have privleges to delete.")
    
    return redirect(url_for('internships'))


def validate_phone(phone):
    phone=f"+1{phone}"
    try:
        p = phonenumbers.parse(phone)
        if not phonenumbers.is_valid_number(p):
            return ValueError()
    except (phonenumbers.phonenumberutil.NumberParseException, ValueError):
        return ValidationError('Invalid phone number')
    else:
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
            phone = f"{form.contact_phone_areacode.data}{form.phone_prefix.data}{form.phone_suffix.data}"
            if len(phone) > 0:
                phone = validate_phone(phone)
                print(type(phone))
            else:
                phone = ""

            contact_phone = f"{form.contact_phone_areacode.data}{form.contact_phone_prefix.data}{form.contact_phone_suffix.data}"
            if len(contact_phone) > 0:
                contact_phone = validate_phone(contact_phone)
            else:
                contact_phone = ""

            new_internship = Internship(
                site_name = form.site_name.data,
                contact_fname = form.contact_fname.data,
                contact_lname = form.contact_lname.data,
                contact_email = form.contact_email.data,
                contact_phone = contact_phone,
                notes = form.notes.data,
                phone = phone,
                street = form.street.data,
                city = form.city.data,
                state = form.state.data,
                zipcode = form.zipcode.data
            )

            new_internship.save()

            if form.ccpa_staff.data:
                try:
                    ccpa_staff = User.objects.get(oemail=form.ccpa_staff.data)
                except:
                    flash("That staff member does not have an account on this site yet.")
                else:
                    editInt.update(ccpa_staff = ccpa_staff)

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

            phone = f"{form.contact_phone_areacode.data}{form.phone_prefix.data}{form.phone_suffix.data}"
            if len(phone) > 0:
                phone = validate_phone(phone)
            else:
                phone = form.phone.data

            contact_phone = f"{form.contact_phone_areacode.data}{form.contact_phone_prefix.data}{form.contact_phone_suffix.data}"
            if len(contact_phone) > 0:
                contact_phone = validate_phone(contact_phone)
            else:
                contact_phone = form.contact_phone.data

            editInt.update(
                site_name = form.site_name.data,
                contact_fname = form.contact_fname.data,
                contact_lname = form.contact_lname.data,
                contact_email = form.contact_email.data,
                contact_phone = contact_phone,
                notes = form.notes.data,
                phone = phone,
                street = form.street.data,
                city = form.city.data,
                state = form.state.data,
                zipcode = form.zipcode.data
            )

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

@app.route('/internship/timesheet/<tsID>', methods=['GET', 'POST'])
def timesheet(tsID):
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

        end_datetime = dt.datetime(
            form.date.data.year,
            form.date.data.month,
            form.date.data.day,
            end_hr,
            int(form.end_time_min.data),
            0)

        diff = end_datetime-start_datetime

        hrs = diff.total_seconds()/60/60
        
        if hrs <= 0:
            flash("You can't create a entry with zero or negative time.  Make sure the end time comes AFTER the start time!")
        else:
            ts.days.create(
                oid = ObjectId(),
                start_datetime = start_datetime,
                end_datetime = end_datetime,
                hrs=hrs
                )
            ts.save()

    return render_template("internship/timesheet.html", ts=ts, form=form)


@app.route('/internship/deletetsday/<tsID>/<dayOID>')
def deletetsday(tsID,dayOID):
    ts = Internship_Timesheet.objects.get(pk=tsID)
    #get works but the resulting object does not have a delete() method
    #filter does have a delete method
    #day = ts.days.get(oid=dayOID)
    days = ts.days.filter(oid=dayOID)
    if len(days) == 1:
        days.delete()
        ts.save()
    else:
        "There are more than one day with that OID.  That shouldn't happen!"

    return redirect(url_for('timesheet',tsID=tsID))
from app import app
from flask import render_template, redirect, flash, url_for
from app.classes.data import Internship, User, Internshp_Timesheet, Internship_Timesheet_Day
from app.classes.forms import InternshipForm, TextAreaForm
from datetime import datetime as dt
from flask_login import current_user
import phonenumbers
import requests
from mongoengine.errors import NotUniqueError

@app.route('/internship/<intID>', methods=['GET', 'POST'])
def internship(intID):

    form = TextAreaForm()
    iship = Internship.objects.get(pk=intID)
    timesheets = Internshp_Timesheet.objects(internship=iship)
    if form.validate_on_submit():
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

    return render_template('internship/internship.html',internship=iship, form=form, timesheets=timesheets)

@app.route('/internship/unenrollstu/<stuID>/<intID>')
def unenrollstu(stuID,intID):
    stu = User.objects.get(pk=stuID)
    iship = Internship.objects.get(pk=intID)
    iship.update(
        pull__ccpa_students=stu
    )
    return redirect(url_for('internship',intID=intID))

@app.route('/internship/list')
def internships():
    internships = Internship.objects()
    return render_template('internship/internships.html',internships=internships)

@app.route('/internship/map')
def internshipmap():
    internships=Internship.objects()
    return render_template('internship/internshipmap.html',internships=internships)


@app.route('/deleteinternship/<intID>')
def internship_delete(intID):
    intDelete = Internship.objects.get(pk=intID)
    flash(f"{intDelete.site_name} deleted.")
    intDelete.delete()
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

@app.route('/internship/edit/<intID>', methods=['GET', 'POST'])
def edit_internship(intID):
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

@app.route('/internship/newtimesheet/<intID>')
def newtimesheet(intID):
    iship = Internship.objects.get(pk=intID)

    newTS = Internshp_Timesheet(
        internship = iship,
        intern = current_user
        )

    try:
        newTS.save()
    except NotUniqueError:
        flash("You already have a timesheet!")

    return redirect(url_for('internship',intID=intID))
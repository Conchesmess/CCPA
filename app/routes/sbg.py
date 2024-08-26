from app import app
from flask import render_template, redirect, session, flash, url_for, Markup, render_template_string, request
from app.classes.data import User
from app.classes.gclassroom import GoogleClassroom, GEnrollment, CourseWork, Standard
from app.classes.forms import AssignmentForm, StandardForm
from bson.objectid import ObjectId
import google.oauth2.credentials
import googleapiclient.discovery
from google.auth.exceptions import RefreshError
import google_auth_oauthlib.flow
from .credentials import GOOGLE_CLIENT_CONFIG
from .scopes import scopes_ousd
from .users import credentials_to_dict
from flask_login import current_user
import pandas as pd
from datetime import datetime as dt


# This function retreives all the assignments from Google and stores them in a dictionary
# field on the GoogleClassroom record in the database.
def getCourseWork(gclassid):
    pageToken = None
    assignmentsAll = {}
    assignmentsAll['courseWork'] = []
    if not "credentials" in session:
        return redirect('/authorize')
    elif not google.oauth2.credentials.Credentials(**session['credentials']).valid:
        return redirect('/authorize')
    else:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])

    session['credentials'] = credentials_to_dict(credentials)
    classroom_service = googleapiclient.discovery.build(
            'classroom',
            'v1',
            credentials=credentials,
            discoveryServiceUrl='https://classroom.googleapis.com/$discovery/rest?labels=DEVELOPER_PREVIEW&key=AIzaSyDz4K5HXeFqHzAFjhDNaXoogrSxo6x7ZHY'
        )
    try:
        topics = classroom_service.courses().topics().list(
            courseId=gclassid
            ).execute()
    except RefreshError:
        return "refresh"
    except Exception as error:
        x, y = error.args     # unpack args
        if isinstance(y, bytes):
            y = y.decode("UTF-8")
        errorDict = ast.literal_eval(y)
        if errorDict['error'] == 'invalid_grant':
            flash('Your login has expired. You need to re-login.')
            return "refresh"
        elif errorDict['error']['status'] == "PERMISSION_DENIED":
            flash("You do not have permission to get assignments from Google for this class.")
            return "refresh"
        else:
            flash(f"Got unknown Error: {errorDict}")
            return False
    try:
        topics = topics['topic']
    except:
        topics = None

    # Topic dictionary
    # [{'courseId': '450501150888', 'topicId': '487477497511', 'name': 'Dual Enrollment', 'updateTime': '2022-05-20T20:55:41.926Z'}, {...}]

    # TODO get all assignments and add as dict to gclassroom record
    while True:
        try:
            assignments = classroom_service.courses().courseWork().list(
                    courseId=gclassid,
                    pageToken=pageToken,
                    ).execute()
        except RefreshError:
            return "refresh"
        except Exception as error:
            x, y = error.args     # unpack args
            if isinstance(y, bytes):
                y = y.decode("UTF-8")
            errorDict = ast.literal_eval(y)
            if errorDict['error'] == 'invalid_grant':
                flash('Your login has expired. You need to re-login.')
                return "refresh"
            elif errorDict['error']['status'] == "PERMISSION_DENIED":
                return "refresh"
            else:
                flash(f"Got unknown Error: {errorDict}")
                return False

        try:
            assignmentsAll['courseWork'].extend(assignments['courseWork'])
        except (KeyError,UnboundLocalError):
            break
        else:
            pageToken = assignments.get('nextPageToken')
            if pageToken == None:
                break

    for ass in assignmentsAll['courseWork']:
        if topics:
            for i,topic in enumerate(topics):
                try:
                    ass['topicId']
                except:
                    ass['topicId'] = None
                if topic['topicId'] == ass['topicId']:
                    ass['topic'] = topic['name']
                    break
        try:
            # Using list because there is always only one rubric per assignment
            response = classroom_service.courses().courseWork().rubrics().list(
                    courseId=gclassid,
                    courseWorkId=ass['id'],
                    # Specify the preview version. Rubrics CRUD capabilities are
                    # supported in V1_20231110_PREVIEW and later.
                    previewVersion="V1_20231110_PREVIEW"
                ).execute()

            rubrics = response.get("rubrics", [])
            if not rubrics:
                ass['rubric'] = None
            else:
                ass['rubric'] = rubrics[0]

        except Exception as error:
            flash(f"An error occurred: {error}")

    gclassroom = GoogleClassroom.objects.get(gclassid=gclassid)
    gclassroom.update(courseworkdict = assignmentsAll, courseworkupdate = dt.utcnow())
    return assignmentsAll

# Standards
# Standards come from rubrics in Google Classroom. A rubric criteria that begins with <S> is a standard. Yu have to add the <s>
# to the criteria in Google Classroom

# TODO standards met for all students in a class
# save in GEnrollment?
@app.route('/rubrics/scores/students/<gclassid>')
def standards_scores_students():
    pass

# TODO for a gClass list all intended standards
# do this one last
@app.route('/standards/list/<gclassid>')
def standards_list(gclassid):
    pass

# TODO from the list of assignments with a rubric with standards click to see all students with met standards for that assignment
# create link on assignment list page
@app.route('/standards/scores/<gclassid>/<courseworkid>')
def standards_scores(gclassid,courseworkid):
    pass

# TODO find all astudsubs for a student in a class
@app.route('/studsubs/student/<gclassid>/<oemail>/<studentid>')
def studsubsstudent(gclassid,oemail,studentid):
    stu = User.objects.get(oemail=oemail)
    gclassroom = GoogleClassroom.objects.get(gclassid=gclassid)
    try:
        allstudsubs = gclassroom.studsubsdict['studsubs']
    except:
        allstudsubs = {}
    studsubs = []
    for subid in allstudsubs:
        sub = allstudsubs[subid]
        if sub['userId'] == studentid:
             studsubs.append(sub)

    coursework=gclassroom.courseworkdict['courseWork']
    cworkDF = pd.DataFrame(coursework)
    def link_to_title(row):
        return '<a href="'+row["alternateLink"]+'">'+row["title"]+'</a>'

    cworkDF['title'] = cworkDF.apply(link_to_title, axis=1)

    cworkDF.rename(columns={"id": "courseWorkId"}, inplace=True)

    studSubsDF = pd.DataFrame(studsubs)
    studSubsDF.drop(['courseId','id','userId','creationTime','updateTime','courseWorkType','previewVersion','draftGrade'],axis=1,inplace=True)

    studSubsDF = pd.merge(cworkDF,
                studSubsDF,
                on ='courseWorkId',
                how ='inner')

    studSubsDF.drop(['courseId','assignment','state_x','assignmentSubmission','alternateLink_x','submissionModificationMode','courseWorkId','creationTime','updateTime','dueTime','workType','assigneeMode','creatorUserId','topicId','materials'],axis=1,inplace=True)
    studSubsDF.rename(columns={'state_y':'state','alternateLink_y':'altLink'},inplace=True)

    def link_to_state(row):
        try:
            return '<a href="'+row["altLink"]+'">'+row["state"]+'</a>'
        except:
            return row['state']
    studSubsDF['state'] = studSubsDF.apply(link_to_state, axis=1)

    studSubsDF.drop(['altLink'],axis=1,inplace=True)

    def due_date(row):
        return f"{row['dueDate']['month']}/{row['dueDate']['day']}/{row['dueDate']['year']}"
    studSubsDF['dueDate'] = studSubsDF.apply(due_date, axis=1)

    def grade_category(row):
        return f"{row['gradeCategory']['name']}"
    studSubsDF['gradeCategory'] = studSubsDF.apply(grade_category, axis=1)

    def submission_history(row):
        gradeHistories=""
        for sub in row['submissionHistory']:
            try:
                sub['gradeHistory']
            except:
                pass
            else:
                if sub['gradeHistory']['gradeChangeType'] == 'ASSIGNED_GRADE_POINTS_EARNED_CHANGE':
                    gradeHistories=f"{gradeHistories}{sub['gradeHistory']['pointsEarned']}/{sub['gradeHistory']['maxPoints']}</br>"
        return gradeHistories
    studSubsDF['submissionHistory'] = studSubsDF.apply(submission_history,axis=1)
    


    studSubsDFHTML = studSubsDF.style\
        .format(precision=0)\
        .set_table_styles([
            {'selector': 'tr:hover','props': 'background-color: #cccccc; font-size: 1em;'},\
            {'selector': 'thead','props': 'height:100px'},\
            {'selector': 'th','props': 'background-color: #CCCCCC !important'}], overwrite=False)\
        .set_table_attributes('class="table table-sm"')  \
        .set_sticky(axis="columns",levels=0)\
        .hide(axis='index')\
        .to_html()
    studSubsDFHTML = Markup(studSubsDFHTML)

    return render_template('sbg/studentsubs.html',studsubs=studSubsDFHTML,stu=stu)


# this function exists to update or create active google classrooms for the current user
# Teacher or student
@app.route('/getgclasses')
def getgclasses():

    if not 'credentials' in session:
        return redirect(url_for('authorize'))
    elif not google.oauth2.credentials.Credentials(**session['credentials']).valid:
        return redirect(url_for('authorize'))
    else:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])

    classroom_service = googleapiclient.discovery.build('classroom', 'v1', credentials=credentials)
    gCourses = classroom_service.courses().list(courseStates='ACTIVE').execute()

    try:
        gCourses = classroom_service.courses().list(courseStates='ACTIVE').execute()
    except RefreshError:
        flash("When I asked for the courses from Google Classroom I found that your credentials needed to be refreshed.")
        return redirect('/authorize')
    else:
        gCourse = None
        gCourses = gCourses['courses']

    # Iterate through the classes
    for gCourse in gCourses:
        # get the teacher record
        try:
            # See if I can find a Google Teacher User
            GClassTeacher = classroom_service.userProfiles().get(userId=gCourse['ownerId']).execute()
        except:
            GClassTeacher = None

        # See if the teacher has a record on OTData site
        try:
            otdataGClassTeacher = User.objects.get(gid = gCourse['ownerId'])
        except:
            otdataGClassTeacher = None

        # Check to see if this course is saved in OTData
        try:
            otdataGCourse = GoogleClassroom.objects.get(gclassid = gCourse['id'])
        except:
            otdataGCourse = None

        # if the GCourse IS NOT in OTData and the teacher IS in the OTData
        if not otdataGCourse and otdataGClassTeacher:
            otdataGCourse = GoogleClassroom(
                gclassdict = gCourse,
                gteacherdict = GClassTeacher,
                gclassid = gCourse['id'],
                teacher = otdataGClassTeacher
            )
            otdataGCourse.save()

        # If there is NOT a teacher in OTData and NOT a course in OTData
        elif not otdataGCourse and not otdataGClassTeacher:
            otdataGCourse = GoogleClassroom(
                gclassdict = gCourse,
                gteacherdict = GClassTeacher,
                gclassid = gCourse['id']
            )
            otdataGCourse.save()

        # if the GCourse and the teacher is in OTData then update it
        elif otdataGCourse and otdataGClassTeacher:
            otdataGCourse.update(
                gclassdict = gCourse,
                gteacherdict = GClassTeacher,
                teacher = otdataGClassTeacher
            )

        # if the course is in OTData but the teacher is not in otdata
        elif otdataGCourse and not otdataGClassTeacher:
            otdataGCourse.update(
                gclassdict = gCourse,
                gteacherdict = GClassTeacher
            )

        # Check for an enrollment.  If not there, create one.
        try:
            userEnrollment = GEnrollment.objects.get(owner = current_user, gclassroom = otdataGCourse)
        except:
            userEnrollment = GEnrollment(
                owner = current_user,
                gclassroom = otdataGCourse)
            userEnrollment.save()

    return redirect(url_for('checkin'))

@app.route('/gclass/<gclassid>')
def gclass(gclassid):
    gClassroom = GoogleClassroom.objects.get(gclassid=gclassid)
    enrollments = GEnrollment.objects(gclassroom=gClassroom)
    gCourseWork = CourseWork.objects(gclassroom = gClassroom)
    return render_template('sbg/gclass.html', gclass=gClassroom, enrollments=enrollments, gCourseWork = gCourseWork)

@app.route('/gclass/assignments/<gclassid>')
def gClassAssignments(gclassid):
    gClassroom = GoogleClassroom.objects.get(gclassid=gclassid)
    try:
        assesDict = gClassroom.courseworkdict['courseWork']
    except:
        assesDict={}
    else:
        assesDict = sorted(assesDict, key = lambda i: (i['title']))

    return render_template('sbg/assignments.html', gClass=gClassroom, assesDict = assesDict)

@app.route('/assignment/<assid>', methods=['GET', 'POST'])
def gAss(assid):
    ass = CourseWork.objects.get(id=assid)
    standards = Standard.objects()
    standardsChoices = []
    for standard in standards:
        standardsChoices.append((standard.id,standard.name))
    form = AssignmentForm()
    form.standards.choices = standardsChoices
    if form.is_submitted():
        ass.update(
            standards = []
        )
        ass.update(
            add_to_set__standards=form.standards.data
        )
        ass.reload()
    return render_template('sbg/assignment.html',ass=ass, form=form)

@app.route('/standard/list', methods=['GET', 'POST'])
def standardlist():
    form = StandardForm()
    standards = Standard.objects()
    return render_template('sbg/standards.html',standards=standards,form=form)

@app.route('/standard/new', methods=['GET', 'POST'])
def standardNew():
    form = StandardForm()
    if form.validate_on_submit():
        standardNew = Standard(
            name = form.name.data,
            desc = form.desc.data,
            gclass = form.gclass.data
        )
        standardNew.save()
        return redirect(url_for('standardlist'))
    if session['role'].lower() == 'teacher':
        currTeacher = User.objects.get(gid = current_user.gid)
    myGClasses = GoogleClassroom.objects(teacher=currTeacher)
    gClassChoices = []
    for gClass in myGClasses:
        gClassChoices.append((gClass.id,gClass.gclassdict['name']))
    form.gclass.choices = gClassChoices
    return render_template('sbg/standardform.html', form=form)

@app.route('/standard/edit/<standardid>', methods=['GET', 'POST'])
def standardedit(standardid):
    form = StandardForm()
    standardEdit = Standard.objects.get(id = standardid)
    if form.validate_on_submit():
        standardEdit.update(
            name = form.name.data,
            desc = form.desc.data,
            gclass = ObjectId(form.gclass.data)
            )
        return redirect(url_for('standardlist'))
    if session['role'].lower() == 'teacher':
        currTeacher = User.objects.get(gid = current_user.gid)
    myGClasses = GoogleClassroom.objects(teacher=currTeacher)
    gClassChoices = []
    for gClass in myGClasses:
        gClassChoices.append((gClass.id,gClass.gclassdict['name']))
    form.gclass.choices = gClassChoices
    form.gclass.data = standardEdit.gclass
    form.name.data = standardEdit.name
    form.desc.data = standardEdit.desc
    return render_template('sbg/standardform.html',form=form)

@app.route('/standard/delete/<standardid>')
def standardDelete(standardid):
    standardDel = Standard.objects.get(id=standardid)
    standardDel.delete()
    flash('Standard is deleted.')
    return redirect(url_for('standardlist'))

@app.route('/my/asssubs/<gclassID>')
def getmyasssubs(gclassid):
    gclass = GoogleClassroom.objects.get(gclassid=gclassid)
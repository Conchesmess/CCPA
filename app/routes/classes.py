#from app.routes.coursecatalog import course
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt 
from app import app
from .users import credentials_to_dict
from flask import render_template, redirect, session, flash, url_for, Markup, render_template_string, request
from app.classes.data import User
from app.classes.gclassroom import GEnrollment, GoogleClassroom
from app.classes.forms import AddToCohortForm, GClassForm
import mongoengine.errors
import google.oauth2.credentials
import googleapiclient.discovery
from google.auth.exceptions import RefreshError
import datetime as dt
from .sbg import getCourseWork
import pandas as pd
import numpy as np
from bson.objectid import ObjectId
from flask_login import current_user
import requests
from datetime import datetime as dt

@app.route('/addtocohort', methods=['GET', 'POST'])
def addtocohort():
    form = AddToCohortForm()
    if form.validate_on_submit():
        gClass = GoogleClassroom.objects.get(gclassid=form.gclassmongoid.data)
        if form.aeriesIds.data:
            ids = form.aeriesIds.data.replace(" ", "")
            ids = form.aeriesIds.data.replace("\n", "")
            ids = form.aeriesIds.data.replace("\r", "")
            ids = ids.split(",")
            for id in ids:
                try:
                    student = User.objects.get(aeriesid=id)
                except mongoengine.errors.DoesNotExist:
                    flash(f"AeriesID: {id} does not exist in OTData.")
                else:
                    try:
                        enrollment = GEnrollment.objects.get(gclassroom=gClass,owner=student)
                    except mongoengine.errors.DoesNotExist:
                        flash(f"There is no enrollment in this class for {student.fname} {student.lname}.")
                    else:
                        enrollment.update(
                            sortCohort = form.sortCohort.data,
                            status = "Active"
                        )
        elif form.emails.data:
            emails = form.emails.data.replace(" ", "")
            emails = emails.strip(",")
            emails = emails.split(",")

            for email in emails:
                email = email.replace("\r","")
                email = email.replace("\n","")
                try:
                    student = User.objects.get(oemail=email)
                except mongoengine.errors.DoesNotExist:
                    flash(f"The email: {email} does not exist in OTData.")
                else:
                    try:
                        enrollment = GEnrollment.objects.get(gclassroom=gClass,owner=student)
                    except mongoengine.errors.DoesNotExist:
                        flash(f"There is no enrollment in this class for {student.fname} {student.lname}.")
                    else:
                        enrollment.update(
                            sortCohort = form.sortCohort.data,
                            status = "Active"
                        )
        else:
            flash(f"You must include EITHER Aeries ID's or OT Emails")
        return redirect(url_for('roster',gclassid=gClass.gclassid))

    currUser = current_user
    activeEnrollments = GEnrollment.objects(owner=currUser,status="Active")
    for enrollment in activeEnrollments:
        form.gclassmongoid.choices.append((enrollment.gclassroom.gclassdict['id'],enrollment.gclassroom.gclassdict['name']))
    return render_template('classes/addtocohortform.html', form=form)
    
@app.route('/addgclass/<gmail>/<gclassid>')
def addgclass(gmail,gclassid):

    try:
        stu = User.objects.get(oemail=gmail)
    except mongoengine.errors.DoesNotExist:
        flash("I can't find this user in OTData.")
        return redirect(url_for('roster',gclassid=gclassid))
    except Exception as error:
        flash(f"Got an unexcepted error: {error}")
        return redirect(url_for('roster',gclassid=gclassid))

    try:
        gClassroom = GoogleClassroom.objects.get(gclassid=gclassid)
    except mongoengine.errors.DoesNotExist:
        flash(f"Could not find this class in list of Google Classrooms at OTData.")
        return redirect(url_for('roster',gclassid=gclassid))
    except Exception as error:
        flash(f"Got an unexpected error: {error}")
        return redirect(url_for('roster',gclassid=gclassid))
    else:
        try:
            enrollment = GEnrollment.objects.get(gclassroom=gClassroom,owner=stu)
        except mongoengine.errors.DoesNotExist:
            newEnrollment = GEnrollment(
                owner = stu,
                gclassroom=ObjectId(gclassid)
                )
            newEnrollment.save()
        else:
            flash(f"{stu.fname} {stu.lname} already has this class stored in OTData.")
            return redirect(url_for('roster',gclassid=gclassid))

    flash(f"This class has been added to the OTData classes for {stu.fname} {stu.lname}.")
    
    return redirect(url_for('roster',gclassid=gclassid))

@app.route('/student/getstudentwork/<gclassid>')
def getstudentwork(gclassid):
    if session['role'].lower() != "student":
        flash('This link is only for students.')
        return redirect('checkin')

    # setup the Google API access credentials
    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    session['credentials'] = credentials_to_dict(credentials)

    classroom_service = googleapiclient.discovery.build('classroom', 'v1', credentials=credentials)
    studSubsAll = []
    pageToken=None
    while True:
        try:
            studSubs = classroom_service.courses().courseWork().studentSubmissions().list(
                courseId=gclassid,
                #states=['TURNED_IN','RETURNED','RECLAIMED_BY_STUDENT'],
                courseWorkId='-',
                ).execute()
        except RefreshError:
            flash('Had to reauthorize your Google credentials.')
            return redirect('/authorize')

        except Exception as error:
            flash(f"unknown error: {error}")

        studSubsAll.extend(studSubs['studentSubmissions'])
        pageToken = studSubs.get('nextPageToken')
        if not pageToken:
            break
    studSubsDict = {}
    studSubsDict['submissions'] = studSubsAll
    gclass = GoogleClassroom.objects.get(gclassid=gclassid)
    enrollment = GEnrollment.objects(owner=current_user,gclassroom=gclass)
    enrollment.update(
        mysubmissions = studSubsDict
        )

    try:
        myCourseWork = classroom_service.courses().courseWork().list(
            courseId=gclassid
            ).execute()
    except RefreshError:
        flash('When trying to retrieve your assignments I had to reauthorize your Google credentials.')
        return redirect('/authorize')
    except Exception as error:
        flash(f"unknown error while retrieving assignments: {error}")

    courseWorkDict = {}
    courseWorkDict = myCourseWork
    enrollment.update(
        myassignments = courseWorkDict
    )
    
    return redirect(url_for('mywork',gclassid=gclassid))

@app.route('/student/mywork/<gclassid>')
def mywork(gclassid):

    getstudentwork(gclassid)

    currUser = current_user
    if currUser.role.lower() != "student":
        flash("this link is only for students.")
        return redirect(url_for('checkin'))
    gclass = GoogleClassroom.objects.get(gclassid=gclassid)
    enrollment = GEnrollment.objects.get(owner=current_user,gclassroom=gclass)

    myWorkDF = pd.DataFrame(enrollment.mysubmissions['submissions'])
    courseWorkDF = pd.DataFrame(enrollment.myassignments['courseWork'])
    courseWorkDF.rename(columns={"id": "courseWorkId",'alternateLink':'Assignment Link'}, inplace=True)
    #courseWorkDF = courseWorkDF.drop(['materials','state','creationTime','updateTime','workType','submissionModificationMode','creatorUserId','courseId'],axis=1)

    #merge in all the assignments
    myWorkDF = pd.merge(courseWorkDF, 
                    myWorkDF, 
                    on ='courseWorkId', 
                    how ='inner')

    myWorkDF.rename(columns={"courseId_x": "courseId","state_y":"status"}, inplace=True)

    myWorkDF.drop(['description','alternateLink','materials','state_x','creationTime_x','creationTime_y','updateTime_x','updateTime_y','workType','submissionModificationMode','creatorUserId','topicId','dueTime','courseId_y','userId','courseWorkType','assignmentSubmission','courseId','courseWorkId','id'],axis=1,inplace=True)


    myWorkDF['Assignment Link'] = myWorkDF.apply(lambda row: f"<a href='{row['Assignment Link']}'>link</a>",axis=1)

    myWorkDF['dueDate'] = myWorkDF.apply(lambda row: dt.strptime(f"{row['dueDate']['month']}/{row['dueDate']['day']}/{row['dueDate']['year']}",'%m/%d/%Y') if pd.notna(row['dueDate']) else row['dueDate'],axis=1)
    myWorkDF['dueDate'] = myWorkDF['dueDate'].dt.strftime('%m/%d/%Y')
    myWorkDF['gradeCategory'] = myWorkDF.apply(lambda row: f"{row['gradeCategory']['name']}" if pd.notna(row['gradeCategory']) else row['gradeCategory'],axis=1)
    myWorkDF['status'] = myWorkDF.apply(lambda row: "Graded" if row['assignedGrade'] > 0 else row['status'],axis=1)
    myWorkDF['perc'] = myWorkDF.apply(lambda row: row['assignedGrade']/row['maxPoints'],axis=1)
    
    def perc(row):
        try:
            if row['late'] and pd.isna(row['assignedGrade']) and row['status'] != "TURNED_IN":
                return 0
            else:
                return row['perc']
        # No late assignments
        except KeyError:
            return row['perc'] 

    myWorkDF['perc'] = myWorkDF.apply(lambda row: perc(row) ,axis=1)

    myWorkDict = myWorkDF.fillna(0)
    myWorkDF.fillna("",inplace=True)
    myWorkDict = myWorkDict.to_dict()
    print(myWorkDict)

    def b_color(val):
        
        try:
            if val == 1:
                color = 'green'
            elif val >= 0.75:
                color = 'yellow'
            else:
                color = 'red'
        except:
            color = "white"

        return f'background-color: {color}'
    
    
    displayDFHTML = myWorkDF.style\
        .applymap(b_color, subset=['perc'])\
        .format(precision=0)\
        .set_table_styles([
            {'selector': 'tr:hover','props': 'background-color: #cccccc; font-size: 1em;'},\
            {'selector': 'thead','props': 'height:100px'},\
            {'selector': 'th','props': 'background-color: #CCCCCC !important'}], overwrite=False)\
        .set_table_attributes('class="table table-sm"')  \
        .set_sticky(axis="columns",levels=0)\
        .hide(axis='index')\
        .to_html()
    displayDFHTML = Markup(displayDFHTML)
    
    return render_template('mywork.html',displayDFHTML=displayDFHTML,myWorkDict=myWorkDict)

@app.route('/ontimeperc/<gclassid>')
def ontimeperc(gclassid):
    gClassroom = GoogleClassroom.objects.get(gclassid=gclassid)
    enrollments = GEnrollment.objects(gclassroom=gClassroom)
    if len(enrollments) < 2:
        flash("There's no students in your roster.  You need to update your roster")
        return redirect(url_for('roster',gclassid=gclassid))

    try:
        subsDF = pd.DataFrame.from_dict(gClassroom.studsubsdict['studsubs'], orient='index')
    except:
        flash(Markup(f'You need to <a href="/getstudsubs/{gclassid}">update student submissions.</a>'))
        return redirect(url_for('gclass',gclassid=gclassid))

    subsDF = subsDF.drop(columns='id')

    try: 
        subsDF['late']
    except KeyError:
        subsDF = subsDF[['userId', 'courseId', 'courseWorkId', 'creationTime', 'updateTime', 'state', 'alternateLink', 'courseWorkType', 'assignmentSubmission', 'submissionHistory']]
        subsDF['late']=""
    else:
        subsDF = subsDF[['userId', 'courseId', 'courseWorkId', 'creationTime', 'updateTime', 'state', 'alternateLink', 'courseWorkType', 'assignmentSubmission', 'submissionHistory', 'late']]


    dictfordf = {}
    for row in enrollments:
        newRow = {'userId':row['owner']['gid'],'fname':row['owner']['fname'],'lname':row['owner']['lname'],'email':row['owner']['oemail']}
        dictfordf[row['owner']['id']] = newRow

    stusDF = pd.DataFrame.from_dict(dictfordf, orient='index')
    
    gbDF = pd.merge(stusDF, 
                      subsDF, 
                      on ='userId', 
                      how ='inner')

    dictfordf = {}
    for row in gClassroom.courseworkdict['courseWork']:
        dictfordf[row['id']] = row

    courseworkDF = pd.DataFrame.from_dict(dictfordf, orient='index')
    courseworkDF.rename(columns={"id": "courseWorkId"}, inplace=True)

    gbDF = pd.merge(courseworkDF, 
                    gbDF, 
                    on ='courseWorkId', 
                    how ='inner')
    gbDF.fillna('', inplace=True)
    gbDF['late'] = gbDF['late'].astype('bool')
    gbDF = pd.pivot_table(data=gbDF,index=['email'],aggfunc={'late':np.sum,'email':len})
    gbDF['On Time %'] = 100-(gbDF['late'] / gbDF['email'] * 100)
    gbDF.rename(columns={"email": "total"}, inplace=True)
    gbDF = gbDF.sort_values(by=['On Time %'], ascending=False)
    median = round(gbDF['On Time %'].median(),2)
    mean = round(gbDF['On Time %'].mean(), 2)

    stuList = gbDF.reset_index(level=0)
    stuList = stuList.values.tolist()


    #plotting boxplot 
    #plt.boxplot([x for x in gbDF['On Time %']],labels=[x for x in gbDF.index], showmeans=True) 
    plt.boxplot([x for x in gbDF['On Time %']], showmeans=True) 

    #x and y-axis labels 
    plt.xlabel('name') 
    plt.ylabel('%') 

    #plot title 
    plt.title('Analysing on time %') 

    #save and display 
    plt.savefig(f'app/static/{gclassid}.png',dpi=300,bbox_inches='tight')
    plt.clf()
  
    displayDFHTML = Markup(pd.DataFrame.to_html(gbDF))

    ### Assignment list with their state: Turned-in, Graded, etc
    assesDF = pd.DataFrame.from_dict(gClassroom.courseworkdict['courseWork'])    
    assesDF = assesDF.rename(columns={'id':'courseWorkId'})
    try:
        assesDF['dueDate']
    except:
        flash("All Assignments must have Due Dates.")
        return redirect(url_for('index'))
    else:
        assesDDDF = assesDF[['courseWorkId','dueDate']].copy()
    assesDDDF = assesDDDF.fillna('-')
    assesDF['alternateLink'] = assesDF.apply(lambda row: row['alternateLink'].replace('details','submissions/by-status/and-sort-name/all'),axis=1)
    assesDF['title'] = assesDF.apply(lambda row: row['title']+'<a href="'+row['alternateLink']+'" target="_blank" rel="noopener noreferrer">'+' (g)'+'</a>',axis=1)
    assesDF = assesDF[['courseWorkId','title']].copy()


    subsDF = pd.DataFrame.from_dict(gClassroom.studsubsdict['studsubs'], orient='index')
    subsDF['state'] = subsDF.apply(lambda row: 'UNATTEMPTED' if row['state'] in ["NEW","CREATED"] else row['state'], axis=1)
    assesDDDF = assesDDDF[['courseWorkId','dueDate']]

    subsDF = pd.merge(subsDF, 
                   assesDDDF, 
                   on ='courseWorkId', 
                   how ='left')

    def checkDueDate(cell):
        if cell == "-":
            return "NOT DUE"
        else:
            dateString = f"{cell['month']}/{cell['day']}/{cell['year']}"
            dateObj = dt.strptime(dateString, '%m/%d/%Y')
            if dt.today() < dateObj:
                return "NOT DUE"

    subsDF['state'] = subsDF.apply(lambda row: "NOT DUE" if checkDueDate(row['dueDate']) == "NOT DUE" else row['state'], axis=1)
    subsDF['state'] = subsDF.apply(lambda row: 'GRADED' if row['assignedGrade'] > 0 else row['state'], axis=1)


    subsDF.reset_index(inplace=True)
    subsDF = pd.pivot_table(data=subsDF,index='courseWorkId',columns="state",values='id',aggfunc='count')
    subsDF = subsDF.fillna("-")

    subsDF = pd.merge(subsDF, 
                   assesDF, 
                   on ='courseWorkId', 
                   how ='left')
    
    subsDF['courseWorkId'] = subsDF['title']

    subsDF.drop('title',axis=1,inplace=True)
    subsDF = subsDF.rename(columns={'courseWorkId':'Title'})
    subsDF = subsDF.sort_values(by=['Title'])
    subsDFHTML = subsDF.style\
        .format(precision=0)\
        .set_table_styles([
            {'selector': 'tr:hover','props': 'background-color: #cccccc; font-size: 1em;'},\
            {'selector': 'thead','props': 'height:100px'},\
            {'selector': 'th','props': 'background-color: #CCCCCC !important'}], overwrite=False)\
        .set_table_attributes('class="table table-sm"')  \
        .set_sticky(axis="columns",levels=0)\
        .hide(axis='index')\
        .to_html()
        # the command below makes the header transparent
        # .set_uuid('trans')\

    subsDFHTML = Markup(subsDFHTML)

    ### assignments with number of times turned in

    ### These lines are refernce, there were run above.
    # assesDF = pd.DataFrame.from_dict(gClassroom.courseworkdict['courseWork'])    
    # assesDF = assesDF.rename(columns={'id':'courseWorkId'})
    # assesDDDF = assesDF[['courseWorkId','dueDate']].copy()
    # assesDDDF = assesDDDF.fillna('-')
    # assesDF['title'] = assesDF.apply(lambda row: row['title']+'<a href="'+row['alternateLink']+'" target="_blank" rel="noopener noreferrer">'+' (g)'+'</a>',axis=1)
    # assesDF = assesDF[['courseWorkId','title']].copy() 

    subsDF = pd.DataFrame.from_dict(gClassroom.studsubsdict['studsubs'], orient='index')
    subsDF = subsDF[['courseWorkId','submissionHistory','userId','id']].copy()

    subsDF = pd.merge(subsDF, 
                   assesDF, 
                   on ='courseWorkId', 
                   how ='left')

    def countIters(row):
        c = 0
        try:
            for item in row:
                try:
                    if item['gradeHistory']['gradeChangeType'] == "ASSIGNED_GRADE_POINTS_EARNED_CHANGE":
                        c = c+1
                except:
                    pass
        except:
            pass

        return c
    # TODO this should count grade history NOT submission history
    subsDF['iterations'] = subsDF['submissionHistory'].apply(lambda row: countIters(row))
    subsDF = subsDF.drop(['submissionHistory'], axis=1)
    subsDF = pd.pivot_table(data=subsDF,index='title',columns="iterations",values='id',aggfunc='count')
    subsDF = subsDF.reset_index()
    subsDF = subsDF.fillna("-")

    subItersDFHTML = subsDF.style\
        .format(precision=0)\
        .set_table_styles([
            {'selector': 'tr:hover','props': 'background-color: #CCCCCC; font-size: 1em;'},\
            {'selector': 'thead','props': 'height:100px'},\
            {'selector': 'th','props': 'background-color: #CCCCCC !important'}], overwrite=False)\
        .set_table_attributes('class="table table-sm"')  \
        .set_sticky(axis="columns",levels=0)\
        .hide(axis='index')\
        .to_html()
    subItersDFHTML = Markup(subItersDFHTML)

    ### Sub State by student

    if current_user.role.lower() == "teacher":

        subsStuDF = pd.DataFrame.from_dict(gClassroom.studsubsdict['studsubs'], orient='index')
        def makeStuURL(url):
            url = url.replace('/a/', '/sp/')
            url = url.replace('/submissions/by-status/and-sort-last-name/student/','/zzz/')
            endBeg = url.find('/sp/')+3
            begEnd = url.find('/zzz/')+4
            url = "<a target='_blank' href='" + url[:endBeg] + url[begEnd:] + "/all'" +">link</a>"
            return url

        subsStuDF['url'] = subsStuDF.apply(lambda row: makeStuURL(row['alternateLink']),axis=1)
        subLinkDF = subsStuDF[['userId','url']].copy()

        subLinkDF = subLinkDF.drop_duplicates(subset='url')

        subsStuDF = pd.merge(subsStuDF, 
                    assesDDDF, 
                    on ='courseWorkId', 
                    how ='left')

        subsStuDF['state'] = subsStuDF.apply(lambda row: 'UNATTEMPTED' if row['state'] in ["NEW","CREATED"] else row['state'], axis=1)

        subsStuDF['state'] = subsStuDF.apply(lambda row: "NOT DUE" if checkDueDate(row['dueDate']) == "NOT DUE" else row['state'], axis=1)
        subsStuDF['state'] = subsStuDF.apply(lambda row: 'GRADED' if row['assignedGrade'] > 0 else row['state'], axis=1)
        subsStuDF.reset_index(inplace=True)

        subsStuDF = pd.pivot_table(data=subsStuDF,index='userId',columns="state",values='id',aggfunc='count')

        subsStuDF = pd.merge(subsStuDF, 
                subLinkDF, 
                on ='userId', 
                how ='left')

        rosterDF = pd.DataFrame.from_dict(gClassroom.grosterTemp, orient="columns")
        def nameFromDict(row):
            try:
                fullName = row['name']['fullName']
                lenName = len(fullName)
                stop = lenName - 10
                return fullName[:stop+1]
            except:
                pass
        rosterDF['name'] = rosterDF['profile'].apply(lambda row: nameFromDict(row))
        rosterDF = rosterDF.drop(['profile','courseId'], axis=1)
        subsStuDF = pd.merge(subsStuDF, 
                    rosterDF, 
                    on ='userId', 
                    how ='left')
        subsStuDF['userId'] = subsStuDF['name']
        subsStuDF.drop(['name'],axis=1,inplace=True)
        url = subsStuDF.pop("url")
        subsStuDF.insert(1, url.name, url)   
        subsStuDF=subsStuDF.sort_values(by=['GRADED','userId'],ascending=True, na_position = 'first')
        subsStuDF.fillna("-", inplace=True)

        subsStuDFHTML = subsStuDF.style\
            .format(precision=0)\
            .set_table_styles([
                {'selector': 'tr:hover','props': 'background-color: #CCCCCC; font-size: 1em;'},\
                {'selector': 'thead','props': 'height:100px'},\
                {'selector': 'th','props': 'background-color: #CCCCCC !important'}], overwrite=False)\
            .set_table_attributes('class="table table-sm"')  \
            .set_sticky(axis="columns",levels=0)\
            .hide(axis='index')\
            .to_html()
        subsStuDFHTML = Markup(subsStuDFHTML)
    if current_user.role.lower()=="teacher":
        return render_template('studsubs.html',gClassroom=gClassroom,subsStuDFHTML=subsStuDFHTML,subItersDFHTML=subItersDFHTML,displayDFHTML=displayDFHTML,median=median,mean=mean,subsDFHTML=subsDFHTML)
    else:
        return render_template('studsubs.html',gClassroom=gClassroom,subItersDFHTML=subItersDFHTML,median=median,mean=mean,subsDFHTML=subsDFHTML)

def getStudSubs(gclassid,courseWorkId="-"):
    gClassroom = GoogleClassroom.objects.get(gclassid=gclassid)
    # setup the Google API access credentials
    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        flash('Had to reauthorize your Google credentials.')
        return "refresh"
    session['credentials'] = credentials_to_dict(credentials)
    # Rubric instructions with dev preview
    # https://developers.google.com/classroom/rubrics/getting-started
    classroom_service = googleapiclient.discovery.build(
            'classroom', 
            'v1', 
            credentials=credentials,
            discoveryServiceUrl='https://classroom.googleapis.com/$discovery/rest?labels=DEVELOPER_PREVIEW&key=AIzaSyDz4K5HXeFqHzAFjhDNaXoogrSxo6x7ZHY'
        )
    studSubsAll = []
    pageToken=None
    counter=1
    while True:
        try:
            studSubs = classroom_service.courses().courseWork().studentSubmissions().list(
                courseId=gclassid,
                #states=['TURNED_IN','RETURNED','RECLAIMED_BY_STUDENT'],
                courseWorkId=courseWorkId,
                pageToken=pageToken,
                previewVersion="V1_20231110_PREVIEW"
                ).execute()
        except RefreshError:
            flash('Had to reauthorize your Google credentials.')
            return "refresh"

        except Exception as error:
            flash(f'Unknown error: {error}')
            return "Refresh"

        studSubsAll.extend(studSubs['studentSubmissions'])
        pageToken = studSubs.get('nextPageToken')
        counter=counter+1
        if not pageToken:
            break
    # how many StudSubs were retreived from Google
    subsLength = len(studSubsAll)

    dictfordf = {}
    for row in studSubsAll:
        dictfordf[row['id']] = row

    studSubsAll = {'lastUpdate':dt.utcnow(),'studsubs':dictfordf}
    gClassroom.update(
        studsubsdict = studSubsAll
    )

    return studSubsAll

@app.route('/getstudsubs/<gclassid>/<courseWorkId>')
@app.route('/getstudsubs/<gclassid>')
def getstudsubs(gclassid,courseWorkId="-"):
    url = request.environ['QUERY_STRING']
    courseWork = getCourseWork(gclassid)
    if courseWork == "refresh":
        return redirect(url_for('authorize'))
    elif courseWork == False:
        return redirect(url_for('checkin'))
    studSubsAll = getStudSubs(gclassid,courseWorkId)
    if studSubsAll == "refresh":
        return redirect(url_for('authorize'))

    return redirect(url)


## Replicated in sbg.py as gclasslist
# this function exists to update the stored values for one or more google classrooms
@app.route('/gclasses')
def gclasses(gclassid=None):

    # Get the currently logged in user because, this will only work for the Current User as I don't have privleges to retrieve classes for other people.
    currUser = current_user
    # setup the Google API access credentials
    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')
    session['credentials'] = credentials_to_dict(credentials)
    classroom_service = googleapiclient.discovery.build('classroom', 'v1', credentials=credentials)

    # Get all of the google classes
    try:
        gCourses = classroom_service.courses().list(courseStates='ACTIVE').execute()
    except RefreshError:
        flash("When I asked for the courses from Google Classroom I found that your credentials needed to be refreshed.")
        return redirect('/authorize')
    else:
        gCourse = None
        gCourses = gCourses['courses']

    # Iterate through the classes
    for gCourse in enumerate(gCourses):
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
            ).save()

        # If there is NOT a teacher in OTData and NOT a course in OTData
        elif not otdataGCourse and not otdataGClassTeacher:
            otdataGCourse = GoogleClassroom(
                gclassdict = gCourse,
                gteacherdict = GClassTeacher,
                gclassid = gCourse['id']
            ).save()

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

        # check to see if the class exists in the current user's embedded doc
        try:
            userGClass = currUser.gclasses.get(gclassid=gCourse['id'])
        except:
            userGClass = None

        # if the class does not exist then add it to the embedded doc 
        if not userGClass:
            newUserGClass = currUser.gclasses.create(
                gclassid = gCourse['id'],
                gclassroom = otdataGCourse,
                classname = otdataGCourse.gclassdict['name'],
                status = 'Inactive'
            )
            userGClass = newUserGClass

    currUser.save()

    return redirect(url_for('checkin'))

@app.route('/editgclass/<gclassid>', methods=['GET', 'POST'])
def editgclass(gclassid):
    currUser = current_user
    gclassroom = GoogleClassroom.objects.get(gclassid=gclassid)
    enrollment = GEnrollment.objects.get(owner=currUser,gclassroom=gclassroom)
    
    form = GClassForm()

    if form.validate_on_submit():
        enrollment.update(
            classnameByUser = form.classname.data, 
            status = form.status.data
        )

        return redirect(url_for('checkin'))

    if enrollment.classnameByUser:
        form.classname.data = enrollment.classnameByUser
    else:
        form.classname.data = enrollment.gclassroom.gclassdict['name']
    
    if enrollment.status:
        form.status.data = enrollment.status

    return render_template('editgclass.html', form = form, editGClass = enrollment)

@app.route('/deletegclass/<gclassid>', methods=['GET', 'POST'])
def deletegclass(gclassid):
    
    if session['role'].lower() == "student":
        flash("Students can't delete enrollments.")
    else:
        currUser = current_user
        gclassroom = GoogleClassroom.objects.get(gclassid=gclassid)
        enrollment = GEnrollment.objects.get(owner=currUser,gclassroom=gclassroom)
        enrollment.delete()
        flash("deleted")
    
    return redirect(url_for('checkin'))

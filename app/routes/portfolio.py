from __future__ import print_function

from app import app
from flask import render_template, redirect, url_for, session, flash
from app.classes.data import Portfolio, User, GFilesToDelete, CreatePortfolioFolderReq
from app.classes.forms import PortfolioSubmissionForm1, PortfolioSubmissionForm2, PortfolioSubmissionFileForm, GFileSeachForm
import datetime as dt
from bson import ObjectId
from flask_login import current_user
from mongoengine.errors import NotUniqueError, DoesNotExist
from mongoengine import Q
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload
import ast
import datetime as dt
from readability import Readability
import nltk
import os

# Google File Attributes: 
# kind, copyRequiresWriterPermission, writersCanShare, viewedByMe, mimeType, exportLinks, parents, thumbnailLink, iconLink, 
# shared, lastModifyingUser, owners, webViewLink, size, viewersCanCopyContent, permissions, hasThumbnail, spaces, id, name, 
# starred, trashed, explicitlyTrashed, createdTime, modifiedTime, modifiedByMeTime, viewedByMeTime, quotaBytesUsed, version, 
# ownedByMe, isAppAuthorized, capabilities, thumbnailVersion, modifiedByMe, permissionIds, linkShareMetadata

#shared drive
driveId = '0ABi_BR4s9fIsUk9PVA'
#student folder in shared drive
folderId = '1ot03EN_B9g86lhKjBZHKBvFWfP260vfh'

# Students can't create their own folder in the shared file so request is created that is run when 
# some one with appropriate privledges logs in
def createStudentFoldersFromReq():
    folderReqs = CreatePortfolioFolderReq.objects()
    for folderReq in folderReqs:
        response = create_student_folders([folderReq.oemail])
        folderReq.delete()

    return


# students can't delete documents from the drive so this creates a request which 
# will automatically delete the document when some one with appropriate provledges logs in
def deletegfiles():

    deletes = GFilesToDelete.objects()

    if len(deletes) == 0:
        return None

    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    service = build('drive', 'v3', credentials=credentials)
    body_value = {'trashed': True}
    responses=[]
    for delete in deletes:
        try:
            response = service.files().update(
                            fileId=delete.fileid, 
                            body=body_value,
                            supportsAllDrives = True
                            ).execute()
        except Exception as error:
            flash(f"An error happen when trying to delete a file in the portfolios. {error}")
        else:
            responses.append(response)
        deleteRecord = GFilesToDelete.objects.get(pk=delete.id)
        deleteRecord.delete()
    return responses


def get_folder_list(oemail=None):
    # check to see if the student already has a folder
    # it is possible that a folder could be created from the drive app
    if oemail:
        query = f"name contains '{oemail}' and '{folderId}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    else:
        query = f"'{folderId}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"

    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    service = build('drive', 'v3', credentials=credentials)

    # GET A LIST OF ALL FILE IDS IN FOLDER
    folders = []
    page_token = None

    while True:
        # pylint: disable=maybe-no-member
        # Query infor: https://developers.google.com/drive/api/guides/search-files
        # * below ask for google to return ALL fields for each file
        # see list of fileds at top of this file

        response = service.files().list(q=query,
                                        corpora='drive',
                                        driveId=driveId,
                                        fields='nextPageToken,files(name)',
                                        includeItemsFromAllDrives = True,
                                        supportsAllDrives = True,
                                        pageToken=page_token).execute()

        folders.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    return folders

# add list of user emails to shared drive
def addTeachersToSharedDrive():

    return render_template("index.html")

    users = ['dom.brassey@ousd.org','sarah.carter@ousd.org','carina.ibarra@ousd.org','sarah.carter@ousd.org','no.e.parker@ousd.org','maria.robles1@ousd.org','tyjun.mack@ousd.org']
    driveRole = 'writer'

    """
    Batch permission modification.
    Args:
        driveId: Id of the shared drive
        users: list of email addresses
        https://developers.google.com/drive/api/guides/ref-roles
        permission roles: owner, organizer, fileOrganizer, writer, commenter, reader
            teachers are organizers and students are writers of their folders and readers of the shared drive
    """
    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    service = build('drive', 'v3', credentials=credentials)
    
    # Add permissions to the Shared Drive
    ids = []

    def callback(request_id, response, exception):
      if exception:
        # Handle error
        flash(exception)
      else:
        # print(f"Request_Id: {request_id}")
        # print(f'Permission Id: {response.get("id")}')
        ids.append(response.get("id"))

    batch = service.new_batch_http_request(callback=callback)

    for userEmail in users:

        # pylint: disable=maybe-no-member
        user_permission = {
            "type": "user",
            "role": driveRole,
            "emailAddress": userEmail,
        }
        batch.add(
            service.permissions().create(
                fileId=driveId,
                body=user_permission,
                supportsAllDrives=True,
                fields="id",
            )
        )

    try:
        batch.execute()

    except HttpError as error:
        print(f"While trying to add you to the shared drive an error occurred: {error}")
        ids = None

    flash(f"number of shares requested: {len(users)}")
    flash(f"Number of shares returned: {len(ids)}")
    
    return render_template('index.html')


# Helper function to create one or more student folder's in the shared drive
def create_student_folders(oemails):
    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    service = build('drive', 'v3', credentials=credentials)

    folders = get_folder_list()

    #TODO check that they are shared to the shared drive

    for oemail in oemails:

        if {'name':oemail} in folders:
            flash(f"A folder already exists for {oemail}.")
            response = None

        else:

            # create the student folder in the folder in the shared drive
            file_metadata = {
                'name': oemail,
                'mimeType': 'application/vnd.google-apps.folder',
                'driveId': driveId,
                'parents': [folderId]
            }

            # pylint: disable=maybe-no-member
            file = service.files().create(body=file_metadata, fields='*',supportsAllDrives=True).execute()

            # add the privledges for the student to be able to add content to their folder
            # pylint: disable=maybe-no-member
            user_permission = {
                "type": "user",
                "role": 'writer',
                "emailAddress": oemail
            }
            response = service.permissions().create(
                    fileId=file['id'],
                    body=user_permission,
                    supportsAllDrives=True
                ).execute()

    return response


@app.route('/allfolders')
def allfolders():
    folders = get_folder_list()
    flash(folders)
    return render_template('index.html')


@app.route('/createstudentfolder/<oemail>')
def create_one_student_folder(oemail):
    folders = create_student_folders([oemail])
    flash(f'request returned: {folders}')
    return render_template('index.html')
    

@app.route('/portfolio/new')
def portfolio_new():

    if current_user.role.lower() == 'student':
        student = current_user
        oemail = current_user.oemail
    else:
        flash("you can't make a new portfolio if you are not a student.")
        return render_template("index.html")

    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    service = build('drive', 'v3', credentials=credentials)

    folders = service.files().list(q=f"name = '{oemail}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                                    spaces='drive',
                                    fields='*',
                                    includeItemsFromAllDrives = True,
                                    supportsAllDrives = True).execute()
    try:
        folderDict = folders['files'][0]
    except IndexError:
        flash(f"You don't have a folder in the shared drive yet.  Ask your teacher to create one from your profile page.")
        CreatePortfolioFolderReq(oemail=current_user.oemail).save()
        return render_template('index.html')

    # create the portfolio object on Mongo
    try:
        newPortfolio = Portfolio(
                                student = student,
                                folderDict = folderDict
                                ).save()
    except NotUniqueError:
        portfolio = Portfolio.objects.get(student=student)
        return redirect(url_for('portfolio',pid=portfolio.id))
    except Exception as error:
        flash(f"something wierd happen when trying to create the new mongoDB object: {error}")
        return render_template('index.html')

    return redirect(url_for('portfolio'))


@app.route('/portfolio')
@app.route('/portfolio/<pid>')
def portfolio(pid=None):

    if current_user.role.lower() == 'student':
        student = current_user
        try:
            portfolio=Portfolio.objects.get(student=current_user)
        except DoesNotExist:
            flash("You don't have a portfolio. Making an empty one now.")
            return redirect(url_for('portfolio_new'))
    else:
        try:
            portfolio = Portfolio.objects.get(pk=pid)
        except Exception as error:
            flash(f'That portfolio is not in the database. {error}')
            return render_template('index.html')

    return render_template('portfolios/portfolio.html',portfolio=portfolio)


# TODO remove docs on submission or deny delete
@app.route('/portfolio/deletesubmission/<pid>/<soid>')
def portfolio_deletesubmission(pid,soid):
    portfolio=Portfolio.objects.get(pk=pid)
    submission = portfolio.submissions.get(oid=soid)
    print(submission)
    if submission.gfiledict:
        flash("you can't delete this submission without deleting the file first.")
        return redirect(url_for('portfolio',pid=pid))
    portfolio.submissions.filter(oid=soid).delete()
    portfolio.submissions.filter(oid=soid).save()
    portfolio.save()
    return redirect(url_for('portfolio',pid=pid))


@app.route('/portfolio/newsubmission/<pid>', methods=['GET', 'POST'])
def portfolio_newsubmision(pid):

    try:
        portfolio = Portfolio.objects.get(pk=pid)
    except DoesNotExist:
        # this should never happen because the pid comes from the portfolio page
        flash(f"Hmmm, that portfolio doesn't exist.")
        return redirect(url_for('portfolio'))

    if portfolio.student != current_user:
        flash("Only the student can create submissions in their portfolio.")
        return redirect(url_for('portfolio'))

    form = PortfolioSubmissionForm1()
    teachers = User.objects(role__iexact='Teacher').order_by('lname','fname')
    tchoices = [(None,'-----')]
    for teacher in teachers:
        tchoices.append((teacher.id,f"{teacher.lname}, {teacher.fname}"))
    form.teacher.choices = tchoices
    this_year = dt.date.today().year
    this_month = dt.date.today().month
    if this_month > 6:
        this_year += 1

    form.year.data = this_year

    if form.validate_on_submit():
        if form.origin.data == "Class":
            newSub = portfolio.submissions.create(
                oid = ObjectId(),
                origin = form.origin.data,
                subject = form.subject.data,
                grade = form.grade.data,
                writing = form.writing.data,
                per = form.per.data,
                teacher=form.teacher.data,
                year=form.year.data,
                term=form.term.data)
        else:
            newSub = portfolio.submissions.create(
                oid = ObjectId(),
                origin = form.origin.data,
                subject = form.subject.data,
                grade = form.grade.data,
                writing = form.writing.data,
                year=form.year.data,
                term=form.term.data)

        portfolio.save()
    
        return redirect(url_for('portfoliosubmissionfile',pid=pid, submissionId=newSub.oid))

    return render_template('portfolios/portfoliosubmissionform1.html',form=form,portfolio=portfolio)


# TODO the student can't delete the actual files so there needs to be something saved
# that will automatically delete the files the next time an "owner" logs in.
@app.route('/portfolio/submissionfiledelete/<pid>/<soid>')
def submissionfiledelete(pid,soid):
    portfolio = Portfolio.objects.get(pk=pid)
    submission = portfolio.submissions.get(oid=soid)
    fileId = submission.gfiledict['id']
    submission.gfiledict = None
    portfolio.save()

    GFilesToDelete(
        fileid = fileId
    ).save()
    
    return redirect(url_for('portfolio',pid=pid))


@app.route('/portfolio/submissionfile/<pid>/<submissionId>', methods=['GET', 'POST'])
def portfoliosubmissionfile(pid,submissionId):
    portfolio = Portfolio.objects.get(pk=pid)
    submission = portfolio.submissions.get(oid=submissionId)
    fileForm = PortfolioSubmissionFileForm()
    fileSearchForm = GFileSeachForm()

    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    service = build('drive', 'v3', credentials=credentials)

    files = []
    page_token = None
    createdSearch = (dt.datetime.utcnow() - dt.timedelta(days=30))
    createdSearch = createdSearch.strftime('%Y-%m-%dT%H:%M:%S')
    nameContains = ""

    if fileSearchForm.fileSearchSubmit.data and fileSearchForm.validate_on_submit():
        if fileSearchForm.allTime.data and fileSearchForm.nameContains.data:
            createdSearch = (dt.datetime.utcnow() - dt.timedelta(days=365*6))
        else:
            flash("Just searching last 30 days. Add a file name to search all time.")
            createdSearch = (dt.datetime.utcnow() - dt.timedelta(days=60))
        createdSearch = createdSearch.strftime('%Y-%m-%dT%H:%M:%S')
        if fileSearchForm.nameContains.data:
            nameContains = fileSearchForm.nameContains.data


    while True:
        # pylint: disable=maybe-no-member
        # Query infor: https://developers.google.com/drive/api/guides/search-files
        # * below ask for google to return ALL fields for each file
        # see list of fileds at top of this file

        response = service.files().list(q=fr"name contains '{nameContains}' and '{current_user.oemail}' in owners and viewedByMeTime > '2012-06-04T12:00:00' and createdTime > '{createdSearch}' and not mimeType contains 'folder'",
                                        spaces='drive',
                                        fields='nextPageToken,*',
                                        pageToken=page_token).execute()

        files.extend(response.get('files', []))
        page_token = response.get('nextPageToken', None)
        if page_token is None:
            break

    for file in files:
        file['createdTime'] = dt.datetime.strptime(file['createdTime'],'%Y-%m-%dT%H:%M:%S.%fZ')
        try:
            file['modifiedByMeTime']
        except:
            pass
        else:
            file['modifiedByMeTime'] = dt.datetime.strptime(file['modifiedByMeTime'],'%Y-%m-%dT%H:%M:%S.%fZ')


    if fileForm.fileSubmit.data and fileForm.validate_on_submit():

        fileId = fileForm.gfileids.data

        try:
            file = service.files().get(fileId=fileId,fields='id,name,owners').execute()
            # Create a new name for the file that includes the users name
            if (portfolio.student.oemail == file['owners'][0]['emailAddress'] and current_user.oemail == portfolio.student.oemail)  or (current_user.role.lower() == "teacher" and portfolio.student.oemail == file['owners'][0]['emailAddress']):
                newFileName = f"{file['name']} ({file['owners'][0]['emailAddress']})"
            elif current_user.role.lower() == "teacher" and portfolio.student.oemail != file['owners'][0]['emailAddress']:
                newFileName = f"{file['name']} ({file['owners'][0]['emailAddress']}"
                flash(f"Warning: The the file {file['name']} is not owned by the portfolio owner {portfolio.student.fname} {portfolio.student.lname}")
            else:
                flash(f"The file {file['name']} is not owned by the portfolio owner: {current_user.oemail}.")
                file = None
            file_metadata = {
                'name':newFileName,
                'driveId': '0ABi_BR4s9fIsUk9PVA',
                'parents': [portfolio.folderDict['id']]
                }

            #Copy the file
            if file:
                try:
                    cloneDict = service.files().copy(
                        fileId=fileId,
                        body=file_metadata,
                        fields='*',
                        supportsAllDrives=True).execute()
                    flash("file copied")
                
                except HttpError as error:
                    flash(F'An error occurred: {error}')
                    file = None

                else:
                    flash("file has been copied")
                    print(cloneDict['id'])
                    readabilityDict = portfolioreadability(cloneDict['id'])  
                    portfolio.submissions.filter(oid=submissionId).update(
                        gfiledict = cloneDict,
                        readabilitydict = readabilityDict
                        )
                    portfolio.save()

        
        except Exception as error:
            flash(error)
            

        return redirect(url_for('portfoliosubmission_p2',pid=pid, soid=submission.oid))

    return render_template('portfolios/portfoliosubmissionfileform.html',fileForm=fileForm,fileSearchForm=fileSearchForm,portfolio=portfolio,submission=submission,files=files)

@app.route('/portfolio/submission_p2/<pid>/<soid>', methods=['GET', 'POST'])
def portfoliosubmission_p2(pid,soid):
    portfolio = Portfolio.objects.get(pk=pid)
    submission = portfolio.submissions.get(oid=soid)

    form = PortfolioSubmissionForm2()

    if form.validate_on_submit():
        portfolio.submissions.filter(oid=soid).update(
            rating = form.rating.data,
            reflection = form.reflection.data
        )
    
        portfolio.save()

        return redirect(url_for('portfolio',pid=pid))

    return render_template('portfolios/portfoliosubmissionform2.html',portfolio=portfolio,submission=submission,form=form)



@app.route('/portfolios')
def portfolios():
    portfolios = Portfolio.objects()
    return render_template('portfolios/portfolios.html',portfolios=portfolios)


@app.route('/portfolio/readability/<gfileid>')
def portfolioreadability(gfileid):
    if google.oauth2.credentials.Credentials(**session['credentials']).valid:
        credentials = google.oauth2.credentials.Credentials(**session['credentials'])
    else:
        return redirect('/authorize')

    nltk.data.path.append('/nltk_data')
    root = os.path.dirname(os.path.abspath(__file__))
    download_dir = os.path.join(root, 'nltk_data')
    # os.chdir(download_dir)
    nltk.data.path.append(download_dir)

    #try:
    service = build("docs", "v1", credentials=credentials)

    # Retrieve the documents contents from the Docs service.
    document = service.documents().get(documentId=gfileid).execute()

    gcontent = document['body']['content']
    content=''
    for item in gcontent:
        try:
            for element in item['paragraph']['elements']:
                content += element['textRun']['content']
        except Exception as error:
            #flash(f"error: {error}")
            pass

    #flash(content)

    # Readability reference: https://github.com/cdimascio/py-readability-metrics
    r = Readability(content)
    stats = r.statistics()
    if stats['num_words'] > 99:
        gf = r.gunning_fog()
        fk = r.flesch_kincaid()
        f = r.flesch()
        dc = r.dale_chall()
        readabilityDict={
            'statastics':stats,
            'GunningFog':{'score':gf.score,'gl':gf.grade_level},
            'FleschKincaid':{'score':fk.score,'fk':fk.grade_level},
            'Flesch':{'score':f.score,'gl':f.grade_levels},
            'DaleChall':{'score':dc.score,'gl':dc.grade_levels}
            }
    else:
        flash("writing sample must have at least 100 words to be analyzed for complexity.")
        readabilityDict = {'statistics':stats}
    #return render_template('index.html')
    return readabilityDict
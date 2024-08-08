from app import app
from flask import render_template, redirect, url_for, session, flash, Markup
from app.classes.data import Transcript, User
from app.classes.forms import TranscriptForm
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
import mongoengine.errors
from flask_login import current_user
import time
from mongoengine.errors import DoesNotExist


@app.route('/transcript/list')
def transcripts():
    trans = Transcript.objects()
    return render_template('transcripts/transcripts.html',trans=trans)


@app.route('/transcript/delete/<tid>')
def transcriptDelete(tid):
    tObj = Transcript.objects.get(id=tid)
    currUser = current_user
    if tObj.student == currUser or current_user.role.lower() == "teacher":
        tObj.delete()
        flash("Transcript is deleted.")
    return redirect(url_for('transcripts'))

@app.route('/transcript/fancy/<aid>')
def transcriptfancy(aid):
    try:
        student=User.objects.get(aeriesid=aid)
    except mongoengine.errors.DoesNotExist:
        flash(f"No student with Aeries ID: {aid}")
        return redirect(url_for('transcriptNew'))
    try:
        tObj = Transcript.objects.get(student=student)
    except:
        flash(f"{student.fname} {student.lname} does not yet have a transcript on OTData.")
        return redirect(url_for('transcriptNew'))

    transcriptDF = pd.DataFrame.from_dict(tObj.transcriptDF).fillna('-')

    transcriptDF = transcriptDF.drop(['crsid','wgp','wcredit','credit','totalgp', 'totalwgp'],axis=1)

    transcriptGB = transcriptDF.groupby(['year','term','sname','grade'])

    dfs = []
    isFirst = True
    for head,df in transcriptGB:
        df = df.drop(['sname','term','year','snum','grade'],axis=1)
        if isFirst:
            df = df.drop(['mark','course','altCourse','N/P/H/AP'],axis=1)
            df = df.reset_index()
            head = (f"Transcript for {student.fname} {student.lname}","")

        df = df.style\
        .format(precision=2)\
        .set_table_styles([
            {'selector': 'tr:hover','props': 'background-color: #CCCCCC; font-size: 1em;'},\
            {'selector': 'thead','props': 'height:0px'},\
            {'selector': 'th','props': 'background-color: white !important'}], overwrite=False)\
        .set_table_attributes('class="table"')  \
        .set_uuid('trans')\
        .hide(axis='index')\
        .to_html()

        df = Markup(df)

        dfs.append((head,df))
        isFirst=False

    return render_template('transcripts/transcriptfancy.html', cols=list(transcriptDF.columns), tObj=tObj,student=student, dfs=dfs)

@app.route('/my/transcript')
@app.route('/transcript/<aid>')
def transcript(aid=None):

    if not aid:
        if current_user.aeriesid:
            aid = current_user.aeriesid
        else:
            flash("You don't have a transcript in the system.  You can make one!")
            return redirect(url_for('transcriptNew'))

    try:
        student=User.objects.get(aeriesid=aid)
    except mongoengine.errors.DoesNotExist:
        flash(f"No student with Aeries ID: {aid}")
        return redirect(url_for('transcriptNew'))
    try:
        tObj = Transcript.objects.get(student=student)
    except:
        flash(f"{student.fname} {student.lname} does not yet have a transcript on OTData.")
        return redirect(url_for('transcriptNew'))

    transcriptDF = pd.DataFrame.from_dict(tObj.transcriptDF).fillna('-')

    creditbydeptDF = pd.DataFrame.from_dict(tObj.creditbydept)

    def highlight_cols(s):
        color = 'grey'
        return 'background-color: %s' % color

    creditbydeptHTML = creditbydeptDF.style\
        .set_uuid('creditbydept')\
        .set_table_attributes('class="table"')  \
        .applymap(highlight_cols, subset=pd.IndexSlice[:, ['Sum']])\
        .apply(lambda row: ['background: grey' if row.name == 'Sum' else '' for cell in row], axis=1)\
        .format(precision=0)\
        .set_table_styles([
            {'selector': 'tr:hover','props': 'background-color: #CCCCCC; font-size: 1em;'},\
            {'selector': 'thead','props': 'height:0px'},\
            {'selector': 'th','props': 'background-color: white !important'}], overwrite=False)\
        .set_table_attributes('class="table"')  \
        .to_html()

    transcriptDFHTML = transcriptDF.style\
        .set_uuid('transcript')\
        .set_table_attributes('class="table table-sm"')  \
        .format(precision=2)\
        .set_table_styles([
            {'selector': 'tr:hover','props': 'background-color: #CCCCCC; font-size: 1em;'},\
            {'selector': 'thead','props': 'height:100px'},\
            {'selector': 'th','props': 'background-color: white !important'}], overwrite=False)\
        .apply(lambda row: ['background:red' if cell == "P/N" else "" for cell in row])\
        .apply(lambda row: ['background:yellow' if row['course'][0:3] == "AP " and row['N/P/H/AP'][-2:] != "AP" else "" for cell in row] ,axis=1)\
        .apply(lambda row: ['background:#ffa533' if row['N/P/H/AP'] == "(N)" else "" for cell in row] ,axis=1)\
        .set_sticky(axis="columns",levels=0)\
        .set_sticky(axis="index")\
        .to_html()

    transcriptDFHTML = Markup(transcriptDFHTML)
    creditbydeptHTML = Markup(creditbydeptHTML)

    return render_template('transcripts/transcript.html', cols=list(transcriptDF.columns), transcriptHTML = transcriptDFHTML,tObj=tObj,student=student,creditbydeptHTML=creditbydeptHTML)

@app.route('/my/transcript/new', methods=['GET', 'POST'])
@app.route('/transcript/new', methods=['GET', 'POST'])
def transcriptNew():
    form = TranscriptForm()
    if form.validate_on_submit():
        html = form.transcript.data
        # with open('html.txt','w') as f:
        #     f.write(html)
        soup = BeautifulSoup(html,features="html.parser")

        try:
            stuName = soup.find('span',{'class':'student-full-name'})
            stuName = stuName.text.strip()
            stuName = " ".join(stuName.split())
        except:
            stuName = soup.find('div',{'class':"StudentName ellipsis"})
            stuName = stuName.text.strip()
            stuName = " ".join(stuName.split())
        acadGPA1 = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblGP'}).text.strip()
        acadGPA2 = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblGPN'}).text.strip()
        totalGPA1 = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblTP'}).text.strip()
        totalGPA2 = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblTPN'}).text.strip()
        tenTwelveGPA1 = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblCP'}).text.strip()
        tenTwelveGPA2 = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblCPN'}).text.strip()
        creditAtt = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblCA'}).text.strip()
        creditComp = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblCC'}).text.strip()
        classRank = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblCR'}).text.strip()
        classSize = soup.find('span',{'id':'ctl00_MainContent_subHIS_rptGPAInfo_ctl01_lblCS'}).text.strip()

        stats = {
            'acadGPA':(acadGPA1,acadGPA2),
            'totalGPA':(totalGPA1,totalGPA2),
            "tenTwelveGPA":(tenTwelveGPA1,tenTwelveGPA2),
            'credit':(creditAtt,creditComp),
            'rank':(classRank,classSize)
            }

        # strip extra whitespace from ends and center of string
        stuID = soup.find('span',attrs={"data-tcfc":"STU.ID"})
        stuID = int(stuID.text)

            
        if current_user.aeriesid != stuID and current_user.role.lower() == 'student':
            flash("You can only enter your own transcript and you can't enter a transcript if your student ID is not in your record")
            return redirect(url_for('index'))
        try:
            student = User.objects.get(aeriesid = stuID)
        except:
            tObj=None
            student = {'stuName':stuName,'aeriesid':stuID}
            flash("This student is not in OTData.")
        else:
            try:
                tObj = Transcript.objects.get(student=student)
            except:
                tObj = None
            else:
                flash(f"Deleting old transcript.")
                tObj.delete()

        results = soup.find('table',{"class":"CourseHistory"})
        all_tr = results.find_all('tr')
        transcript = []

        for tr in all_tr:
            schoolNum = tr.find('td',attrs={"data-tcfc":"HIS.ST"})
            schoolName = tr.find('span')
            grade = tr.find('td',attrs={"data-tcfc":"HIS.GR"})
            crsid = tr.find('td',attrs={"data-tcfc":"HIS.CN"})
            year = tr.find('td',attrs={"data-tcfc":"HIS.YR"})
            term = tr.find('td',attrs={"data-tcfc":"HIS.TE"})
            mark = tr.find('td',attrs={"data-tcfc":"HIS.MK"})
            course = tr.find('td',attrs={"data-tcfc":"CRS.CO"})
            otherCourse = tr.find('td',attrs={"data-tcfc":"HIS.CO"})
            cp = tr.find('td',attrs={"data-tcfc":"CRS.CP"})
            nh = tr.find('td',attrs={"data-tcfc":"CRS.NA"})
            cc = tr.find('td',attrs={"data-tcfc":"HIS.CC"})
            cr = tr.find('td',attrs={"data-tcfc":"HIS.CR"})

            if grade:
                txtCourse = course.text.strip()
                txtCourse = " ".join(txtCourse.split())
                if otherCourse:
                    txtOtherCourse = otherCourse.text.strip()
                    txtOtherCourse = " ".join(txtOtherCourse.split())
                row={
                    'sname':schoolName.attrs['title'],
                    'snum':schoolNum.text.strip(),
                    'grade':grade.text.strip(),
                    'year':year.text.strip(),
                    'term':term.text.strip(),
                    'mark':mark.text.strip(),
                    'course':txtCourse,
                    'crsid':crsid.text.strip(),
                    'altCourse':txtOtherCourse,
                    'cp':cp.text.strip(),
                    'nh':nh.text.strip(),
                    'cc':cc.text.strip(),
                    'cr':cr.text.strip()
                    }
                transcript.append(row)

        transcriptDF = pd.DataFrame.from_dict(transcript)

        transcriptDF['grade'] = pd.to_numeric(transcriptDF['grade'])
        transcriptDF = transcriptDF[transcriptDF.grade > 8]

        gp = [
            {'mark':'A+','gp':4},
            {'mark':'A','gp':4},
            {'mark':'A-','gp':4},
            {'mark':'B+','gp':3},
            {'mark':'B','gp':3},
            {'mark':'B-','gp':3},
            {'mark':'C+','gp':2},
            {'mark':'C','gp':2},
            {'mark':'C-','gp':2},
            {'mark':'D+','gp':1},
            {'mark':'D','gp':1},
            {'mark':'D-','gp':1},
            {'mark':'F+','gp':0},
            {'mark':'F','gp':0},
            {'mark':'F-','gp':0},
        ]

        gpDF = pd.DataFrame.from_dict(gp)

        transcriptDF = pd.merge(transcriptDF, 
                            gpDF, 
                            on ='mark', 
                            how ='left')

        ag = {'E':'English','Q':'Science','M':'Math','S':'Social Studies','Y':'Elective','Z':'Z?', 'G':'World Language','P':'Physical Education','R':'R?','B':'Art'}

        transcriptDF['a-g'] = transcriptDF.apply(lambda row: ag[row['crsid'][:1]],axis=1)
        col = transcriptDF.pop('a-g')
        transcriptDF.insert(7, col.name, col)
                        
        transcriptDF['cc'] = transcriptDF['cc'].astype('float64')
        transcriptDF['cr'] = transcriptDF['cr'].astype('float64')

        creditByDept = transcriptDF.groupby('a-g')['cc'].agg(['sum','count'])

        def addn(row):
            if row['cp'] != 'P' and row['nh'] not in ['N','H','AP']:
                return '(N)'
            else:
                return row['nh']

        transcriptDF['nh'] = transcriptDF.apply(lambda row: addn(row), axis=1)
        # Created an Adjusted Grade Points for Honors and AP whever grade is above a D
        transcriptDF['wgp'] = np.where(((transcriptDF['nh'] == "H") | (transcriptDF['nh'] == "H/AP")) & ((transcriptDF['gp'] > 1)), transcriptDF['gp']+1, transcriptDF['gp'])
        # Remove values from adjusted grade points that are not cllege prep
        transcriptDF['wgp'] = np.where((transcriptDF['nh'] == "N") | (transcriptDF['cp'] != "P"), np.nan, transcriptDF['wgp'])
        #transcriptDF['gp'] = np.where((transcriptDF['nh'] == "N") | (transcriptDF['cp'] != "P"), np.nan, transcriptDF['wgp'])
        #transcriptDF['credit'] = np.where((transcriptDF['nh'] == "N") | (transcriptDF['cp'] != "P"), np.nan, transcriptDF['wgp'])
        
        transcriptDF['credit'] = np.where(transcriptDF['gp'] > 0, transcriptDF['cr'],np.nan)
        transcriptDF['wcredit'] = np.where(transcriptDF['wgp'] > 0, transcriptDF['cr'],np.nan)

        # Sort the data
        transcriptDF = transcriptDF.sort_values(by=['grade', 'term','snum']).reset_index(drop=True)
        # created weighted colums that multiply the credits received by the gradepoints
        transcriptDF['totalgp'] = transcriptDF['cr']*transcriptDF['gp']
        transcriptDF['totalwgp'] = transcriptDF['cr']*transcriptDF['wgp']

        # get total for numeric columns
        transcriptDF.loc['total'] = transcriptDF[['cc','cr','totalgp','totalwgp','wcredit','credit']].sum()

        # Divide weighted columns by credit earned (cc) to get weighted averages
        #transcriptDF.loc['Ave'] = transcriptDF[['gp','wgp']].mean()
        transcriptDF.at['Ave','totalwgp'] = transcriptDF.at['total','totalwgp'] / transcriptDF.at['total','wcredit']
        transcriptDF.at['Ave','totalgp'] = transcriptDF.at['total','totalgp'] / transcriptDF.at['total','credit']
        stats['totalGPA2'] = (transcriptDF.at['Ave','totalwgp'],transcriptDF.at['Ave','totalgp'])
        def nhtocp(row):
            if len(str(row['nh'])) > 0:
                if len(str(row['cp'])) > 0:
                    return str(row['cp']) + '/' + str(row['nh'])
                else:
                    return str(row['nh'])
            else:
                return str(row['cp'])

        transcriptDF['cp'] = transcriptDF.apply(lambda row: nhtocp(row) ,axis=1)
        creditByDept = pd.pivot_table(transcriptDF,values="cc",index='a-g',columns='cp',aggfunc=sum, margins=True, margins_name='Sum')

        creditByDept = creditByDept.fillna('-')


        # Cleanup the NaN's
        transcriptDF[["sname","snum",'grade','year','term','cc','cr','mark','course','altCourse','cp','nh']] = transcriptDF[["sname","snum",'grade','year','term','cc','cr','mark','course','altCourse','cp','nh']].fillna('')
        transcriptDF.rename(columns={'cc': 'Credit Earned', 'cr': 'Credit Attempted', 'cp':'N/P/H/AP'}, inplace=True)
        transcriptDF = transcriptDF.drop(['nh'],axis=1)
        transcriptDF.index = transcriptDF.index.map(str)

        transcriptDict = transcriptDF.to_dict()
        tObj = Transcript(
            student=student,
            transcriptDF = transcriptDict,
            stats = stats,
            creditbydept = creditByDept
            )
        tObj.save()
        flash("Transcipt saved to OTData.")
        return redirect(url_for('transcript',aid=stuID))
    
    return render_template('transcripts/transcriptform.html',form=form)

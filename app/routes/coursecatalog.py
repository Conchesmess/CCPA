from app import app
import mongoengine.errors
from flask import render_template, flash, redirect, url_for, session
from markupsafe import Markup
from flask_login import current_user
from app.classes.data import Courses, Comment, TeacherCourse, User, StudentReview, Role
from app.classes.forms import StudentReviewForm, TeacherForm, CoursesForm, CommentForm, CourseFilterForm, TeacherCourseForm
from flask_login import login_required
import datetime as dt
from mongoengine import Q
import json

@app.route('/resultstocsv')
def resultsToCSV():
    courses = Courses.objects()
    coursesDict = json.loads(courses.to_json())
    tcDF = DataFrame(coursesDict)
    tcDF.to_csv('tc.csv')

    return render_template('index.html')

@app.route('/course/<courseID>')
@login_required
def course(courseID):
    thisCourse = Courses.objects.get(id=courseID)
    theseComments = Comment.objects(course=thisCourse)
    teacherCourses = TeacherCourse.objects(course = thisCourse)
    return render_template('course.html',course=thisCourse, comments=theseComments, teacherCourses=teacherCourses)


@app.route('/course/list', methods=['GET', 'POST'])
@app.route('/activecourses', methods=['GET', 'POST'])
@app.route('/activecourses/<skip>', methods=['GET', 'POST'])
@login_required
def activecourses(skip=0):
    skip=int(skip)
    limit=110

    form = CourseFilterForm()

    if form.validate_on_submit():

        if form.incomplete.data:
            form.department.data=""
            match = {"$match" : 
                    {
                        "$or":
                            [
                                {"course_department" : ""},
                                {"course_ag_requirement" : ""}
                            ]
                    },
                }
        elif form.department.data and form.name.data:
            # regex allows for partial matches and option i is case insensitive
            match = {"$match" : 
                    {
                        "course_department" : form.department.data,
                        "$or":
                            [   
                                {"course_name" : {"$regex":form.name.data, '$options' : 'i'}},
                                {"course_title" : {"$regex":form.name.data, '$options' : 'i'}}
                            ]
                    },
                }
        elif form.department.data and not form.name.data:
            match = {"$match" : 
                    {
                        "course_department" : form.department.data,
                    },
                }
        elif not form.department.data and form.name.data:
            match = {"$match" : 
                        {"$or":
                            [
                                {"course_name" : {"$regex":form.name.data, '$options' : 'i'}},
                                {"course_title" : {"$regex":form.name.data, '$options' : 'i'}}
                            ]
                        },
                    }
        countPipeline = [
                {"$match" : {"course_department" : form.department.data}},
                {"$lookup":
                    {
                    "from": "TeacherCourses",
                    "localField": "teacher",
                    "foreignField": "teacher",
                    "as": "courses"
                    }
                },
                {
                    "$count": "total"  # No. of documents to skip (Should be `0` for Page - 1)
                }
            ]
        total = Courses.objects().aggregate(countPipeline)
        total = list(total)[0]['total']
        limit = total
        skip = 0
        pipeline = [
                match,
                {"$lookup":
                    {
                    "from": "TeacherCourses",
                    "localField": "teacher",
                    "foreignField": "teacher",
                    "as": "courses"
                    }
                },
                {
                    "$skip": skip  # No. of documents to skip (Should be `0` for Page - 1)
                },
                {
                    "$limit": limit  # No. of documents to be displayed on your webpage
                }
            ]
    else:
        # pipeline is how pymongo access the mongodb aggregation API 
        # https://pymongo.readthedocs.io/en/stable/examples/aggregation.html
        # the $lookup aggregation stage is how mongodb does "outer left joins"
        # which means everything in table1 (left) and everything in table2 (right) that is in table 1
        pipeline = [
                    {"$lookup":
                        {
                        "from": "TeacherCourses",
                        "localField": "teacher",
                        "foreignField": "teacher",
                        "as": "courses"
                        }
                    },
                    {
                        "$skip": skip  # No. of documents to skip (Should be `0` for Page - 1)
                    },
                    {
                        "$limit": limit  # No. of documents to be displayed on your webpage
                    }
            ]
        countPipeline = [
                    {"$lookup":
                        {
                        "from": "TeacherCourses",
                        "localField": "teacher",
                        "foreignField": "teacher",
                        "as": "courses"
                        }
                    },
                    {
                        "$count": "total"  # No. of documents to skip (Should be `0` for Page - 1)
                    }
            ]
    # aggregate is how mongoengine access pymongo 
    # http://docs.mongoengine.org/guide/querying.html#aggregation
        total = Courses.objects().aggregate(countPipeline)
        total = list(total)[0]['total']
    courses = Courses.objects().aggregate(pipeline)
    skip=skip+limit

    return render_template('courses.html',courses=courses,skip=skip,limit=limit,total=total,title="Active Courses",form=form)


@app.route('/course/new', methods=['GET', 'POST'])
@login_required
def courseNew():
    if not current_user.isadmin:
        flash("Only Admins can create new courses.")
        return redirect(url_for('activecourses'))

    form = CoursesForm()

    if form.validate_on_submit():

        newCourse = Courses(
            course_number = form.course_number.data,
            course_title = form.course_title.data,
            course_name = form.course_name.data,
            course_ag_requirement = form.course_ag_requirement.data,
            course_difficulty = form.course_difficulty.data,
            course_department = form.course_department.data,
            course_gradelevel = form.course_gradelevel.data,
            modify_date = dt.datetime.utcnow()
        )
        newCourse.save()

        return redirect(url_for('course',courseID=newCourse.id))

    return render_template('coursesform.html',form=form)


@app.route('/course/edit/<courseID>', methods=['GET', 'POST'])
@login_required
def courseEdit(courseID):
    editCourse = Courses.objects.get(id=courseID)
    if not current_user.isadmin:
        flash("You can't edit a course unless you are an admin.")
        return redirect(url_for('course',courseID=courseID))
    form = CoursesForm()
    if form.validate_on_submit():

        editCourse.update(
            course_name = form.course_name.data,
            course_ag_requirement = form.course_ag_requirement.data,
            course_difficulty = form.course_difficulty.data,
            course_department = form.course_department.data,
            course_ = form.course_pathway.data,
            course_gradelevel = form.course_gradelevel.data,
            modify_date = dt.datetime.utcnow()
        )
        return redirect(url_for('course',courseID=courseID))

    form.course_number.data = editCourse.course_number
    form.course_gradelevel.data = editCourse.course_gradelevel
    form.course_title.data = editCourse.course_title
    form.course_name.data = editCourse.course_name
    form.course_ag_requirement.data = editCourse.course_ag_requirement
    form.course_difficulty.data = editCourse.course_difficulty
    form.course_department.data = editCourse.course_department
    form.course_pathway.data = editCourse.course_pathway

    return render_template('coursesform.html',form=form, course=editCourse)

@app.route('/course/delete/<courseID>')
@login_required
def courseDelete(courseID):
    try:
        deleteCourse = Courses.objects.get(id=courseID)
    except:
        flash("This course doesn't exist.  I may have already been deleted.")
    else:
        if current_user.isadmin:
            flash(f'The Course {deleteCourse.course_title} is being deleted.')
            deleteCourse.delete()
        else:
            flash("You can't delete a post you don't own.")
    courses = Courses.objects()  
    form = CourseFilterForm()

    return redirect(url_for('activecourses'))


@app.route('/teachercourse/<tcid>')
@login_required
def teachercourse(tcid):
    thisTC = TeacherCourse.objects.get(id=tcid)
    sRevs = StudentReview.objects(teacher_course = thisTC)
    return render_template("teachercourse.html",tCourse = thisTC, sRevs=sRevs)


@app.route('/teachercourse/delete/<tcid>')
@login_required
def teachercourseDelete(tcid):
    if current_user.isadmin:
        delTCID = TeacherCourse.objects.get(id=tcid)
        teacherID = delTCID.teacher.id
        delTCID.delete()
    else:
        flash('Only Admins can delete.  If you teach this class you should be able to edit.')
    return redirect(url_for('teacher',teacherID=teacherID))


@app.route('/teachercourse/edit/<tcid>',methods=["GET","POST"])
@login_required
def teacherCourseEdit(tcid):
    thisTC = TeacherCourse.objects.get(id=tcid)
    if current_user.id != thisTC.teacher.id and not current_user.isadmin:
        flash("You can only edit this if it is your class.")
        return redirect(url_for('teachercourse',tCourse = thisTC))
    form = TeacherCourseForm()
    if form.validate_on_submit():
        thisTC.update(
            course_description = form.course_description.data,
            course_link = form.course_link.data
        )
        return redirect(url_for('teachercourse',tcid=thisTC.id))
    form.course_description.data = thisTC.course_description
    form.course_link.data = thisTC.course_link
    return render_template('teachercourseform.html',form=form,teacherCourse=thisTC)


@app.route('/teachercourse/add/<teacherID>')
@app.route('/teachercourse/add/<teacherID>/<courseID>')
@login_required
def teacherCourseAdd(teacherID,courseID=None):
    if 'teacher' not in current_user.roles:
        flash('You are not a teacher.')
        return redirect(url_for('teacher/list'))
    
    if courseID == None:
        courses = Courses.objects()
        teacher = User.objects.get(id=teacherID)
        return render_template('teachercourseadd.html', teacher = teacher, courses=courses)
    
    if teacherID != current_user.id and not current_user.isadmin:
        flash("You don't have the privleges to add this teacher course.")
        return redirect(url_for("teacher",teacherID=teacherID))
    else:
        newTeachercourse = TeacherCourse(
            teacher = teacherID,
            course = courseID,
            teachercourseid = f"{teacherID}-{courseID}"
        )
        newTeachercourse.save()
        return redirect(url_for("teacher",teacherID=teacherID))
    
@app.route('/teacher/list/<letter>')
@app.route('/teacher/list')
@login_required
def teacherList(letter=None):
    teacherFirstLetters = set()
    teacherObj = Role.objects.get(name__iexact="teacher")
    allTeachers = User.objects(roles__contains=teacherObj)
    for teacher in allTeachers:
        teacherFirstLetters.add(teacher.lname[0].upper())
    teacherFirstLetters = list(teacherFirstLetters)
    teacherFirstLetters.sort()

    if letter:
        teachers = User.objects(roles__contains=teacherObj,lname__istartswith=letter)
    else:
        teachers=allTeachers

    return render_template('teachers.html',teachers=teachers,teacherFirstLetters=teacherFirstLetters)

def findChoice(choices,value):
    choiceList = ""
    choice="<So Much Empty>"
    for data in choices:
        if data[0] > 0:
            choiceList = choiceList + f"{data[0]} - {data[1]} <br>"
        if value == data[0]:
            choice = f"{data[0]}-{data[1]}"
        if value == 0:
            choice = "<So Much Empty>"
    choiceList = Markup(choiceList)
    return(choice,choiceList)


@app.route('/teacher/<teacherID>')
@login_required
def teacher(teacherID):
    teacher = User.objects.get(id=teacherID)
    form = TeacherForm()
    
    tCourses = TeacherCourse.objects(teacher=teacher)
    return render_template('teacher.html',teacher=teacher,tCourses=tCourses, form=form)

@app.route('/teacher/edit/<teacherID>', methods=['GET', 'POST'])
@login_required
def teacherEdit(teacherID):

    if teacherID != str(current_user.id) and not session['isadmin']:
        flash("You don't have the privleges to edit this record.")
        return redirect(url_for('teacher',teacherID=teacherID))

    form = TeacherForm()
    teacher = User.objects.get(id=teacherID)

    if form.validate_on_submit():
        if not form.troom_phone.data:
            form.troom_phone.data = 0
        fname=form.fname.data.title()
        lname=form.lname.data.title()
        teacher.update(
            troom_number = form.troom_number.data,
            tdescription = form.tdescription.data,
            tdepartment = form.tdepartment.data,
            tdivision = form.tdivision.data,
            troom_phone = form.troom_phone.data,
            pronouns = form.pronouns.data,
            fname = fname,
            lname = lname,
            late_work = form.late_work.data,
            late_work_policy = form.late_work_policy.data,
            feedback = form.feedback.data,
            feedback_policy = form.feedback_policy.data,
            classcontrol = form.classcontrol.data,
            classcontrol_policy = form.classcontrol_policy.data,
            classroom = form.classroom.data,
            grading_policy = form.grading_policy.data
        )
        if form.image.data:
            if teacher.image:
                teacher.image.delete()
            teacher.image.put(form.image.data, content_type = 'image/jpeg')
            teacher.save()

        return redirect(url_for('teacher',teacherID=teacherID))

    form.troom_number.data = teacher.troom_number
    form.tdescription.data = teacher.tdescription
    if teacher.troom_phone != 0:
        form.troom_phone.data = teacher.troom_phone
    form.tdepartment.data = teacher.tdepartment
    form.tdivision.data = teacher.tdivision
    form.pronouns.data = teacher.pronouns
    form.fname.data = teacher.fname
    form.lname.data = teacher.lname
    form.late_work.process_data(teacher.late_work)
    form.late_work_policy.process_data(teacher.late_work_policy)
    form.feedback.process_data(teacher.feedback)
    form.feedback_policy.process_data(teacher.feedback_policy)
    form.classcontrol.process_data(teacher.classcontrol)
    form.classcontrol_policy.process_data(teacher.classcontrol_policy)
    form.classroom.process_data(teacher.classroom)
    form.grading_policy.process_data(teacher.grading_policy)

    return render_template('teacheredit.html', form=form, teacher=teacher)

@app.route('/srevs')
def srevs():
    if current_user.email != "stephen.wright@ousd.org":
        return redirect("/")
    sRevs = StudentReview.objects()
    return render_template('srevs.html',sRevs=sRevs)

@app.route('/srev/delete/<srid>')
def srevdelete(srid):
    thisSRev = StudentReview.objects.get(id=srid)
    if current_user.isadmin or current_user == thisSRev.student:
        thisSRev.delete()
        return redirect(url_for('profile'))
    flash("You can't delete this review.")
    return redirect(url_for('profile'))

@app.route('/studentreview/new/<tcid>', methods=['GET', 'POST'])
@login_required
def studentReviewNew(tcid):
    tCourse = TeacherCourse.objects.get(id=tcid)
    reviews = StudentReview.objects(teacher_course=tCourse,student=current_user)
    if len(reviews) > 0:
        flash("you have already reviewed this class. You can delete it from your profile page.")
        return redirect(url_for("teachercourse",tcid=tcid))

    form = StudentReviewForm()

    if form.validate_on_submit():

        newStudentReview = StudentReview(
            teacher_course = tCourse,
            student = current_user,
            year_taken = form.year_taken.data,
            late_work = form.late_work.data,
            feedback = form.feedback.data,
            classcontrol = form.classcontrol.data,
            grading_policy = form.grading_policy.data,
            classroom_environment = form.classroom_environment.data,
            modify_date = dt.datetime.utcnow()
        )

        newStudentReview.save()

        return render_template("studentreview.html", sRev=newStudentReview)
    
    form.classcontrol.data = 3
    form.feedback.data = 3
    form.grading_policy.data = 3
    form.classroom_environment.data = 3
    form.late_work.data = 3
    
    return render_template("studentreviewform.html", form=form, tCourse=tCourse)



@app.route('/comment/new/<courseID>', methods=['GET', 'POST'])
@login_required
def commentNew(courseID):
    course = Courses.objects.get(id=courseID)
    form = CommentForm()
    if form.validate_on_submit():
        newComment = Comment(
            author = current_user.id,
            course = courseID,
            content = form.content.data
        )
        newComment.save()
        return redirect(url_for('course',courseID=courseID))
    return render_template('commentform.html',form=form,course=course)

@app.route('/comment/edit/<commentID>', methods=['GET', 'POST'])
@login_required
def commentEdit(commentID):
    editComment = Comment.objects.get(id=commentID)
    if current_user != editComment.author:
        flash("You can't edit a comment you didn't write.")
        return redirect(url_for('post',courseID=editComment.course.id))
    course = Courses.objects.get(id=editComment.course.id)
    form = CommentForm()
    if form.validate_on_submit():
        editComment.update(
            content = form.content.data,
            modify_date = dt.datetime.utcnow()
        )
        return redirect(url_for('course',courseID=editComment.course.id))

    form.content.data = editComment.content

    return render_template('commentform.html',form=form,course=course)   

@app.route('/comment/delete/<commentID>')
@login_required
def commentDelete(commentID): 
    deleteComment = Comment.objects.get(id=commentID)
    deleteComment.delete()
    flash('The comments was deleted.')
    return redirect(url_for('course',courseID=deleteComment.course.id)) 

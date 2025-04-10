from tokenize import String
from typing import Text
from flask.app import Flask
from flask_wtf import FlaskForm
from wtforms_components import TimeField
from wtforms.validators import Length, URL, NumberRange, Email, Optional, InputRequired, ValidationError, DataRequired
from wtforms import IntegerRangeField, ColorField, URLField, DateField, DateTimeField, EmailField, widgets, SelectMultipleField, StringField, SubmitField, validators
from wtforms import TextAreaField, HiddenField, IntegerField, SelectField, FileField, BooleanField, FloatField
import datetime as d
from zoneinfo import ZoneInfo
import phonenumbers

departments = [("",""),("Mathmatics","Mathmatics"),("Science", "Science"),("English", "English"),("Visual and Performing Arts", "Visual and Performing Arts"),("Humanities", "Humanities"),("PE", "Physical Education (PE)"), ("World Languages", "World Languages"), ("CompSci", "Computer Science"),("Other Elective","Other Elective")]
onetoten = [(0,"---"),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8),(9,9),(10,10)]

class ComputerCartForm(FlaskForm):
    name = StringField('Cart Name', validators=[DataRequired()])
    room = StringField('Room', validators=[DataRequired()])

class ComputerForm(FlaskForm):
    #cart = ReferenceField()
    number = StringField()
    serial = StringField(unique=True)
    os = StringField()

class TeacherForm(FlaskForm):
    pronouns = StringField('Pronouns')
    fname = StringField('First Name', validators=[DataRequired()])
    lname = StringField('Last Name', validators=[DataRequired()]) 
    troom_number = StringField('Room Number')
    tdivision = SelectField('Division', choices=[("",""),('D1','D1'),("D2","D2"),("D3","D3")])
    tdescription = TextAreaField('Description')
    tdepartment = SelectField('Department',choices=departments)
    troom_phone = StringField('Phone Number', validators=[Optional()])
    image = FileField("Image") 
    late_work = IntegerRangeField('Late Work')
    late_work_policy = TextAreaField('Late Work Policy', render_kw={"placeholder": "Late Work Policy (optional)"})
    feedback = IntegerRangeField('Openness to Feedback')
    feedback_policy = TextAreaField('Feedback Policy')
    classcontrol = IntegerRangeField('Classroom Environment')
    classcontrol_policy = TextAreaField('Class Control Policy')
    grading_policy = TextAreaField('Grading Policy')
    classroom = TextAreaField('Tell us about your classroom.')
    submit = SubmitField('Submit')

class CoursesForm(FlaskForm):
    course_number = StringField('Course Number')
    course_title = StringField('Course Title')
    course_name = StringField('Course Name', validators=[DataRequired()])
    course_ag_requirement = SelectField('Courses A-G Requirement',choices=[("",""),("A-History","A-History"),("B-English", "B-English"), ("C-Mathematics","C-Mathematics"), ("D-Science","D-Science"), ("E-Language Other Than English","E-Language Other Than English"), ("F-Visual And Performing Arts","F-Visual And Performing Arts"), ("G-College-Preparatory Elective","G- College-Preparatory Elective")])
    course_difficulty = SelectField('Course Difficulty',choices=[("",""),("AP","Advanced Placement (AP)"),("HP", "Honors (HP)"),("CP","College Prep (CP)")])
    course_difficulty = SelectField('Course Difficulty',choices=[("",""),("AP","Advanced Placement (AP)"),("HP", "Honors (HP)"),("CP","College Prep (CP)")])
    course_department = SelectField('Course Department',choices=departments)
    course_gradelevel = SelectField('Grade Level', choices=[("",""),("9th","9th"),("10th","10th"),("11th","11th"),("12th","12th"),("Any","Any")])
    submit = SubmitField('Add Course')

class TeacherCourseForm(FlaskForm):
    teacher = SelectField('Teacher',choices=[],validate_choice=False)
    course = SelectField('Course',choices=[],validate_choice=False)
    course_description = TextAreaField('Course Description')
    course_link = URLField("Link to syllabus",validators=[(Optional()),URL()], render_kw={"placeholder": "https://..."})
    submit = SubmitField('Submit')

class StudentReviewForm(FlaskForm):
    year_taken = IntegerField("Year You Took the Course",validators=[(InputRequired())])
    late_work = IntegerRangeField("Late Work",validators=[(InputRequired())])
    feedback = IntegerRangeField("Feedback",validators=[(InputRequired())])
    classcontrol = IntegerRangeField("Class Control",validators=[(InputRequired())])
    grading_policy = IntegerRangeField("Grading Policy",validators=[(InputRequired())])
    classroom_environment = IntegerRangeField("Classroom Environment",validators=[(InputRequired())])
    submit = SubmitField('Submit')

class CourseFilterForm(FlaskForm):
    department = SelectField('Department',choices = departments)
    name = StringField('Course Name')
    incomplete = BooleanField('Incomplete')
    submit = SubmitField("Search")

class AddressForm(FlaskForm):
    name = StringField()
    streetAddress = StringField()
    city = StringField()
    state = StringField()
    zipcode = IntegerField()
    description = TextAreaField()
    addresstype = SelectField(choices=[('','---'),('Work','Work'),('Residence','Residence')])
    submit = SubmitField('Save')

class CollegeForm(FlaskForm):
    name = StringField("Name")
    gradyear = IntegerField("Graduation Year")
    submit = SubmitField("Save")

class QRForm(FlaskForm):
    QRText = StringField()
    size = SelectField(choices=[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8),(9,9),(10,10)])
    borderSize = SelectField(choices=[(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8),(9,9),(10,10)])
    colorDark = ColorField()
    colorLight = ColorField()
    colorDataDark = ColorField()
    colorDataLight = ColorField()
    submit = SubmitField("Enter")

class WCloudForm(FlaskForm):
    text = TextAreaField()
    stopwords = TextAreaField()
    submit = SubmitField('Submit')

class PortfolioSubmissionForm1(FlaskForm):
    origin = SelectField(choices=[(None,"-----"),('Class','Class'),('Personal Project','Personal Project'),('Job','Job'),('Program/Internship','Program/Internship')])
    # Fields that are only for the class origin type
    per = SelectField(validators=[validators.Optional()],choices=[(None,'-----'),('1',1),('2',2),('3',3),('4',4),('5',5),('6',6),('7',7),('8',8)])
    teacher = SelectField(choices=[]) 
    subject = SelectField(choices=[
        (None,'-----'),
        ('Math','Math'),
        ('English','English'),
        ('Science','Science'),
        ('Computer Science','Computer Science'),
        ('Social Science','Social Science'),
        ('Art','Art'),
        ('World Language','World Language'),
        ('Music','Music'),
        ('Other','Other')
        ])
    year = IntegerField("School Year")
    term = SelectField(choices=[
        (None,'-----'),
        ("1st Semester","1st Semester"),
        ("2nd Semester","2nd Semester")
        ])
    grade = SelectField(choices=[(None,'-----'),(6,6),(7,7),(8,8),(9,9),(10,10),(11,11),(12,12)])
    writing = BooleanField()    
    submit = SubmitField('Submit')

class PortfolioSubmissionForm2(FlaskForm):
    name = StringField() # for all types
    reflection = TextAreaField() # student's reflection on their work
    rating = SelectField(choices=[(None,"-----"),('Green','Green'),('Yellow','Yellow'),('Red','Red')]) # student's 1-5 on the quality of this work
    submit = SubmitField('Submit')

class GFileSeachForm(FlaskForm):
    nameContains = StringField()
    allTime = BooleanField()
    ownedByMe = BooleanField()
    viewedByMe = BooleanField()
    fileSearchSubmit = SubmitField("Search")

class PortfolioSubmissionFileForm(FlaskForm):
    gfileids = StringField(id="content")
    fileSubmit = SubmitField("Submit")


# class PortfolioSubmissionForm(FlaskForm):
#     origin = SelectField(choices=[(None,"-----"),('Class','Class'),('Personal Project','Personal Project'),('Job','Job'),('Program/Internship','Program/Internship')])
#     # Fields that are only for the class origin type
#     per = SelectField(validators=[validators.Optional()],choices=[(None,'-----'),('1',1),('2',2),('3',3),('4',4),('5',5),('6',6),('7',7),('8',8)])
#     teacher = SelectField(choices=[]) 
#     subject = SelectField(choices=[
#         (None,'-----'),
#         ('Math','Math'),
#         ('Science','Science'),
#         ('Computer Science','Computer Science'),
#         ('Social Science','Social Science'),
#         ('Art','Art'),
#         ('World Language','World Language'),
#         ('Music','Music'),
#         ('Other','Other')
#         ])
#     year = IntegerField("School Year")
#     term = SelectField(choices=[
#         (None,'-----'),
#         ("1st Semester","1st Semester"),
#         ("2nd Semester","2nd Semester")
#         ])
#     grade = SelectField(choices=[(None,'-----'),(6,6),(7,7),(8,8),(9,9),(10,10),(11,11),(12,12)])
#     # Fields for all types
#     file = URLField() # want to try and use google drive for file storage
#     writing = BooleanField() # Is this an example of the student's writing ability
#     name = StringField() # for all types
#     reflection = TextAreaField() # student's reflection on their work
#     rating = SelectField(choices=[(None,"-----"),('Green','Green'),('Yellow','Yellow'),('Red','Red')]) # student's 1-5 on the quality of this work
#     psubsubmit = SubmitField('Submit')

class TextAreaForm(FlaskForm):
    csv = TextAreaField()
    taSubmit = SubmitField("Submit")

class InternshipStakeholderForm(FlaskForm):
    title = StringField(validators=[InputRequired()])
    name = StringField(validators=[Optional()])
    story = TextAreaField(validators=[Optional()])
    stakeholderSubmit = SubmitField('Submit')


class SignatureForm(FlaskForm):
    emailOut = EmailField(validators=[InputRequired(),Email()])

class TimeSheetForm(FlaskForm):
    date = DateField(default=d.datetime.now(ZoneInfo('US/Pacific')))
    start_time_hr = SelectField(choices=[(12,12),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8),(9,9),(10,10),(11,11)],validators=[InputRequired()])
    start_time_min = SelectField(choices=[(0,"00"),(15,15),(30,30),(45,45)],validators=[InputRequired()])
    start_time_am_pm = SelectField(choices=[('PM','PM'),('AM','AM')],validators=[InputRequired()])
    end_time_hr = SelectField(choices=[(12,12),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8),(9,9),(10,10),(11,11)],validators=[InputRequired()])
    end_time_min = SelectField(choices=[(0,"00"),(15,15),(30,30),(45,45)],validators=[InputRequired()])
    end_time_am_pm = SelectField(choices=[('PM','PM'),('AM','AM')],validators=[InputRequired()])
    desc = TextAreaField('What did you do?',validators=[InputRequired()] )
    submit = SubmitField('Submit')

class InternshipActivityForm(FlaskForm):
    title = StringField()
    desc = TextAreaField()
    activitySubmit = SubmitField("Submit")

class InternshipImpactForm(FlaskForm):
    metric = StringField()
    howCollected = TextAreaField()
    howConnected = TextAreaField()
    impactSubmit = SubmitField("Submit")

class InternshipForm(FlaskForm):
    site_name = StringField(validators=[InputRequired()])
    ccpa_staff = EmailField(validators=[Optional()])
    contact_fname = StringField()
    contact_lname = StringField()
    contact_email = EmailField(validators=[Optional(),Email()])
    contact_phone_areacode = StringField(validators=[Optional(),Length(min=3,max=3,message="Must be three characters")])
    contact_phone_prefix = StringField(validators=[Optional(),Length(min=3,max=3,message="Must be three characters")])
    contact_phone_suffix = StringField(validators=[Optional(),Length(min=4,max=4,message="Must be four characters")])
    street = StringField()
    street2 = StringField()
    city = StringField()
    state = StringField(default="CA")
    zipcode = StringField()
    phone_areacode = StringField(validators=[Optional(),Length(min=3,max=3,message="Must be three characters")])
    phone_prefix = StringField(validators=[Optional(),Length(min=3,max=3,message="Must be three characters")])
    phone_suffix = StringField(validators=[Optional(),Length(min=4,max=4,message="Must be four characters")])
    notes = TextAreaField()
    image = FileField("Image: ")
    vision = TextAreaField()
    mission = TextAreaField()
    submit = SubmitField('Submit')

class AddToCohortForm(FlaskForm):
    emails = TextAreaField()
    aeriesIds = TextAreaField()
    sortCohort = StringField(validators=[InputRequired()])
    gclassmongoid = SelectField(validators=[InputRequired()],choices=[],validate_choice=False)
    submit = SubmitField()

class BreakSettingsForm(FlaskForm):
    breakstartdate = DateField(default=d.datetime.now(ZoneInfo('US/Pacific')))
    breakstarthrs = SelectField(choices=[(8,8),(9,9),(10,10),(11,11),(12,12),(13,1),(14,2),(15,3)])
    breakstartmins = IntegerField(IntegerField(validators=[(NumberRange(min=0, max=59, message="Must be a number between 0 and 59."))]))
    classenddate = DateField(default=d.datetime.now(ZoneInfo('US/Pacific')))
    classendhrs = SelectField(choices=[(8,8),(9,9),(10,10),(11,11),(12,12),(13,1),(14,2),(15,3)])
    classendmins = IntegerField(IntegerField(validators=[(NumberRange(min=0, max=59, message="Must be a number between 0 and 59."))]))
    submit = SubmitField("Submit")

class SimpleForm(FlaskForm):
    field = TextAreaField(validators=[InputRequired()])
    submit = SubmitField("Submit")

class GroupMsgForm(FlaskForm):
    msg = TextAreaField(validators=[InputRequired()])
    parents = BooleanField(default=False)
    submit = SubmitField("Submit")

class DateForm(FlaskForm):
    querydate = DateField("Date", id="queryDate")
    submitDateForm = SubmitField("Submit", id="submitDateForm")

class SearchDatesForm(FlaskForm):
    start_date = DateField("Start Date", id="start_date")
    end_date = DateField("End Date", id="end_date")
    submit = SubmitField("Search")

class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()

class StudentWasHereForm(FlaskForm):
    student = MultiCheckboxField('Students:')
    submitStuForm = SubmitField("Submit",id="submitStuForm")

class ActiveClassesForm(FlaskForm):
    gclassid = SelectField(choices=[])
    students = SelectField(choices=[],validators=[(validators.Optional())],validate_choice=False)
    submit = SubmitField("Submit")

class TokenForm(FlaskForm):
    numTokens = SelectField("Number of Tokens",choices=[(1,1)],validators=[InputRequired()])
    owner = SelectField("To",choices=[],validators=[InputRequired()],validate_choice=False)
    note = TextAreaField("Note",validators=[InputRequired()])
    submit = SubmitField("Send")

class SendemailForm(FlaskForm):
    to = MultiCheckboxField(choices=[])
    cc = MultiCheckboxField(choices=[])
    otherto = StringField()
    from_ = EmailField('From',validators=[(validators.Optional()),(Email())])
    subject = StringField()
    body = TextAreaField()
    submit = SubmitField("Submit")

class TxtMessageForm(FlaskForm):
    to = StringField("To")
    body = TextAreaField("Message")
    submit = SubmitField("Send")

class StudentNoteForm(FlaskForm):
    content = TextAreaField("Note:")
    type_ = SelectField("Type:",choices=[('---','---'),('Mtg', 'Mtg'),('Call','Call'),('Note','Note')])
    date = DateField(default=d.datetime.now(ZoneInfo('US/Pacific')))
    submit = SubmitField("Submit")

class StudentForm(FlaskForm):
    fname = StringField("First Name")
    lname = StringField("Last Name")
    aeriesid = IntegerField(validators=[(validators.Optional()),(NumberRange(min=100000, max=999999, message="Must be a 6 digit number."))])
    oemail = EmailField()
    grade = IntegerField(validators=[(validators.Optional()),(NumberRange(min=100000, max=999999, message="Must be a 6 digit number."))])
    submit = SubmitField("Submit")

class NewStudentForm(FlaskForm):
    afname = StringField("First Name",validators=[InputRequired()])
    alname = StringField("Last Name",validators=[InputRequired()])
    aeriesid = IntegerField("6 digit Aeries ID", validators=[InputRequired(),(NumberRange(min=100000, max=999999, message="Must be a 6 digit number."))])
    oemail = EmailField('OUSD Email',validators=[InputRequired(),(Email())])
    grade = SelectField('Grade', choices=[(None,'-'),(9,9),(10,10),(11,11),(12,12)],validators=[InputRequired()])
    submit = SubmitField("Submit")

class CheckInForm(FlaskForm):
    desc = TextAreaField("What specifically have you done since the last class.",validators=[InputRequired()])
    other = TextAreaField()
    assigns = SelectField("Assignments",choices=[],validators=[InputRequired()])
    #gclassid = SelectField(choices=[],validators=[InputRequired()])
    #gclassname = StringField()
    status = SelectField("How are you?",choices=[('','---'),('5','Very Productive'),('4','Mostly'),('3','Meh'),('2','Not really'),('1', 'Not')],validators=[InputRequired()])
    #synchronous = SelectField(id="synchronous",choices=[('synchronous','synchronous'),('asynchronous','asynchronous')])
    #camera = SelectField(id="cameraoff",choices=[("on","on"),("off","off")])
    #cameraoffreason = SelectField("Why do you want your camera off today for this class?",id="cameraoffreason",choices=[('','---'),('poor bandwidth','poor bandwidth'),('zoom fatigue','zoom fatigue'),('visual distraction','visual distraction'),('my current environment','current environment'),('other','other')])
    #cameraoffreasonother = TextAreaField(id="cameraoffreasonother")
    approved = BooleanField("Approved")
    submit = SubmitField('Submit')

class GClassForm(FlaskForm):
    classname = StringField() # for user to input a custom name
    status = SelectField("Status:",choices=[('Inactive','Inactive'),('Active','Active')])
    submit = SubmitField()

class UserForm(FlaskForm):
    fname = StringField("First Name")
    lname = StringField("Last Name")
    image = FileField("Image")
    ufname = StringField("First Name")
    ulname = StringField("Last Name")
    pronouns = StringField()
    birthdate = DateField()
    personalemail = EmailField('Personal Email',validators=[(validators.Optional()),(Email())])
    mobile = StringField()
    ustreet = StringField()
    ustreet2 = StringField()
    ucity = StringField()
    ustate = StringField()
    uzipcode = IntegerField(validators=[(validators.Optional()),(NumberRange(min=10000, max=99999, message="Must be a 5 digit number."))])
    #altphone = IntegerField(validators=[(validators.Optional()),(NumberRange(min=1000000000, max=9999999999, message="Must be a 7 digit number with no space or other characters."))])
    altphone = StringField()
    ugender = TextAreaField()
    uethnicity = MultiCheckboxField(choices=[("Decline to say","Decline to say"),('American Indian or Alaskan Native','American Indian or Alaskan Native'), ('Asian Indian','Asian Indian'), ('Black or African American','Black or African American'), ('Cambodian','Cambodian'), ('Chinese','Chinese'), ('Filipino','Filipino'), ('Guamanian','Guamanian'), ('Hawaiian','Hawaiian'), ('Hispanic or Latino','Hispanic or Latino'), ('Hmong','Hmong'), ('Japanese','Japanese'), ('Korean','Korean'), ('Laotian','Laotian'), ('Samoan','Samoan'), ('Vietnamese','Vietnamese'), ('White','White')])
    uethnicityother = TextAreaField()
    shirtsize = SelectField("Unisex Shirt Size", choices=[('','---'),('xs','xs'),('sm','sm'),('med','med'),('lg','lg'),('xl','xl'),('xxl','xxl'),('3xl','3xl'),('4xl','4xl')],validators=[(validators.Optional())])
    linkedin = URLField()
    lat = FloatField(validators=[Optional()])
    lon = FloatField(validators=[Optional()])
    submit = SubmitField("Submit")

class AdultForm(FlaskForm):
    preferredcontact = BooleanField()
    fname = StringField()
    lname = StringField()
    relation = StringField()
    mobile = StringField()
    altphone = StringField()
    email = EmailField(validators=[(validators.Optional()),(Email())])
    altemail = EmailField(validators=[(validators.Optional()),(Email())])
    street = TextAreaField()
    city = StringField()
    state = StringField()
    zipcode = IntegerField(validators=[(validators.Optional()),(NumberRange(min=10000, max=99999, message="Must be a 5 digit number."))])
    notes = TextAreaField()
    primarylang = StringField()
    needstranslation = BooleanField()
    submit = SubmitField("Submit")

class BreakForm(FlaskForm):
    gclassid = SelectField(choices=[])
    duration = IntegerField()
    submit = SubmitField('Submit')

class ComputerForm(FlaskForm):
    equiptype = SelectField(choices=[('','---'),('Thinkpad','Thinkpad'),('Dell102','Dell Room 102 (Wright)'),('Dell104','Dell Room 104 (Ong)'),('Dell105','Dell Room 105 (Ketcham)')],validators=[InputRequired()])
    idnum = StringField('ID Number on the Equipment:',validators=[InputRequired()])
    location = SelectField(choices=[('','---'),(102,102),(104,104),(105,105)],validators=[InputRequired()])
    stickernum = IntegerField('Number on a sticker:',)
    statusdesc = TextAreaField('Description')
    status = SelectField(choices=[('','---'),('Working','Working'),('Problem','Problem'),('Not Working','Not Working')],validators=[InputRequired()])
    submit = SubmitField('Submit')

    def validate_statusdesc(self,status):
        if self.status.data != "Working" and len(self.statusdesc.data) == 0:
            raise ValidationError("Status Description: You need to have a status description of the status isn't 'Working'.")

class CommentForm(FlaskForm):
    content = TextAreaField("Comment")
    submit = SubmitField("Submit")

class PostForm(FlaskForm):
    subject = StringField("Title")
    body = TextAreaField("Body")
    submit = SubmitField("Submit")

class EventForm(FlaskForm):
    title = StringField("Title")
    desc = StringField("Description")
    date = DateField("Date", format='%Y-%m-%d')
    time = TimeField("Time")
    submit = SubmitField("Submit")

class FeedbackForm(FlaskForm):
    url = StringField()
    subject = StringField('Subject')
    body = TextAreaField('Description')
    solution = TextAreaField('Solution')
    status = SelectField("Status", choices=[('4-New','4-New'),('1-In Progress','1-In Progress'),('2-Complete','2-Complete'),('3-Maybe Someday','3-Maybe Someday')], default='4-New')
    priority = SelectField("Priority", choices=[('1-High','1-High'),('2-Medium','2-Medium'),('3-Low','3-Low')], default='3-Low')
    submit = SubmitField('Submit')

class CohortForm(FlaskForm):
    cohort = SelectField("Cohort", choices=[("","Unknown"),('No Academy','No Academy'),('Oakland Tech - Computer Academy','Oakland Tech - Computer Academy'),('Oakland Tech-Engineering Academy','Oakland Tech-Engineering Academy'),('Oakland Tech - Fashion, Art and Design Academy (All)','Oakland Tech - Fashion, Art and Design Academy (All)'),('Oakland Tech - Fashion, Arts, & Design Academy (CPA)','Oakland Tech - Fashion, Arts, & Design Academy (CPA)'),('Oakland Tech - Health Academy','Oakland Tech - Health Academy'),('Oakland Tech - Race, Policy and Law Academy','Oakland Tech - Race, Policy and Law Academy'),('Oakland Tech-9th Grade Janus','Oakland Tech-9th Grade Janus'),('Oakland Tech-9th Grade Neptune','Oakland Tech-9th Grade Neptune'),('Oakland Tech-9th Grade Sol','Oakland Tech-9th Grade Sol')])
    casemanager = SelectField(choices=[('',''),('Jelani Noble', 'Jelani Noble')])
    submit = SubmitField('Submit')

class ListQForm(FlaskForm):
    #cohort = MultiCheckboxField("Cohort: ", choices=[])
    grade = MultiCheckboxField("Grade: ", choices=[])
    gender = MultiCheckboxField("Gender: ", choices=[])
    advisor = SelectField("Advisor: ", choices=[])
    #ethnicity = MultiCheckboxField("Ethnicity: ", choices=[])
    results = SelectField("Results", choices=[('list','list'),('map','map')])
    submit = SubmitField("Submit")

class SortOrderCohortForm(FlaskForm):
    sortOrderCohort = SelectField("Sort Value:",choices=[],validate_choice=False)
    gid = HiddenField()
    gmail = HiddenField()
    gclassid = HiddenField()
    order = HiddenField()
    submit = SubmitField("Submit")

class PlanThemeForm(FlaskForm):
    name = StringField("Name: ",validators=[InputRequired()])
    timeframe = SelectField("Timeframe: ",choices=[('','----'),('Year','Year'),('Semester','Semester'),('Season','Season')])
    description = TextAreaField("Description: ",validators=[InputRequired()])
    old = BooleanField("Old")
    submit = SubmitField("Submit")

class PlanSettingsForm(FlaskForm):
    timeframe = SelectField("Time Frame", choices=[(None,'---'),('Season','Season'),('Semester','Semester'),('Year','Year')], validators=[InputRequired()])
    yearbegin = DateField("Year Begin", validators=[InputRequired()])
    summerbegin = DateField("Semester Summer Begin", validators=[InputRequired()])
    seasonwinterbegin = DateField("Winter Begin", validators=[InputRequired()])
    seasonspringbegin = DateField("Spring Begin", validators=[InputRequired()])
    semestertwobegin = DateField("Semester Two Begin", validators=[InputRequired()])
    submit = SubmitField("Submit")

class PlanInterventionForm(FlaskForm):
    status = SelectField("Status: ", choices=[('New','New'),('In Progress','In Progress'),('Flagged','Flagged'),('Monitorring','Monitorring'),('Complete','Complete')])
    type_ = SelectField("Intervention: ", choices=[('Tutoring','Tutoring'),('Case Manager','Case Manager'),('Other','Other')])
    statusother = StringField("Other: ")
    description = TextAreaField("Description: ")
    submit = SubmitField("Submit")

class PlanIdealOutcomeForm(FlaskForm):
    name = StringField("Name: ",validators=[InputRequired()])
    description = TextAreaField("Description: ",validators=[InputRequired()])
    example = TextAreaField("Example",validators=[InputRequired()])
    submit = SubmitField("Submit")

class PlanCheckinForm(FlaskForm):
    # todayfocus = SelectField(choices="",validators=[InputRequired()])
    todayfocus = MultiCheckboxField(choices="",validators=[InputRequired()])
    yesterdayrating = SelectField(choices=[(0,'--'),(4,4),(3,3),(2,2),(1,1)],validate_choice=False)
    yesterdaynarrative = TextAreaField()
    todaynarrative = TextAreaField(validators=[InputRequired()])
    submit = SubmitField("Submit")

class CourseForm(FlaskForm):
    aeriesname = StringField('Aeries Name:')
    aeriesnum = StringField('Aeries #:')
    name = StringField('Course Name:')
    dept = SelectField("Department: ", choices=[("","----"),('Math','Math'),('Science','Science'),('CTE','CTE'),('PE','PE'),('English/Language Arts','English/Language Arts'),('Social Studies','Social Studies'),('Art','Art-visual and performing'),('World Languages','World Lqanguages'),('SPED','SPED'),('ELD','English Language Development'),('Computer Science','Computer Science')])
    atog = SelectField('A - G: ', choices=[("","----"),('A-History','A-History'),('B-English','B-English'),('C-Math','C-Math'),('D-Science','D-Science'),('E-Language','E-Language other than English'),('F-Art','F-Visual and performaing arts'),('G-Elective','G-College-preparatory elective')])
    level = SelectField("Level: ", choices=[("","----"),('CP','College Prep'),('HP','Honors'),('AP','Advanced Placement')])
    notupdated = BooleanField("Edited?")
    aeriesnum = StringField("Aeries Number")
    aeriesname = StringField("Aeries Name")
    pathway = SelectField("Pathway",validators=[(validators.Optional())], choices=[('','----'),('Computer','Computer'),('Engineering','Engineering'),('Fashion, Art, Design and Animation','Fashion, Art, Design and Animation'),('Health','Health'),('Race, Policy and Law','Race, Policy and Law')])
    yearinschool = MultiCheckboxField("Year",validators=[(validators.Optional())],choices=[("9th","9th"),("10th","10th"),("11th","11th"),("12th","12th")])
    submit = SubmitField('Submit')

class SectionForm(FlaskForm):
    pers = MultiCheckboxField('Periods',choices=[(0,0),(1,1),(2,2),(3,3),(4,4),(5,5),(6,6),(7,7),(8,8)])
    url = URLField('URL: ')
    desc = TextAreaField('Description: ')
    pathway = SelectField("Pathway", choices=[('','----'),('Computer','Computer'),('Engineering','Engineering'),('Fashion, Art, Design and Animation','Fashion, Art, Design and Animation'),('Health','Health'),('Race, Policy and Law','Race, Policy and Law')])
    prereq = TextAreaField('Prerequisites: ')
    yearinschool = MultiCheckboxField('Year: ',choices=[("9th","9th"),("10th","10th"),("11th","11th"),("12th","12th")])
    # modified = BooleanField("Modified?: ") # Mark this modified to update the last modified date so users know it has been updated for this year.
    submit = SubmitField('Submit')

class GroupsForm(FlaskForm):
    name = StringField('Group Name')
    desc = TextAreaField('Group Description')
    students = TextAreaField('Students')
    submit = SubmitField('Submit')

class PostGradForm(FlaskForm):
    type_ = SelectField("Type", validators=[InputRequired()], choices=[("","----"), ("Work","Work"), ("Gap Year","Gap Year"), ("2yr College","2yr College"),("4yr College","4yr College"),("Trade School","Trade School")])
    org = StringField(validators=[InputRequired()])
    link = URLField(validators=[(validators.Optional()),(URL())])
    major = StringField(validators=[(validators.Optional())])
    graduated = BooleanField(validators=[(validators.Optional())])
    desc = TextAreaField(validators=[(validators.Optional())])
    yr_started = IntegerField(validators=[InputRequired()])
    yr_ended = IntegerField(validators=[(validators.Optional())])
    pg_st_address = TextAreaField(validators=[(validators.Optional())])
    pg_city = StringField(validators=[(validators.Optional())])
    pg_state = StringField(validators=[(validators.Optional())])
    pg_zip = IntegerField(validators=[(validators.Optional())])
    submit = SubmitField("Submit")

class ScheduleForm(FlaskForm):
    active = BooleanField(validators=[InputRequired()])
    name = StringField(validators=[InputRequired()])
    submit = SubmitField("Submit")

class ScheduleClassForm(FlaskForm):
    per = IntegerField(validators=[InputRequired()])
    startHr = IntegerField(validators=[InputRequired()])
    startMin = IntegerField(validators=[InputRequired()])
    endHr = IntegerField(validators=[InputRequired()])
    endMin = IntegerField(validators=[InputRequired()])
    submit = SubmitField("Submit")

class StandardForm(FlaskForm):
    name = StringField(validators=[InputRequired()])
    desc = TextAreaField()
    gclass = SelectField("Google Classroom", choices=[],validators=[InputRequired()],validate_choice=False)
    submit = SubmitField("Submit")

class AssignmentForm(FlaskForm):
    standards = MultiCheckboxField("Standards",choices=[],validate_choice=False)
    submit = SubmitField("Submit")


class ProjectForm(FlaskForm):
    name = StringField('Name')
    course = SelectField('Course',choices=[('Robotics DE','Robotics DE'),('Computer Science Priniciples','Computer Science Priniciples'),('Other','Other'),('None','None',)])
    open_to_contributors = BooleanField()
    #desc = TextAreaField('Description')
    product = TextAreaField('What do you think you will make?')
    learning_materials = TextAreaField('Links and descriptions to videos or other learning materials.')
    status = SelectField('Status',choices=[('In Progress','In Progress'),('Done','Done')])
    submit = SubmitField('Enter')

class MilestoneForm(FlaskForm):
    status = SelectField('Status',choices=[('In Progress','In Progress'),('Done','Done'),('Delete','Delete')])
    name = StringField('Name')
    desc = TextAreaField('Description')
    submit = SubmitField('Save')

class ProjPostForm(FlaskForm):
    post_type = SelectField("Type", choices=[('','---'),('Intention','Intention'),('Reflection','Reflection'),('Discussion','Discussion')], validators=[DataRequired()])
    confidence = SelectField("Confidence",choices=[(0,'---'),(3,"Very"),(2,'Sorta'),(1,'Not')])
    satisfaction = SelectField("Satisfaction",choices=[(0,'---'),(3,"Very"),(2,'Sorta'),(1,'Not')])
    reflection = TextAreaField("Reflection")
    intention = TextAreaField("Intention")
    discussion = TextAreaField("Discussion")
    milestone = SelectField("Milestone",choices=[],validate_choice=False)
    image_reflection = FileField("Image")
    image_reflection_src = StringField()
    submit = SubmitField("Save")

class ObstacleForm(FlaskForm):
    name = StringField('Name')
    desc = TextAreaField('Why is this an obstacle?')
    submit = SubmitField('Save')

class TranscriptForm(FlaskForm):
    transcript = TextAreaField('Transcript HTML')
    submit = SubmitField('Submit')
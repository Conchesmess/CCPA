from mongoengine import Document, EmbeddedDocumentListField, DictField, ObjectIdField
from mongoengine import URLField, StringField, IntField, ReferenceField, EmbeddedDocument
from mongoengine import DateTimeField, ListField, URLField, FileField, CASCADE
from bson.objectid import ObjectId
import datetime as d


# _____________________ Start CourseCatalog

class Courses(Document): 
    course_number = StringField(required=True,unique=True)
    course_title = StringField()
    course_name = StringField()
    course_ag_requirement = StringField()
    course_difficulty = StringField()
    course_department = StringField()
    course_pathway = StringField()
    course_gradelevel = StringField()
    create_date = DateTimeField(default=d.datetime.utcnow())
    modify_date = DateTimeField()

    meta = {
        'ordering': ['-createdate'],
        'indexes':
            [
                {
                    'fields': ['course_name','course_title'],
                    'collation' : {'locale': 'en', 'strength': 2} 
                }   
            ]
        }

class TeacherCourse(Document):
    teachercourseid = StringField(sparse=True, required=True,unique=True)
    teacher = ReferenceField('User',reverse_delete_rule=CASCADE, required=True) 
    course = ReferenceField('Courses',reverse_delete_rule=CASCADE,required=True)
    course_description = StringField()
    course_files = FileField()
    course_link = StringField()
    create_date = DateTimeField(default=d.datetime.utcnow())
    modify_date = DateTimeField()

    meta = {
        'ordering': ['-createdate']
    }

class StudentReview(Document):
    teacher_course = ReferenceField('TeacherCourse')
    student = ReferenceField('User')
    year_taken = IntField()
    late_work = IntField()
    feedback = IntField()
    classcontrol = IntField()
    grading_policy = IntField()
    classroom_environment = IntField()
    create_date = DateTimeField(default=d.datetime.utcnow())
    modify_date = DateTimeField()

class Comment(Document):
    author = ReferenceField('User',reverse_delete_rule=CASCADE) 
    course = ReferenceField('Courses',reverse_delete_rule=CASCADE)
    content = StringField()
    create_date = DateTimeField(default=d.datetime.utcnow())
    modify_date = DateTimeField()
    role = StringField("Role")

    meta = {
        'ordering': ['-createdate']
    }

# End CourseCatalog


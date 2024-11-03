from mongoengine import Document, EmbeddedDocumentListField, DictField, ObjectIdField
from mongoengine import URLField, StringField, IntField, ReferenceField, EmbeddedDocument
from mongoengine import DateTimeField, ListField, URLField, CASCADE
from bson.objectid import ObjectId
import datetime as d


# a join table between GoogleClassroom and User
class GEnrollment(Document):
    gclassroom = ReferenceField('GoogleClassroom', required=True, sparse=True)
    owner = ReferenceField('User', unique_with='gclassroom', sparse=True, required=True, reverse_delete_rule=CASCADE)
    createdate = DateTimeField(default=d.datetime.utcnow)
    status = StringField(default='~~~') # Created by student active, inacative, ignore
    classnameByUser = StringField() # created by user for sorting
    nummissingupdate = DateTimeField()
    missingasses = DictField()
    missinglink = StringField()
    sortCohort = StringField(default='~')
    submissionsupdate = DateTimeField()
    mysubmissions = DictField()
    myassignments = DictField()

class StandardLevel(Document):
    oid = ObjectIdField(default=ObjectId())
    level = IntField()
    name = StringField()
    desc = StringField()
    courseWorkIDs = ListField()
    standard = ReferenceField("Standard", required=True)

class Standard(Document):
    name = StringField(required=True)
    desc = StringField(required=True)
    gclass = ReferenceField('GoogleClassroom', required=True, unique_with='name')
    meta = {
        'ordering': ['+name']
    }

# depricated
class CourseWork(Document):
    gclassroom = ReferenceField('GoogleClassroom', required=True)
    courseworkid = StringField(unique=True, sparse=True, required=True)
    courseworkdict = DictField()
    createdate = DateTimeField(default=d.datetime.utcnow)
    lastupdate = DateTimeField()
    standards = ListField(ReferenceField('StandardLevels'))
    topic = StringField()


class GoogleClassroom(Document):
    teacher = ReferenceField('User')
    gteacherdict = DictField()
    gclassdict = DictField()
    courseworkdict = DictField()
    # courseworkdict values: https://developers.google.com/classroom/reference/rest/v1/courses.courseWork
    courseworkupdate = DateTimeField()
    # TODO move this to CourseWork class
    studsubsdict = DictField()
    studsubsupdate = DateTimeField()
    gclassid = StringField(unique=True)
    teacher = ReferenceField('User')
    # This is a list of possible cohorts for this class
    sortcohorts = ListField()
    #This filed is used to iteratively build the roster from Google Classroom
    #It should be empty excetp during the process of retrieving the roster
    #From Google Classroom
    grosterTemp = ListField(DictField())
    aeriesid = StringField()
    aeriesname = StringField()
    pers = ListField()

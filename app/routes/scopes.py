# Scopes are what google calls the privleges necessary to do certain things.
# These scopes are communicated to the user when they log in to the app.
# This OAuth 2.0 access scope allows for full read/write access to the
# authenticated user's account and requires requests to use an SSL connection.

# For a thorough description of how to do stuff, go to the feedback.py file.

# anothr possible email scope if we want to manage a Label for the user
# 'https://www.googleapis.com/auth/gmail.labels'

scopes_ousd = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
    'openid',
    #'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/classroom.courses.readonly',
    'https://www.googleapis.com/auth/classroom.rosters.readonly',
    'https://www.googleapis.com/auth/classroom.profile.emails',
    'https://www.googleapis.com/auth/classroom.profile.photos',
    'https://www.googleapis.com/auth/classroom.student-submissions.students.readonly',
    'https://www.googleapis.com/auth/classroom.student-submissions.me.readonly',
    'https://www.googleapis.com/auth/classroom.guardianlinks.students',
    'https://www.googleapis.com/auth/classroom.guardianlinks.me.readonly',
    'https://www.googleapis.com/auth/classroom.topics.readonly'
    #'https://www.googleapis.com/auth/drive.install',
    #'https://www.googleapis.com/auth/drive.appdata',
    #'https://www.googleapis.com/auth/drive.file',
    #'https://www.googleapis.com/auth/drive.metadata',
    #'https://www.googleapis.com/auth/drive',
    #'https://www.googleapis.com/auth/documents.readonly'
    ]
    
# 'https://www.googleapis.com/auth/drive.appfolder'
# 'https://www.googleapis.com/auth/drive.resource',



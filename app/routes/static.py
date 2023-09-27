from app import app
from flask import render_template, redirect, session, flash, url_for

@app.route('/static')
def statichtml():
    return render_template('static.html')

from app import app
from app.classes.forms import QRForm
#from .users import credentials_to_dict
from flask import render_template, redirect, session, flash, url_for, Markup
from flask_login import current_user, login_required
# from time import sleep
# from os import path
# from PIL import Image
# from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
# import matplotlib.pyplot as plt
# import matplotlib
import base64
import io
import segno

@app.route('/qr', methods=['GET', 'POST'])
@login_required
def qr():
    form = QRForm()

    if form.validate_on_submit():

        qrcode = segno.make_qr(form.QRText.data)
        buff = io.BytesIO()
        qrcode.save(
            buff,
            kind='png',
            scale=form.size.data,
            border=int(form.borderSize.data),
            dark=form.colorDark.data,
            light=form.colorLight.data,
            data_dark=form.colorDataDark.data, 
            data_light=form.colorDataLight.data
        )
        buff.seek(0)
        encoded_img_data = base64.b64encode(buff.getvalue())

        return render_template('qr.html',img_data=encoded_img_data.decode('utf-8'),form=form)

    form.colorLight.process_data('#FFFFFF')
    form.colorDark.process_data('#000000')
    form.colorDataDark.process_data('#000000')
    form.colorDataLight.process_data('#FFFFFF')
    form.size.process_data('6')
    form.borderSize.process_data('2')

    return render_template('qr.html',form=form)
from app import app
from app.classes.forms import WCloudForm
#from .users import credentials_to_dict
from flask import render_template, redirect, session, flash, url_for, Markup
from flask_login import current_user
from time import sleep
from os import path
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
import matplotlib
import base64
import io

@app.route('/wordcloud', methods=['GET', 'POST'])
def wordcloud():
    form = WCloudForm()
    if form.validate_on_submit():
        text = form.text.data
        # Create and generate a word cloud image:
        wordcloud = WordCloud(width=1000,height=1000,min_word_length=3,max_words=400,min_font_size=8)
        stopwords = form.stopwords.data
        stopwords = stopwords.split(',')
        if len(stopwords[0])>0:
            flash(f"These are the ommitted words {stopwords}")
        for word in stopwords:
            wordcloud.stopwords.add(word)
        wordcloud.generate(text)
        words = wordcloud.words_

        # Display the generated image:
        matplotlib.use('agg')
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")

        data = io.BytesIO()
        plt.savefig(data, format='jpeg')
        data.seek(0)
        im = Image.open(data)
        im.save(data, "jpeg")
        encoded_img_data = base64.b64encode(data.getvalue())

        return render_template("wordcloud.html", img_data=encoded_img_data.decode('utf-8'),form=form, words=words)

    return render_template('wordcloud.html',form=form)



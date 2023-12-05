from app import app
from app.classes.forms import WCloudForm
from .users import credentials_to_dict
from flask import render_template, redirect, session, flash, url_for, Markup
from os import path
from PIL import Image
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import matplotlib.pyplot as plt
from flask_login import current_user
from time import sleep

@app.route('/theme', methods=['GET', 'POST'])
def theme():
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

        # Display the generated image:
        plt.imshow(wordcloud, interpolation='bilinear')
        plt.axis("off")
        plt.savefig(f'app/static/wc/{current_user.id}.png')
        sleep(5)
        return render_template('theme.html',form=form)

    return render_template('theme.html',form=form)


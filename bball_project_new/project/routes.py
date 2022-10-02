# Routes to different domains


# General
import numpy as np
import pandas as pd

import sys
import os
import glob
import re
import secrets
import pickle
from PIL import Image
from keras.preprocessing import image
# from werkzeug.datastructures import FileStorage

# Flask Utilities
from flask import render_template, url_for, flash, redirect, request
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
# from gevent.pywsgi import WSGIServer
# from flask_uploads import configure_uploads, IMAGES, UploadSet


# Project
from project import app, db, bcrypt
from project.forms import RegistrationForm, LoginForm, UpdateAccountForm, SubmitImageForm
from project.models import User, Post


posts = [{
            'author': 'Edmond',
            'title': 'EDMOND WANG',
            'content': 'Edmond is the student of black mamba.',
            'date': '2021'
         },  
         {
            'author': 'Kobe',
            'title': 'Black Mamba',
            'content': 'Kobe is the black mamba. ',
            'date': '1978'
         }]

MODEL_PATH = 'project/forest_clf.pkl'

model = None

def load_model():
    global model
    model = pickle.load(open(MODEL_PATH, 'rb'))


# CV2 is a highly optimised library focused on computer vision p- image processing, video capture and analysis
# def processImageCV2(IMG_PATH):

    # image = cv2.imread(IMG_PATH)
    # image = cv2.resize(image, (200, 200))
    # image = image.astype('float') / 255.0
    # image = img_to_array(image)
    # image = np.expand_dims(image, axis=0)


def processImage(IMG_PATH):
    img = image.load_img(IMG_PATH, target_size=(255, 255))
    img = image.img_to_array(img)
    img = img.reshape(255*255*3)
    # img = np.expand_dims(img, axis=0)
    return img

# def pytorchTransform(image_bytes):
#     transform = transforms.Compose([transforms.Resize(255),
#                                     transfors.CenterCrop(224),
#                                     transforms.ToTensor(),
#                                     transforms.Normalize(
#                                         [0.485, 0.456, 0.406],
#                                         [0.229, 0.224, 0.225])])
#     image = Image.open(io.BytesIO(image_bytes))
#     return transform(image).unsqueeze(0)

def getPrediction(path):
    load_model()
    image = processImage(path)
    preds = model.predict([image])
    return preds


# different pages - using route decorators
# adding additional functionalities
@app.route('/')
@app.route('/home')
def home():
    return render_template('home.html', posts=posts)


@app.route('/about')
def about():
    return render_template('about.html', title='About')


def save_image_ml(form_image, path, size):
    # Randomly hashing the image
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename) # _ for throw-away variables
    image_fn = random_hex + f_ext # name
    image_path = os.path.join(app.root_path, path, image_fn) # path

    # Automatic resizing
    output_size = (size, size)
    image_resize = Image.open(form_image)
    image_resize.thumbnail(output_size)
    image_resize.save(image_path)

    return image_fn


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    form = SubmitImageForm()
    if form.validate_on_submit():
        filename = secure_filename(form.image.data.filename)
        form.image.data.save(os.path.join(
            app.config['UPLOAD_FOLDER'], 'classify_pics/', filename
        ))
        # form.image.data.save(os.path.join(
        #     app.root_path, 'static/uploads/classify_pics/', filename
        # ))
        # return render_template('upload.html', filename=filename)
        flash('Photo uploaded', 'success')
        return redirect(url_for('predict'))
        # return render_template('predict.html', title='Predict', filename=filename)
        # return redirect(url_for('outcome'))
    return render_template('upload.html', title='Upload', form=form)


# Dummy one - for testing
@app.route('/display', methods=['GET', 'POST'])
def display():
    # No idea why it requires a relative path and sometimes an absolute path
    # filename = os.path.join(app.config['UPLOAD_FOLDER'], '21d.png')
    filename = os.path.join('static/uploads/classify_pics', '21d.png')
    return render_template('blah.html', user_image=filename)


@app.route('/predict', methods=['GET', 'POST'])
def predict():
    # path = os.path.join(app.root_path, 'static/uploads/classify_pics', '21d.png')
    image_name = 'jordan.jpg'
    absolute_path = os.path.join(app.config['UPLOAD_FOLDER'], 'classify_pics', image_name)
    relative_path = os.path.join('static/uploads/classify_pics', image_name)
    if getPrediction(absolute_path) == [0]:
        result = 'Basketball'
    else:
        result = 'Non-Basketball'
    return render_template('predict.html', title='Predict', user_image=relative_path, data=result)


# @app.route('/wtf', method=['GET', 'POST'])
# def display():
#     path_abs = os.path.join(app.config['UPLOAD_FOLDER'], 'classify_pics', '21d.png')
#     path_rlt = os.path.join('static/uploads/classify_pics', '21d.png')
#     return render_


# Accepting kinds of requests
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Account created for {form.username.data}.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if form.email.data == 'admin@test.com' and form.password.data == 'strongpassword':
            flash(f'ADMINISTRATOR LOGIN. Greetings.', 'success')
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))            
        elif user and bcrypt.check_password_hash(user.password, form.password.data):
            flash(f'SUCCESSFUL LOGIN.', 'success')
            login_user(user, remember=form.remember.data)
            # args is dictionary - the 'get' method only returns if it exists
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('LOGIN FAILED. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    flash('You have successfully logged out. Good day.', 'success')
    return redirect(url_for('home'))


def save_image(form_image):
    # Randomly hashing the image
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_image.filename) # _ for throw-away variables
    image_fn = random_hex + f_ext # name
    image_path = os.path.join(app.root_path, 'static/profile_pics', image_fn) # path

    # Automatic resizing
    output_size = (125, 125)
    image_resize = Image.open(form_image)
    image_resize.thumbnail(output_size)
    image_resize.save(image_path)

    return image_fn

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        # Saving the image
        if form.image.data:
            image_file = save_image(form.image.data)
            current_user.image_file = image_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Account has been updated.', 'success')
        # POST, GET, REDIRECT Pattern
        # After form is submitted, if page reloaded it will ask whether you want to submit another POST request.
        # This redirection causes the browser to send a GET request.
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', 
                            image_file=image_file, form=form)


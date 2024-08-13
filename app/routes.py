from datetime import datetime, timezone
import os
import traceback
from flask import render_template, flash, redirect, current_app, abort, url_for, request
from werkzeug.utils import secure_filename
from urllib.parse import urlsplit
from flask_login import current_user, login_user, logout_user, login_required
from sqlalchemy import select
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm
from app.models import User

@app.route('/')
@app.route('/index')
@login_required
def index():
    user = {'username' : 'Rafig'}
    posts = [
        {
            'author': {'username': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'username': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    return render_template('index.html', title='Home', posts=posts)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/registration', methods=['GET', 'POST'])
def registration():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(select(User).where(User.username == username))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)

@app.route('/user/<username>/avatar/<int:size>')
@login_required
def user_avatar(username, size):
    user = db.session.execute(select(User).where(User.username == username)).scalar_one_or_none()
    if user is None:
        abort(404)
    return user.avatar(size)

@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        
        if form.profile_picture.data:
            pic_file = form.profile_picture.raw_data[0]
            
            try:
                pic_filename = secure_filename(pic_file.filename)
                pic_extension = '.png'
                pic_filename = f'{current_user.id}{pic_extension}'
                pic_path = os.path.join(current_app.static_folder, 'avatars', pic_filename)
                
                if not os.path.exists(current_app.static_folder):
                    print(f'{current_app.static_folder} does not exist')
                
                avatars_path = os.path.join(current_app.static_folder, 'avatars')
                if not os.path.exists(avatars_path):
                    print(f'{avatars_path} does not exist')

                with open(pic_path, 'wb') as f:
                    file_data = pic_file.read()
                    f.write(file_data)

                current_user.profile_picture = pic_filename

            except Exception as e:
                print('Exception occurred:')
                print(traceback.format_exc())
                flash(f'Error: {e}')
                return redirect(url_for('edit_profile'))

        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', title='Edit Profile', form=form)

@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()

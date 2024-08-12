from typing import Optional
import os
from datetime import datetime, timezone
from PIL import Image
from hashlib import md5
import tempfile
from flask import send_file, abort, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import sqlalchemy as sa
import sqlalchemy.orm as so
from flask_login import UserMixin
from app import db, login

class User(UserMixin, db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    username: so.Mapped[str] = so.mapped_column(sa.String(64), index=True,
                                                unique=True)
    email: so.Mapped[str] = so.mapped_column(sa.String(120), index=True,
                                             unique=True)
    password_hash: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256))
    about_me: so.Mapped[Optional[str]] = so.mapped_column(sa.String(140))
    last_seen: so.Mapped[Optional[datetime]] = so.mapped_column(
        default=lambda: datetime.now(timezone.utc))
    profile_picture: so.Mapped[Optional[str]] = so.mapped_column(sa.String(256), default='default.png')


    posts: so.WriteOnlyMapped['Post'] = so.relationship(
        back_populates='author')
    
    def avatar(self, size):
        avatars_dir = os.path.join(current_app.static_folder, 'avatars')
        if self.profile_picture and os.path.isfile(os.path.join(avatars_dir, self.profile_picture)):
            image_path = os.path.join(avatars_dir, self.profile_picture)
        else:
            image_path = os.path.join(avatars_dir, 'default.png')

        if not os.path.exists(image_path):
            abort(404)

        with Image.open(image_path) as img:
            img.thumbnail((size, size))
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as temp_file:
                img.save(temp_file, 'PNG')
                temp_file.seek(0)
                return send_file(temp_file.name, mimetype='image/png', as_attachment=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

class Post(db.Model):
    id: so.Mapped[int] = so.mapped_column(primary_key=True)
    body: so.Mapped[str] = so.mapped_column(sa.String(140))
    timestamp: so.Mapped[datetime] = so.mapped_column(
        index=True, default=lambda: datetime.now(timezone.utc))
    user_id: so.Mapped[int] = so.mapped_column(sa.ForeignKey(User.id),
                                               index=True)

    author: so.Mapped[User] = so.relationship(back_populates='posts')

    def __repr__(self):
        return '<Post {}>'.format(self.body)

@login.user_loader
def load_user(id):
    return db.session.get(User, int(id))

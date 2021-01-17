from flask_sqlalchemy import SQLAlchemy
from cubot import app
db = SQLAlchemy(app)




class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}')"

    def is_authenticated(self):
        return True

    def is_active(self): # line 37
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    # Required for administrative interface
    def __unicode__(self):
        return self.username


class Post(db.Model):
 
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False, unique=True)
    

    def __repr__(self):
        return f"Post('{self.content}')"

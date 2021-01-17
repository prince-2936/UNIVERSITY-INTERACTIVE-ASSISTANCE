from flask import Flask, redirect, url_for, request,render_template, flash

from flask_login import login_user, current_user, logout_user, login_required
import nltk
import warnings
import sqlite3
import numpy as np
import random
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf import FlaskForm


app = Flask(__name__)
app.config['SECRET_KEY'] = 'abc'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.secret_key = 'xxxxyyyyyzzzzz'

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


from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo


class RegistrationForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password',
                                     validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('That email is taken. Please choose a different one.')


class LoginForm(FlaskForm):
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


GREETING_INPUTS = ("hello", "hi", "greetings", "sup", "what's up","hey",)
GREETING_RESPONSES = ["hi", "hey", "*nods*", "hi there", "hello", "I am glad! You are talking to me"]

f=open('cu_chatbot_data.txt','r',errors = 'ignore')
raw=f.read()
raw=raw.lower()
sent_tokens = nltk.sent_tokenize(raw)
lemmer = nltk.stem.WordNetLemmatizer()
def LemTokens(tokens):
    return [lemmer.lemmatize(token) for token in tokens]

remove_punct_dict = dict((ord(punct), None) for punct in string.punctuation)

def LemNormalize(text):
    return LemTokens(nltk.word_tokenize(text.lower().translate(remove_punct_dict)))


def greeting(sentence):
    """If user's input is a greeting, return a greeting response"""
    global GREETING_INPUTS
    global GREETING_RESPONSES
    for word in sentence.split():
        if word.lower() in GREETING_INPUTS:
            return random.choice(GREETING_RESPONSES)


def response(user_response):
    robo_response=''
    
    #sent_tokens.append(user_response)    
    TfidfVec = TfidfVectorizer(tokenizer=LemNormalize, stop_words='english')
    tfidf = TfidfVec.fit_transform(sent_tokens)
    u = TfidfVec.transform([user_response])
    #print(TfidfVec.get_feature_names())
    vals = cosine_similarity(u, tfidf)
    #print(vals.argsort()[0])
    idx=vals.argsort()[0][-1]
    #print(idx)
    flat = vals.flatten()
    flat.sort()
    #print(flat)
    req_tfidf = flat[-1]
    if(req_tfidf==0):
        robo_response=robo_response+"I am sorry! I don't understand you"
        post = Post(content=user_response)
        db.session.add(post)
        db.session.commit()
        return robo_response
    else:
        robo_response = robo_response+sent_tokens[idx]
        return robo_response




@app.route('/home')
def home():
    return render_template('index.html')

@app.route('/qus',methods = ['POST', 'GET'])
def qus():
    if request.method == 'POST':
        qustion = request.form['qus']
                 
        if greeting(qustion) != None:
            return render_template('index.html',rows = greeting(qustion))

        if qustion in ['bye','exit','goodbye','thanks','thankyou','thank']:
            return render_template('end.html')
        qus = qustion.lower().translate(remove_punct_dict)
        con = sqlite3.connect("hey_cu.db")
        #con.row_factory = sqlite3.Row
        cur = con.cursor()
        cur.execute("SELECT answers FROM cu WHERE qustions  LIKE  '%{}%'".format(qustion))
        rows = cur.fetchone();
        if rows != None:
            return render_template('index.html',rows = ''.join(rows))
        else:
            return render_template('index.html',rows = response(qus))
            
            
    else:
      
      return render_template("index.html")



@app.route("/register", methods=['GET', 'POST'])
def register():
    
    form = RegistrationForm()
    if form.validate_on_submit():
        
        user = User(username=form.username.data, email=form.email.data, password=form.password.data,)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', title='Register', form=form)


@app.route("/", methods=['GET', 'POST'])
def login():
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and (user.password == form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

if __name__ == '__main__':
    login_manager = LoginManager()
    login_manager.login_view = 'login'
    login_manager.init_app(app)
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    app.run(debug=True)
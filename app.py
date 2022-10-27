from flask import Flask, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from datetime import datetime
import os

base_dir = os.path.dirname(os.path.realpath(__file__))

db = SQLAlchemy()

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///' + \
    os.path.join(base_dir, 'blogga.db')
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = '368a9fb9cbe27df3ac61bd23'

db.init_app(app)

login_manager = LoginManager(app)


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer(), primary_key=True)
    firstname = db.Column(db.String, nullable=False)
    lastname = db.Column(db.String, nullable=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(60), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=False)
    post = db.relationship('BlogPost', backref='owned_user', lazy=True)

    def __repr__(self):
        return f"User <{self.username}>"


class BlogPost(db.Model):
    __tablename__ = 'blog_post'
    id = db.Column(db.Integer(), primary_key=True)
    caption = db.Column(db.String(), nullable=False)
    content = db.Column(db.String(), nullable=False)
    posted_by = db.Column(db.Integer(), db.ForeignKey('user.username'))
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"BlogPost <{self.picture}>, <{self.caption}>, <{self.content}>, <{self.date_created}>"


@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


@app.route('/')
@app.route('/blogposts')
def home():
    posts = BlogPost.query.all()

    context = {
        'posts':posts
    }
    return render_template('index.html', **context)

# @app.route('/')
# def get_all_posts():


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        return redirect(url_for('index'))

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        user = User.query.filter_by(username=username).first()
        if user:
            return redirect(url_for('register'))

        email_exists = User.query.filter_by(email=email).first()
        if email_exists:
            return redirect(url_for('register'))

        password_hash = generate_password_hash(password)

        new_user = User(username=username, email=email,
                        password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))



@app.route('/create_post', methods=['POST'])
def create_post():
    # username = request.form.get('username')
    # email = request.form.get('email')
    # age = request.form.get('age')
    # gender = request.form.get('gender')
    if request.method == 'POST':
        caption = request.form.get('caption')
        content = request.form.get('content')

        new_post = BlogPost(caption=caption, content=content)

        db.session.add(new_post)
        db.session.commit

        return redirect(url_for('home'))
    
    return render_template('create_post.html')


@app.route('/edit_post/<int:id>', methods=['GET', 'POST'])
def edit_post(id):
    post_to_edit = BlogPost.query.get_or_404(id)

    if request.method == 'POST':
        post_to_edit.caption = request.form.get('caption')
        post_to_edit.content = request.form.get('content')

        db.session.commit()
        return redirect(url_for('home'))

    context = {
        'blog_post': post_to_edit
    }

    return render_template('edit_post.html', **context)





if __name__ == '__main__':
    app.run(debug=True)


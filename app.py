from flask import Flask, render_template, request, url_for, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required
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
    firstname = db.Column(db.String(), nullable=False, unique=False)
    lastname = db.Column(db.String(), nullable=False, unique=False)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(60), nullable=False, unique=True)
    password_hash = db.Column(db.Text(), nullable=False)
    posts = db.relationship('BlogPost', backref='owner')

    def __repr__(self):
        return f"User <{self.username}>"


class BlogPost(db.Model):
    __tablename__ = 'blog_post'
    id = db.Column(db.Integer(), primary_key=True)
    caption = db.Column(db.String(), nullable=False)
    content = db.Column(db.String(), nullable=False)
    owner_id = db.Column(db.Integer(), db.ForeignKey(
        'users.id'), nullable=False)
    date_created = db.Column(db.DateTime(), default=datetime.utcnow)

    def __repr__(self):
        return f"BlogPost <{self.caption}, {self.content}, {self.date_created}, {self.owner_id}>"


@login_manager.user_loader
def user_loader(id):
    return User.query.get(int(id))


@app.route('/')
@app.route('/blogposts')
def home():
    posts = BlogPost.query.order_by(desc(BlogPost.date_created))

    return render_template('index.html', posts=posts)


@app.route('/login', methods=['GET', 'POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password_hash, password):
        login_user(user)
        flash("Login successful")
        return redirect(url_for('home'))
    elif user == None and password == None:
        flash('Enter your login credentials')
    else:
        flash("User credentials not correct!!")

    return render_template('login.html')


@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm')

        user = User.query.filter_by(username=username).first()
        email_exists = User.query.filter_by(email=email).first()

        password_hash = generate_password_hash(password)

        if user:
            flash("Username already used, try another username")
            return redirect(url_for('register'))

        elif email_exists:
            flash("Email already exists, try using another email")
            return redirect(url_for('register'))

        elif confirm != password:
            flash(
                "Confirm password is not correct, make sure the confirm password is the same with the password")
            return redirect(url_for('register'))

        new_user = User(firstname=firstname, lastname=lastname, username=username, email=email,
                        password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route('/create', methods=['GET', 'POST'])
@login_required
def create_post():
    if request.method == 'POST':
        caption = request.form.get('caption')
        content = request.form.get('content')

        owner = current_user.id
        new_post = BlogPost(caption=caption, content=content, owner_id=owner)

        db.session.add(new_post)
        db.session.commit()

        flash("Post Created successfully!!!")

        return redirect(url_for('home'))

    return render_template('create.html')


@app.route('/blogposts/post/edit_post/<int:id>/', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    post_to_edit = BlogPost.query.get_or_404(id)

    if request.method == 'POST':
        post_to_edit.caption = request.form.get('caption')
        post_to_edit.content = request.form.get('content')

        db.session.add(post_to_edit)
        db.session.commit()

        flash("Post Updated!")
        return redirect(url_for('view_post', id=id))

    if current_user.id == post_to_edit.owner_id:
        post_to_edit.caption = post_to_edit.caption
        post_to_edit.content = post_to_edit.content
        return render_template('edit_post.html', post=post_to_edit)

    else:
        flash("You do not have the previledge to edit this post")
        post = BlogPost.query.get_or_404(id)

        return render_template('post.html', post=post)


@app.route('/blogposts/post/<int:id>', methods=['GET', 'POST'])
def view_post(id):
    post = BlogPost.query.get_or_404(id)

    return render_template('post.html', post=post)


@app.route('/blogposts/post/delete/<int:id>/')
@login_required
def delete_post(id):
    post_to_delete = BlogPost.query.get_or_404(id)
    if current_user.id == post_to_delete.owner_id:
        db.session.delete(post_to_delete)
        db.session.commit()

        flash("Post deleted successfully")

        return redirect(url_for('home'))
    else:
        flash("You cannot delete this post!!!")
        post = BlogPost.query.get_or_404(id)

        return render_template('post.html', post=post)


@app.route('/contact')
def contact():

    return render_template('contact.html')


@app.route('/about')
def about():

    return render_template('about.html')


if __name__ == '__main__':
    app.run(debug=True)

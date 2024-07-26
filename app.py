from multiprocessing import synchronize
from flask import Flask, render_template, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy import exc
import psycopg2

app = Flask(__name__, template_folder='src/frontend/templates')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://<user>:<password>@localhost/<appname>'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/nutrinotes'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'

db = SQLAlchemy(app)

class User(db.Model):
    __tablename__ = 'Users'
    User_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.String(255), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    catalogs = db.relationship('Catalog', back_populates='user')
    goals = db.relationship('Goal', back_populates='user')

class Food(db.Model):
    __tablename__ = 'Food'
    Food_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(255), unique=True, nullable=False)
    Calories = db.Column(db.Integer, nullable=False)
    servings = db.relationship('Serving', back_populates='food')

class Catalog(db.Model):
    __tablename__ = 'Catalog'
    Catalog_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_ID = db.Column(db.Integer, db.ForeignKey('Users.User_ID'), nullable=False)
    user = db.relationship('User', back_populates='catalogs')
    servings = db.relationship('Serving', back_populates='catalog')

class Serving(db.Model):
    __tablename__ = 'Serving'
    Catalog_ID = db.Column(db.Integer, db.ForeignKey('Catalog.Catalog_ID'), primary_key=True, nullable=False)
    Food_ID = db.Column(db.Integer, db.ForeignKey('Food.Food_ID'), primary_key=True, nullable=False)
    Name = db.Column(db.String(255))
    catalog = db.relationship('Catalog', back_populates='servings')
    food = db.relationship('Food', back_populates='servings')

class Goal(db.Model):
    __tablename__ = 'Goals'
    Goal_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_ID = db.Column(db.Integer, db.ForeignKey('Users.User_ID'), nullable=False)
    Weight = db.Column(db.Float, nullable=False)
    Date_of_Goal = db.Column(db.Date, nullable=False)
    user = db.relationship('User', back_populates='goals')

if __name__ == '__main__':
    app.run()

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/user')
def user():
    return render_template('user.html')

#CRUD FOR USERS
#CREATE
@app.route("/createuser")
def userinfo(feedback_message=None, feedback_type=False):
    return render_template("createuser.html",
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route("/usercreate", methods=['POST'])
def usercreate():
    Username = request.form["Username"]
    Password = request.form["Password"]

    try:
        entry = User(Username=Username, Password=Password)
        db.session.add(entry)
        db.session.commit()
    except exc.IntegrityError as err:
        db.session.rollback()
        return userinfo(feedback_message='A username named {} already exists. Create a username with a different name.'.format(Username), feedback_type=False)
    except Exception as err:
        db.session.rollback()
        return userinfo(feedback_message='Database error: {}'.format(err), feedback_type=False)
    
    return userinfo(feedback_message='Successfully added user {}'.format(Username),
                       feedback_type=True)

#READ
@app.route("/readuser")
def readuser():
    query = select(User)
    result = db.session.execute(query)

    userList = []
    for user in result.scalars():
        userList.append((user.Username))
    
    return render_template("readuser.html", userlist=userList)

#UPDATE
def getusers():
    query = select(User)
    result = db.session.execute(query)

    userList = []
    for user in result.scalars():
        userList.append((user.Username, user.Password))
    return userList

@app.route("/updateuser")
def updateuser(feedback_message=None, feedback_type=False):
    userslist = [name for name, _, in getusers()]
    return render_template("updateuser.html", 
                           allusers=userslist, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/userupdate", methods=['POST'])
def userupdate():
    userForm = request.form.get('allusers')
    username = request.form["Username"]
    password = request.form["Password"]

    try:
        obj = db.session.query(User).filter(
            User.Username==userForm).first()
        
        if obj == None:
            msg = 'User {} not found.'.format(userForm)
            return updateuser(feedback_message=msg, feedback_type=False)

        if username != '':
            obj.Username = username
        if password != '':
            obj.Password = password 
        
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return updateuser(feedback_message=err, feedback_type=False)

    return updateuser(feedback_message='Successfully updated user {}'.format(userForm),
                       feedback_type=True)

#DELETE

@app.route("/deleteuser")
def deleteuser(feedback_message=None, feedback_type=False):
    userslist = [name for name, _, in getusers()]
    return render_template("deleteuser.html", 
                           allusers=userslist, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/userdelete", methods=['POST'])
def userdelete():
    userForm = request.form.get('allusers')

    try:
        obj = db.session.query(User).filter(
            User.Username==userForm).first()
        
        if obj == None:
            msg = 'User {} not found.'.format(userForm)
            return deleteuser(feedback_message=msg, feedback_type=False)
        
        db.session.delete(obj)
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return deleteuser(feedback_message=err, feedback_type=False)

    return deleteuser(feedback_message='Successfully deleted user {}'.format(userForm),
                       feedback_type=True)
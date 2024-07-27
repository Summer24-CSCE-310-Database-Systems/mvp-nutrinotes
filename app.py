from multiprocessing import synchronize
from flask import Flask, render_template, request, flash, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy import exc
from flask_login import LoginManager, login_user, login_required, logout_user, current_user #FOR LOGIN
from flask_login import UserMixin
import psycopg2

app = Flask(__name__, template_folder='src/frontend/templates')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://<user>:<password>@localhost/<appname>'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:password@localhost/nutrinotes'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = 'secret string'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

db = SQLAlchemy(app)

class User(db.Model, UserMixin):
    __tablename__ = 'Users'
    User_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Username = db.Column(db.String(255), unique=True, nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    catalogs = db.relationship('Catalog', back_populates='user')
    goals = db.relationship('Goal', back_populates='user')

    #return ID for login
    def get_id(self):
        return str(self.User_ID)

#Defines user id as attribute tracked
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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

#AUTHENTICATION VIA LOGIN FLASK #############################################

#IMPORTANT! Current_User is set as global by flask login and can thus be used in any html!!!!

@app.route('/')
def start():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login_action'))

@app.route('/login', methods=['GET', 'POST'])
def login_action():

    #If user is logged in redirect to home
    #if current_user.is_authenticated:
        #return redirect(url_for('home'))
    
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(Username=username).first()
        #If the user exists and the password for that user matches
        if user and user.Password == password:
            #User has been authenticated and is logged in
            login_user(user)
            #redirect to home
            return redirect(url_for('home'))
        else:
            #failed login
            flash('Invalid Login')
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout_action():
    logout_user()
    return redirect(url_for('login_action'))

#####################################################

# @app.route('/SignUp', methods=['GET', 'POST'])
# def SignUp():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = User.query.filter_by(Username=username).first()
#         #If the user exists and the password for that user matches
#         if user:
#             flash('Invalid Username!')
#             #User has been authenticated and is logged in
#             return render_template('signup.html')
#         elif password != "" and user != "":
#             #User successfully signed up
#             login_user(user)
#             #redirect to home
#             return redirect(url_for('home'))
        
#     return render_template('signup.html')
@app.route('/SignUp')
def SignUp():
    return render_template('SignUp.html')

@app.route("/SignUpNewUser")
def SignUpInfo(feedback_message=None, feedback_type=False):
    return render_template("SignUp.html",
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route('/SignUpAction', methods = ['POST'])
def SignUpAction():
    username = request.form["Username"]
    password = request.form["Password"]

    try:
        entry = User(Username=username, Password=password)
        db.session.add(entry)
        db.session.commit()
        user = User.query.filter_by(Username=username).first()
        login_user(user)
        flash('Successfully added user {}'.format(username), 'success')
        return redirect(url_for('home'))  # Redirect to the form page after successful sign-up
    except exc.IntegrityError as err:
        db.session.rollback()
        #flash('A username named {} already exists. Create a username with a different name.'.format(username), 'error')
        return SignUpInfo(feedback_message='A username named {} already exists. Create a username with a different name.'.format(username), feedback_type=False)
        #return redirect(url_for('SignUp'))  # Redirect to the form page with error message
    except Exception as err:
        db.session.rollback()
        #flash('Database error: {}'.format(err), 'error')
        return SignUpInfo(feedback_message='Database error: {}'.format(err), feedback_type=False)
        #return redirect(url_for('SignUp'))
    
#AUTHENTICATION VIA LOGIN FLASK #############################################




@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/user')
def user():
    return render_template('user.html')


def getusers():
    query = select(User)
    result = db.session.execute(query)

    userList = []
    for user in result.scalars():
        userList.append((user.Username, user.Password))
    return userList

def getfoods():
    query = select(Food)
    result = db.session.execute(query)

    foodList = []
    for food in result.scalars():
        foodList.append((food.Name, food.Calories))
    return foodList

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

#CRUD FOR FOOD

#CREATE
@app.route("/food")
def foodinfo(feedback_message=None, feedback_type=False):
    foodList = [name for name, _, in getfoods()]
    return render_template("food.html",
            allFoods=foodList,
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route("/foodcreate", methods=['POST'])
def foodcreate():
    Name = request.form["Name"]
    Calories = request.form["Calories"]

    try:
        entry = Food(Name=Name, Calories=Calories)
        db.session.add(entry)
        db.session.commit()
    except exc.IntegrityError as err:
        db.session.rollback()
        return foodinfo(feedback_message='A food named {} already exists. Create a food with a different name.'.format(Name), feedback_type=False)
    except Exception as err:
        db.session.rollback()
        return foodinfo(feedback_message='Database error: {}'.format(err), feedback_type=False)
    
    return foodinfo(feedback_message='Successfully added food {}'.format(Name),
                       feedback_type=True)
#DELETE
@app.route("/fooddelete", methods=['POST'])
def fooddelete():
    foodForm = request.form.get('allFoods')

    try:
        obj = db.session.query(Food).filter(
            Food.Name==foodForm).first()
        
        if obj == None:
            msg = 'Food {} not found.'.format(foodForm)
            return foodinfo(feedback_message=msg, feedback_type=False)
        
        db.session.delete(obj)
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return foodinfo(feedback_message=err, feedback_type=False)

    return foodinfo(feedback_message='Successfully deleted food {}'.format(foodForm),
                       feedback_type=True)

#READ
@app.route("/foodlist")
def readfood():
    query = select(Food)
    result = db.session.execute(query)

    foodList = []
    for food in result.scalars():
        foodList.append((food.Name, food.Calories))
    
    return render_template("foodlist.html", foodList=foodList)

# Catelog

def getCatelogs():
    query = select(Catalog)
    result = db.session.execute(query)

    catList = []
    for catelog in result.scalars():
        catList.append((catelog.Catelog_ID, catelog.User_ID))
    return catList

#UPDATE
@app.route("/updatefood")
def updatefood(feedback_message=None, feedback_type=False):
    foodslist = [name for name, _, in getfoods()]
    return render_template("updatefood.html", 
                           allfoods=foodslist, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

@app.route("/foodupdate", methods=['POST'])
def foodupdate():
    foodForm = request.form.get('allfoods')
    name = request.form["Name"]
    calories = request.form["Calories"]

    try:
        obj = db.session.query(Food).filter(
            Food.Name==foodForm).first()
        
        if obj == None:
            msg = 'Food {} not found.'.format(foodForm)
            return updatefood(feedback_message=msg, feedback_type=False)

        if name != '':
            obj.Name = name
        if calories != '':
            obj.Calories = calories 
        
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return updatefood(feedback_message=err, feedback_type=False)

    return updatefood(feedback_message='Successfully updated food {}'.format(foodForm),
                       feedback_type=True)

# Crud for Catelog
# Create
@app.route("/catelog")
def cateloginfo(feedback_message=None, feedback_type=False):

    # getCatelogs()

    return render_template("catelog.html",
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route("/catelogcreate", methods=['POST'])
def catelogcreate():
    Name = request.form["Name"]
    
    return cateloginfo(feedback_message='Need Catelog_ID and User_ID code finished first {}'.format(Name),
                       feedback_type=True)



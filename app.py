from multiprocessing import synchronize
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import select
from sqlalchemy import exc
from sqlalchemy.sql import func
from flask_login import LoginManager, login_user, login_required, logout_user, current_user #FOR LOGIN
from flask_login import UserMixin
import psycopg2
from datetime import datetime

app = Flask(__name__, template_folder='src/frontend/templates')
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://<user>:<password>@localhost/<appname>'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Little12@localhost/nutrinotes'
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
    friends = db.relationship('Friend', back_populates='user')

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
    servings = db.relationship('Serving', back_populates='food', cascade = 'all, delete-orphan')

class Catalog(db.Model):
    __tablename__ = 'Catalog'
    Catalog_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_ID = db.Column(db.Integer, db.ForeignKey('Users.User_ID'), nullable=False)
    Name = db.Column(db.String(255), nullable=False)
    user = db.relationship('User', back_populates='catalogs')
    servings = db.relationship('Serving', back_populates='catalog', cascade = 'all, delete-orphan')

class Serving(db.Model):
    __tablename__ = 'Serving'
    Catalog_ID = db.Column(db.Integer, db.ForeignKey('Catalog.Catalog_ID', ondelete = 'CASCADE'), primary_key=True, nullable=False)
    Food_ID = db.Column(db.Integer, db.ForeignKey('Food.Food_ID', ondelete = 'CASCADE'), primary_key=True, nullable=False)
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

class Friend(db.Model):
    __tablename__ = 'Friends'
    Friend_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    User_ID = db.Column(db.Integer, db.ForeignKey('Users.User_ID'), nullable=False)
    Name = db.Column(db.String(255))
    Date_of_Friendship = db.Column(db.Date, nullable=False)
    user = db.relationship('User', back_populates='friends')

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

def getFriends():
    query = select(Friend)
    result = db.session.execute(query)

    fList = []
    for f in result.scalars():
        fList.append((f.Name, f.Date_of_Friendship))
    return fList

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

# Crud for Catalog##################################################################
# Create
@app.route("/catalog_home")
def cataloginfo(feedback_message=None, feedback_type=False):

    return render_template("catalog_home.html",
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

#CREATE CATALOG
@app.route("/createcatalog")
def createcataloginfo(feedback_message=None, feedback_type=False):
    return render_template("createcatalog.html",
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route("/catalogcreate", methods=['POST'])
def catalogcreate():
    name = request.form["Name"]

    try:
        entry = Catalog(Name=name, User_ID = current_user.User_ID)
        db.session.add(entry)
        db.session.commit()
    except exc.IntegrityError as err:
        db.session.rollback()
        return createcataloginfo(feedback_message='A catalog named {} already exists. Create a catalaog with a different name.'.format(name), feedback_type=False)
    except Exception as err:
        db.session.rollback()
        return createcataloginfo(feedback_message='Database error: {}'.format(err), feedback_type=False)
    
    return createcataloginfo(feedback_message='Successfully added catalog {}'.format(name),
                       feedback_type=True)

#VIEW CATALOG
@app.route('/selectcatalogview')
def selectcatalogview():
    session.pop('current_catalog_ID', None)
    catalogs = Catalog.query.filter_by(User_ID = current_user.User_ID).all()
    for catalog in catalogs:
        print(f"Catalog ID: {catalog.Catalog_ID}, Name: {catalog.Name}")
    return render_template('catalogviewselect.html', catalogs=catalogs)

@app.route('/storeviewcatalog', methods = ['POST'])
def storeviewcatalog():
    catalog_ID = request.form['catalog_id']
    session['current_catalog_ID'] = catalog_ID
    return redirect(url_for('viewcatalogselect'))

@app.route('/viewcatalogselect', methods = ['GET','POST'])
def viewcatalogselect():
    catalog_ID = session.get('current_catalog_ID')
    foodlist = db.session.query(Food).join(Serving).filter(Serving.Catalog_ID == catalog_ID).all()
    return render_template('catalogshow.html', foods=foodlist)




#DELETE CATALOG
@app.route('/catalogdelete', methods = ['POST'])
def catalogdelete():
    catalog_ID = request.form.get('catalog_id')
    catalog = db.session.query(Catalog).filter_by(Catalog_ID = catalog_ID).first()
    if catalog:
        db.session.delete(catalog)
        db.session.commit()
        return redirect(url_for('catalogdeleteinit'))
    else:
        return "No record of this food in DB"

@app.route('/catalogdeleteinit', methods = ['GET', 'POST'])
def catalogdeleteinit():
    catalogs = Catalog.query.filter_by(User_ID = current_user.User_ID).all()
    return render_template('catalogdelete.html', catalogs=catalogs)


#UPDATE CATALOG

#selecting a catalog to update 
@app.route('/catalogselect')
def catalogselect():
    session.pop('current_catalog_ID', None)
    catalogs = Catalog.query.filter_by(User_ID = current_user.User_ID).all()
    return render_template('updatecatalogselect.html', catalogs=catalogs)


@app.route('/storecatalog', methods = ['POST'])
def storecatalog():
    catalog_ID = request.form['catalog_id']
    session['current_catalog_ID'] = catalog_ID
    return redirect(url_for('selectcatalog'))

#used to FINALLY app/remove to selected catalog
@app.route('/selectcatalog', methods = ['GET','POST'])
def selectcatalog():
    #for adding
    catalog_ID = session.get('current_catalog_ID')
    foodlist = Food.query.all()

    #for removing
    catalogfoodquery = db.session.query(Food).join(Serving).filter(Serving.Catalog_ID == catalog_ID)
    catalogfood = catalogfoodquery

    #removing those foods already in catalog from adding list
    catalogfoodID = {food.Food_ID for food in catalogfood}
    validfoods = [food for food in foodlist if food.Food_ID not in catalogfoodID]

    print("All Foods:", [food.Name for food in foodlist]) 
    return render_template('updatecatalogfin.html', allFoods = validfoods, catalogFood = catalogfood)

#Adding food to a catalog
@app.route('/addfoodcatalog', methods = ['POST'])
def addfoodcatalog():
    catalog_ID = session.get('current_catalog_ID')
    food_ID = request.form.get('addedfood')
    serving = Serving(Food_ID = food_ID, Catalog_ID = catalog_ID)
    db.session.add(serving)
    db.session.commit()
    return redirect(url_for('selectcatalog'))

#Removing food from a catalog
@app.route('/removefoodcatalog', methods = ['POST'])
def removefoodcatalog():
    catalog_ID = session.get('current_catalog_ID')
    food_ID = request.form.get('removedfood')
    serving = db.session.query(Serving).filter_by(Food_ID=food_ID, Catalog_ID=catalog_ID).first()
    if serving:
        db.session.delete(serving)
        db.session.commit()
        return redirect(url_for('selectcatalog'))
    else:
        return "No record of this food in DB"

# Friend
# Create
@app.route("/friends")
def friendsinfo(feedback_message=None, feedback_type=False):

    friendsList = readfriends()

    return render_template("friends.html", friendsList=friendsList, 
            feedback_message=feedback_message, 
            feedback_type=feedback_type)

@app.route("/friendscreate", methods=['POST'])
def friendscreate():
    Name = request.form["Name"]
    # Calories = request.form["Calories"]

    try:
        entry = Friend(User_ID=current_user.User_ID, Name=Name, Date_of_Friendship=func.now())
        db.session.add(entry)
        db.session.commit()
    except exc.IntegrityError as err:
        db.session.rollback()
        return friendsinfo(feedback_message='Friend id already exists?', feedback_type=False)
    except Exception as err:
        db.session.rollback()
        return friendsinfo(feedback_message='Database error: {}'.format(err), feedback_type=False)
    
    return friendsinfo(feedback_message='Successfully added friend {}'.format(Name),
                       feedback_type=True)

#READ
def readfriends():
    query = select(Friend).where(Friend.User_ID == current_user.User_ID)
    result = db.session.execute(query)

    friendslist = []
    for friend in result.scalars():
        friendslist.append((friend.Name, friend.Date_of_Friendship))
    
    return friendslist



@app.route('/friends_action', methods=['POST'])
def friends_action():

    # selected_friend = request.form['friend']
    action = request.form['f_action']

    friendsForm = request.form.get('friendsList')

    if action == 'delete':
        # Logic to delete the friend
        # For example, remove the friend from the list or database
        return friendsdelete()
    
    elif action == 'update':
        # Logic to update the friend
        # For example, redirect to an update page with the friend's details
        return redirect(url_for('updatefriend', friendName=friendsForm))
    
    return "Unknown action", 400




# Update
@app.route("/friendupdate", methods=['POST', 'Get'])
def friendupdate():
    oldfriendsName = request.form.get('friendName')
    friendsName = request.form.get('Name')
    friendsDate = request.form.get('Date_of_Friendship')

    final_name = oldfriendsName

    try:
        obj = db.session.query(Friend).filter(Friend.Name==oldfriendsName).first()

        if obj == None:
            msg = 'Friend {} not found.'.format(oldfriendsName)
            return friendsinfo(feedback_message=msg, feedback_type=False)

        if friendsName != '':
            obj.Name = friendsName
            final_name = friendsName
        if friendsDate != '':
            if is_valid_date(friendsDate):
                obj.Date_of_Friendship = friendsDate 
        
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return friendsinfo(feedback_message=err, feedback_type=False)

    return friendsinfo(feedback_message=f'Successfully updated friend!\n{oldfriendsName} ----> {final_name}    {friendsDate}',
                       feedback_type=True)

@app.route("/updatefriend")
def updatefriend(feedback_message=None, feedback_type=False):
    friendName = request.args.get('friendName')
    return render_template("updatefriend.html", 
                           friendName=friendName, 
                           feedback_message=feedback_message, 
                           feedback_type=feedback_type)

#DELETE
@app.route("/friendsdelete", methods=['POST'])
def friendsdelete():
    friendsForm = request.form.get('friendsList')

    try:
        obj = db.session.query(Friend).filter(Friend.Name == friendsForm).first()
        
        if obj == None:
            msg = 'Friend {} not found.'.format(friendsForm)
            return friendsinfo(feedback_message=msg, feedback_type=False)
        
        db.session.delete(obj)
        db.session.commit()
    except Exception as err:
        db.session.rollback()
        return friendsinfo(feedback_message=err, feedback_type=False)

    return friendsinfo(feedback_message='Successfully deleted friend: {}'.format(friendsForm),
                       feedback_type=True)

def is_valid_date(date_str, date_format='%Y-%m-%d'):
    try:
        datetime.strptime(date_str, date_format)
        return True
    except ValueError:
        return False


#CRUD FOR Goals
@app.route("/goals")
def goals():
    try:
        user = db.session.query(User).filter(User.Username == current_user.Username).first()
        if user is None:
            return render_template('goals.html', feedback_message='User not found', feedback_type=False)
        goals = db.session.query(Goal).filter(Goal.User_ID == user.User_ID).all()
        return render_template('goals.html', goals=goals)

    except Exception as err:
        return render_template('goals.html', feedback_message=str(err), feedback_type=False)

#CREATE
@app.route("/creategoal", methods=['POST'])
def creategoal():
    Username = request.form['username']
    Weight = request.form.get("Weight")
    Date_of_Goal = request.form.get("Date_of_Goal")

    if not Username or not Weight or not Date_of_Goal:
        send = "Please Enter All Information!"
        return render_template('goals.html', feedback_message=send, feedback_type=False)
    try:
        user = db.session.query(User).filter(User.Username == Username).first()
        if user is None:
            send = 'USER ID NOT FOUND ({})'.format(Username)
            return render_template('goals.html', feedback_message=send, feedback_type=False)
        
        newGoal = Goal(
            User_ID=user.User_ID,
            Weight=float(Weight),
            Date_of_Goal=Date_of_Goal
        )

        db.session.add(newGoal)
        db.session.commit()

        send = 'Goal Added successfully!'
        return render_template('goals.html', feedback_message=send, feedback_type=True)
    except Exception as err:
        db.session.rollback()
        return render_template('goals.html', feedback_message=str(err), feedback_type=False)

#DELETE
@app.route("/deletegoal/<int:goal_id>", methods=['POST'])
def deletegoal(goal_id):
    try:
        # Query the goal using the provided goal_id
        goal = db.session.query(Goal).filter(Goal.Goal_ID == goal_id).first()
        
        if goal is None:
            send = 'Goal ID NOT FOUND ({})'.format(goal_id)
            return render_template('goals.html', feedback_message=send, feedback_type=False)
        
        # Delete the goal
        db.session.delete(goal)
        db.session.commit()

        send = 'Goal Deleted successfully!'
        return redirect(url_for('goals', feedback_message=send, feedback_type=True))
    except Exception as err:
        db.session.rollback()
        return render_template('goals.html', feedback_message=str(err), feedback_type=False)
#UPDATE
@app.route("/updategoal/<int:goal_id>", methods=['GET', 'POST'])
def updategoal(goal_id):
    try:
        # Fetch the goal to update
        goal = db.session.query(Goal).filter(Goal.Goal_ID == goal_id).first()
        
        if goal is None:
            send = 'Goal ID NOT FOUND ({})'.format(goal_id)
            return render_template('goals.html', feedback_message=send, feedback_type=False)
        
        if request.method == 'POST':
            # Get updated data from the form
            Weight = request.form.get("Weight")
            Date_of_Goal = request.form.get("Date_of_Goal")
            
            if not Weight or not Date_of_Goal:
                send = "Please Enter All Information!"
                return render_template('updategoal.html', goal=goal, feedback_message=send, feedback_type=False)
            
            # Update goal
            goal.Weight = float(Weight)
            goal.Date_of_Goal = Date_of_Goal
            
            db.session.commit()
            
            send = 'Goal Updated successfully!'
            return redirect(url_for('goals', feedback_message=send, feedback_type=True))
        
        return render_template('updategoal.html', goal=goal)
    
    except Exception as err:
        db.session.rollback()
        return render_template('goals.html', feedback_message=str(err), feedback_type=False)

#VIEW FRIENDS GOALS
#@app.route('/friendsgoals', methods=['GET'])
#def friendgoals():
#    try:
##        current_user = db.session.query(User).filter(User.Username == current_user.Username).first()
#        if current_user is None:
#            return render_template('goals.html', feedback_message='User not found', feedback_type=False)
#        friends = db.session.query(Friend).filter(Friend.User_ID == current_user.User_ID).all()
#        friend_ids = [friend.Friend_ID for friend in friends]
#        
#        if not friend_ids:
#            return render_template('goals.html', feedback_message='No friends found', feedback_type=False)
#      
#        goals = db.session.query(Goal).filter(Goal.User_ID.in_(friend_ids)).all()
#        
#        friends_list = db.session.query(User).filter(User.User_ID.in_(friend_ids)).all()
#        
#        return render_template('goals.html', goals=goals, friends=friends_list, current_user=current_user)
#
#    except Exception as err:
#        return render_template('goals.html', feedback_message=str(err), feedback_type=False)
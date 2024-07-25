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
    Username = db.Column(db.String(255), nullable=False)
    Password = db.Column(db.String(255), nullable=False)
    catalogs = db.relationship('Catalog', back_populates='user')
    goals = db.relationship('Goal', back_populates='user')

class Food(db.Model):
    __tablename__ = 'Food'
    Food_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    Name = db.Column(db.String(255), nullable=False)
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


from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(256), unique=False, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    tos = db.Column(db.Boolean(), unique=False, nullable=False)
    is_active = db.Column(db.Boolean(), unique=False, nullable=False)
    diary = db.relationship('Day', backref = 'user')
    # Diary (relationship 1 to n -> Food)


    def repr(self):
        return '<User %r>' % self.username

    def serialize(self):
        return {
            "id": self.id,
            "email": self.email,
            "first_name": self.firstname,
            "last_name": self.lastname,
            "diary": [d.serialize() for d in self.diary]
            # do not serialize the password, its a security breach
        }

    def validate(self,password):
        if not check_password_hash(self.password, password):
            return False

        return True

class Day(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(100), nullable=False)
    foods = db.relationship('Food', backref = 'day')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def repr(self):
        return '<Journal Entry for %r>' % self.date

    def serialize(self):
        return {
            "id": self.id,
            "date": self.date,
            "foods": [f.serialize() for f in self.foods]
        }

class Food(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    calories = db.Column(db.String(15), unique=False, nullable=False)
    serving_unit = db.Column(db.String(50), unique=False, nullable=False)
    serving_size = db.Column(db.String(120), unique=False, nullable=False)
    quantity = db.Column(db.String(10), unique=False, nullable=False)
    day_id = db.Column(db.Integer, db.ForeignKey('day.id'))
    time_of_day = db.Column(db.Enum('morning','afternoon','night'), nullable=False, server_default='morning')

    def repr(self):
        return '<Food Item %r>' % self.name

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "calories": self.calories,
            "serving_size": self.serving_size,
            "quantity": self.quantity,
            "time_of_day": self.time_of_day,
            "day_id": self.day_id
        }

# Date (datetime stamp)
# Time of day (ENUM morning | afternoon | evening)

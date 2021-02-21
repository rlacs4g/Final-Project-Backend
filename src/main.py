"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Day, Food
#from models import Person
from flask_jwt_extended import create_access_token
from flask_jwt_extended import get_jwt_identity
from flask_jwt_extended import jwt_required
from flask_jwt_extended import JWTManager
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)

@app.route('/register', methods=['POST'])
def register():
    email = request.json.get("email", None)
    password = request.json.get("password", None)
    fname = request.json.get("fname", None)
    lname = request.json.get("lname", None)
    tos = request.json.get("tos", None) 



    if not email:
        return jsonify({"msg": "Email is required"}), 400
    if not password:
        return jsonify({"msg": "Password is required"}), 400
    if not fname:
        return jsonify({"msg": "First name is required"}), 400
    if not lname:
        return jsonify({"msg": "Last name is required"}), 400
    if not tos:
        return jsonify({"msg": "tos is required"}), 400

    user = User.query.filter_by(email=email).first()
    if user is not None:
        return jsonify({"msg": "Email address already exists"}), 400

    user = User(email=email, password=generate_password_hash(password), firstname=fname, lastname=lname, tos=tos, is_active=True)
    db.session.add(user)
    db.session.commit()

    return jsonify({"msg": "User successfully registered"}),200

# Provide a method to create access tokens. The create_jwt()
# function is used to actually generate the token
@app.route('/login', methods=['POST'])
def login():
    # make sure request is a json
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    # get email and password from request
    email = request.json.get('email', None)
    password = request.json.get('password', None)

    # if params are empty, return a 400
    if not email:
        return jsonify({"msg": "Missing email parameter"}), 400
    if not password:
        return jsonify({"msg": "Missing password parameter"}), 400

    # try to find user
    try:
        # query user
        user = User.query.filter_by(email=email).first()
        # test validate method. 
        if user.validate(password):
            # if user is validated (password is correct), return the token
            expires = datetime.timedelta(days=7)
            response_msg = {
                "user": user.serialize(),
                'token': create_access_token(identity=email,expires_delta=expires),
                # 'token': create_access_token(identity=email),
                "expires_at": expires.total_seconds()*1000 
            }
            status_code = 200
        else:
            # otherwise, raise an exception so that they check their email and password
            raise Exception('Failed to login. Check your email and password.')
    # catch the specific exception and store in var
    except Exception as e:
        # format a json respons with the exception
        response_msg = {
            'msg': str(e),
            'status': 401
        }
        status_code = 401
    
    # general return in json with status
    return jsonify(response_msg), status_code

@app.route('/diary', methods=['POST'])
def createDiaryEntry():

    # make sure request is a json
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    
    foods = request.json.get("foods", None)
    date = request.json.get("date", None)
    user_id = request.json.get("user_id", None)

    if not foods:
        return jsonify({"msg": "Array of Foods is required"}), 400
    if not date:
        return jsonify({"msg": "Date is required"}), 400
    if not user_id:
        return jsonify({"msg": "User ID is required"}), 400

    user = User.query.filter_by(id=user_id).first()
    if not user:
        return jsonify({"msg": "Invalid User ID"}), 400 
    
    day = Day.query.filter_by(date=date).first()
    if day is not None:
        return jsonify({"msg": "Day already exists. Please update existing day instead of creating again."}), 400 
    
    try:
        day = Day(date=date,user_id=user_id)
        db.session.add(day)
        db.session.commit()
    except:
        db.session.rollback()
        return jsonify({"msg": "Failed to create day in journal"}), 400 

    try:
        for item in foods:
            name = item.get("name", None)
            calories = item.get("calories", None)
            serving_size = item.get("serving_size", None)
            serving_unit = item.get("serving_unit", None)
            quantity = item.get("quantity", None)
            time_of_day = item.get("time_of_day", None)
            if not name:
                return jsonify({"msg": "name is required"}), 400
            if not quantity:
                return jsonify({"msg": "quantity is required"}), 400
            if not serving_size:
                return jsonify({"msg": "serving size is required"}), 400
            if not serving_unit:
                return jsonify({"msg": "serving unit is required"}), 400
            if not calories:
                return jsonify({"msg": "calories is required"}), 400
            if not time_of_day:
                return jsonify({"msg": "time of day is required"}), 400     
            
            try:
                food = Food(name=name, calories=calories, serving_size=serving_size, serving_unit=serving_unit, quantity=quantity, time_of_day=time_of_day, day_id=day.id)
                print(food)
                print(day.id)
                db.session.add(food)
                db.session.commit()
            except:
                db.session.rollback()  
                return jsonify({"msg": "Failed to create food and associate to day"}), 400       
        

    except:
        pass  


    return jsonify({"msg": "Journal entry was recorded", "journal": day.serialize()}), 200

@app.route('/diary/food', methods=['POST'])
def createNewFood():
    # make sure request is a json
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400
        
    name = request.json.get("name", None)
    calories = request.json.get("calories", None)
    serving_size = request.json.get("serving_size", None)
    serving_unit = request.json.get("serving_unit", None)
    quantity = request.json.get("quantity", None)
    time_of_day = request.json.get("time_of_day", None)    
    day_id = request.json.get("day_id", None)    

    if not name:
        return jsonify({"msg": "name is required"}), 400
    if not quantity:
        return jsonify({"msg": "quantity is required"}), 400
    if not serving_size:
        return jsonify({"msg": "serving size is required"}), 400
    if not serving_unit:
        return jsonify({"msg": "serving unit is required"}), 400
    if not calories:
        return jsonify({"msg": "calories is required"}), 400
    if not time_of_day:
        return jsonify({"msg": "time of day is required"}), 400    
    if not day_id:
        return jsonify({"msg": "time of day is required"}), 400    
    print(day_id)
# json must have the food details and the id for the day that we are updating
    food_entry = Day.query.filter_by(id = day_id).first()

    if food_entry is None:
        return jsonify({"msg": "The requested day does not exist. "}), 400


    try:
        food = Food(name=name, calories=calories, serving_size=serving_size, serving_unit=serving_unit, quantity=quantity, time_of_day=time_of_day, day_id=day_id)
        db.session.add(food)
        db.session.commit()
    except:
        db.session.rollback()  
        return jsonify({"msg": "Failed to create food and associate to day"}), 400     

    return jsonify({"msg": "Success", "food": food.serialize()}), 400   

@app.route('/diary/food/<int:food_id>', methods=['DELETE','PUT'])
def handleFoodDelete(food_id):
    if not food_id:
        return jsonify({"msg": "food_id is required"}), 400

    food = Food.query.filter_by(id = food_id).first()
    if food is None:
        return jsonify({"msg": "ID not found. The requested food does not exist. "}), 400

    if request.method =="PUT":
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400
        
        name = request.json.get("name", None)
        calories = request.json.get("calories", None)
        serving_size = request.json.get("serving_size", None)
        serving_unit = request.json.get("serving_unit", None)
        quantity = request.json.get("quantity", None)
        time_of_day = request.json.get("time_of_day", None)

        if not name:
            return jsonify({"msg": "name is required"}), 400
        if not quantity:
            return jsonify({"msg": "quantity is required"}), 400
        if not serving_size:
            return jsonify({"msg": "serving size is required"}), 400
        if not serving_unit:
            return jsonify({"msg": "serving unit is required"}), 400
        if not calories:
            return jsonify({"msg": "calories is required"}), 400
        if not time_of_day:
            return jsonify({"msg": "time of day is required"}), 400   

        times = ["morning","afternoon","evening"]
        if not time_of_day in times:
            return jsonify({"msg": "Time_of_day must be 'morning', 'afternoon', or 'night'."}), 400 

        try:
            # handle updating qty or other info on an existing food
            food.name = name
            food.calories = calories
            food.serving_size = serving_size
            food.serving_unit = serving_unit
            food.quantity = quantity
            food.time_of_day = time_of_day

            db.session.commit()
        except Exception as e:
            return jsonify({"msg": str(e)})
        
        return jsonify({
            "msg": "Food successfully updated",
            "food": food.serialize()
        }), 200


    if request.method =="DELETE":
        # handle deleting/removing food item from the day
        try:
            db.session.delete(food)
            db.session.commit()

        except Exception as e:
            return jsonify({"msg": str(e)})

            
        return jsonify({"msg": "Success!"}), 200

@app.route('/diary/food/all', methods=['GET'])
def getAllFoods():
    food = Food.query.all()
    return jsonify({"foods": list(map(lambda x: x.serialize(),food))}), 200

@app.route('/diary/<int:day_id>', methods=['GET'])
def getDay(day_id):
    day = Day.query.filter_by(id=day_id).first()
    return jsonify({"day": day.serialize()}), 200

# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)

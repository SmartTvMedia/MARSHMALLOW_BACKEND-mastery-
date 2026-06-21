from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
import uuid
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from marshmallow import Schema, fields, validate, ValidationError



app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

solo = lambda: str(uuid.uuid4())


# ASSOCIATION TABLE


product_category = db.Table(
    'product_category',
    db.Column('product_id', db.String(300),db.ForeignKey('products.id'),primary_key=True),
    
    db.Column('category_id',db.String(100), db.ForeignKey('categories.id'),primary_key=True)
)

# user model
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.String(100), primary_key=True,default=solo)
    name = db.Column(db.String(36), nullable=True)
    email = db.Column(db.String(36),nullable=True)
    password = db.Column(db.String(36), nullable=True)
    age = db.Column(db.String(30), nullable=True)
    username = db.Column(db.String(36), nullable = True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)



# PRODUCT MODEL

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.String(30), primary_key =True, default =solo)
    
    name = db.Column(db.String(36))
    
    qty = db.Column(db.Integer,nullable=False)
    
    price = db.Column(db.Integer, nullable=False)
    
    description = db.Column(db.String(300), nullable=False)
    
    created_at = db.Column(db.DateTime, default = datetime.utcnow)
    
    categories = db.relationship('Category', secondary =product_category, backref='products' ,lazy=True)

# CATEGORY MODEL

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.String(100),primary_key=True, default=lambda:str(uuid.uuid4()))
    title = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
 
 
# SCHEMA FOR PRODUCT MODEL  
   
class Product_Schema(SQLAlchemyAutoSchema):
    class Meta:
        model = Product 
        load_instance = True
        sqla_session = db.session
        
    id = fields.Str(dump_only = True)
    name =fields.Str(required=True,validate=validate.Length(min=3, max=100))
    qty = fields.Int(required=True , validate = validate.Range(min=1))
    price = fields.Float(required=True )
    description = fields.Str(required=True, validate = validate.Length(min=10,max=50))
    
 
product_schema = Product_Schema()
products_schema = Product_Schema(many=True)  



# SCHEMA FOR USER VALIDATION

class User_Schema(SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        sqla_session = db.session
    id = fields.Str(required=False )
    name = fields.Str(required=True, validate=validate.Length(min=5,max=20))
    email = fields.Email(required=True)
    password = fields.Str(required=True, validate=validate.Length(min=5))
    age = fields.Int(required=True, validate=validate.Range(min=18))
    username = fields.Str(required=True, validate=validate.Length(min=5,max=20))
    role = fields.Str(required=True, validate=validate.OneOf(
        [
        "admin",
        "user"
        ]
        ))
user_schema=User_Schema()
users_schema = User_Schema(many=True)


# HOME

@app.route('/')
def home():
    return jsonify({
        'message':'welcome to products api'
    })


 # CREATE USERS
 
@app.route('/user',methods=['POST'])
def create_user  ():
    try:
        user =user_schema.load(request.json)
        db.session.add(user)
        db.session.commit()     
        return jsonify(user_schema.dump(user))
    except  ValidationError as err:
        
        return jsonify(err.messages),400
        
#CREATING THE PRODUCT ROUTE

@app.route('/products',methods=['POST'])
def product_create():
    
    try:
        product = product_schema.load(request.json)
        
        db.session.add(product)
        db.session.commit()
        
        return jsonify(product_schema.dump(product)),200
    except ValidationError as err:
        
        return jsonify(err.messages),400
    
    
#get all users    
@app.route('/users',methods=['GET'])
def get_users():
    users=User.query.all()
    
    return jsonify(users_schema.dump(users))
    
#get one user
@app.route('/user/<string:user_id>',methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'message':'innvalid request'}),400
    return jsonify(user_schema.dump(user))


#update user

@app.route('/user/<string:user_id>',methods=['PUT'])
def update_user(user_id):
    user =User.query.get(user_id)
    if not user:
        return jsonify({'message':'invalid user'})
    try:
        update=user_schema.load(request.json,
        instance = user)
        
        db.session.commit()
        
        return jsonify(user_schema.dump(update))
    except ValidationError as err:
        return jsonify(err.messages),400
    
    
@app.route('/user/<string:user_id>',methods=['DELETE'])
def delete_user(user_id):
    user=User.query.get(user_id)
    if not user:
        return jsonify({'message':'user not found'}),400
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message':"user deleted"})
    
    
        
if __name__ == '__main__':

    with app.app_context():
        db.create_all()
        print('database created sucessfully')

    app.run(debug=True) 
    
   
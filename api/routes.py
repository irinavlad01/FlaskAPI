from api import app, db
from flask import request, jsonify, make_response
from api.models import Utilizatori, Produse, Cos, DetaliiCos
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime
from functools import wraps
import jwt

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        #args = positional argument; kwargs = keyword arguments 
        token = None 

        if 'x-access-token' in request.headers:
            token = request.headers['x-access-token']
        
        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401
        
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms = ['HS256'])
            current_user = Utilizatori.query.filter_by(id=data['id']).first()
        except:
            return jsonify({'message' : 'Token is invalid or you must log in!'}), 401
    
        return f(current_user, *args, **kwargs)
    
    return decorated


#!!! RUTE UTILIZATORI !!!#
@app.route('/users', methods = ['GET'])
@token_required
def get_all_users(current_user):

    if not current_user.admin:
        return jsonify({'message' : 'Must be an admin to perform that function'})
    
    users = Utilizatori.query.all()

    output = []

    for user in users:
        user_data = {} #creaza un dictionar python. Cheie si valori
        user_data['id'] = user.id
        user_data['nume'] = user.nume
        user_data['prenume'] = user.prenume
        user_data['email'] = user.email
        user_data['parola'] = user.parola
        user_data['adresa_domiciliu'] = user.adresa_domiciliu
        user_data['telefon'] = user.telefon
        output.append(user_data)

    return jsonify({'users' : output})

@app.route('/users/<id_utilizator>', methods = ['GET'])
@token_required
def one_user(current_user, id_utilizator):

    if not current_user.admin:
        return jsonify({'message' : 'Must be an admin to perform that function'})
    
    user = Utilizatori.query.get(id_utilizator)
    if not user:
        return jsonify({'message' : 'User does not exist'})
    
    user_data = {}
    user_data['id'] = user.id
    user_data['nume'] = user.nume
    user_data['prenume'] = user.prenume
    user_data['email'] = user.email
    user_data['parola'] = user.parola
    user_data['adresa_domiciliu'] = user.adresa_domiciliu
    user_data['telefon'] = user.telefon

    return jsonify({'user' : user_data})

@app.route('/users/add', methods = ['POST'])
@token_required
def create_user(current_user):
    if not current_user.admin:
       return jsonify({'message' : 'Must be an admin to perform that function'})
    
    data = request.get_json()

    hashed_pwd = generate_password_hash(data['parola'], method="sha256")

    utilizator =  Utilizatori(id = str(uuid.uuid4()), nume = data['nume'], prenume = data['prenume'], email = data['email'],
                              parola = hashed_pwd, adresa_domiciliu = data['adresa_domiciliu'], telefon = data['telefon'])
    db.session.add(utilizator)
    db.session.commit()

    return jsonify({'mesaj' : 'Utilizator adaugat cu succes!'})


@app.route('/users/<id_utilizator>', methods = ['PUT'])
@token_required
def promote_user(current_user, id_utilizator):
    if not current_user.admin:
        return jsonify({'message' : 'Must be an admin to perform that function'})

    user = Utilizatori.query.get(id_utilizator)
    if not user:
        return jsonify({'message' : 'User does not exist'})
    
    user.admin = True
    db.session.commit()

    return jsonify({'message' : 'The user has been promoted!'})


@app.route('/users/<id_utilizator>', methods = ['DELETE'])
@token_required
def delete_user(current_user, id_utilizator):
    if not current_user.admin:
        return jsonify({'message' : 'Must be an admin to perform that function'})
    
    user = Utilizatori.query.get(id_utilizator)
    if not user:
        return jsonify({'message' : 'User does not exist'})
    
    Cos.query.filter_by(id_utilizator=id_utilizator).delete()
    
    db.session.delete(user)
    db.session.commit()

    return jsonify({'message' : 'This user has been deleted!'})

@app.route('/login', methods=['GET'])
def login():
    auth = request.authorization

    if not auth or not auth.username or not auth.password:
        return make_response('Could not verify. No data provided.', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
        #cand nu primim date de autentificare
    user = Utilizatori.query.filter_by(email = auth.username).first()

    if not user:
        return make_response('Could not verify. User does not exist.', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
        #cand nu exista un anumit user
    if check_password_hash(user.parola, auth.password):
        token = jwt.encode({'id' : user.id, 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes = 15)}, app.config['SECRET_KEY'], algorithm='HS256')

        return jsonify({'token' : token})
    else: 
        return make_response('Could not verify. Password incorrect.', 401, {'WWW-Authenticate' : 'Basic realm="Login required!"'})
   #cand parola este incorecta 


#!!! RUTE COS DE CUMPARATURI !!!#

@app.route('/cart', methods=['POST'])
@token_required
def create_cart(current_user):

    cart = Cos(id_utilizator = current_user.id)

    db.session.add(cart)
    db.session.commit()

    return jsonify({'message' : 'Cart created'})

@app.route('/cart', methods=['GET'])
@token_required
def get_cart(current_user):

    carts = Cos.query.filter_by(id_utilizator = current_user.id).all()

    output = []
    
    for cart in carts: 
        cart_data = {} #creaza un dictionar python. Cheie si valori
        cart_data['id'] = cart.id
        cart_data['data_creare'] = cart.data_creare
        cart_data['id_utilizator'] = cart.id_utilizator
        output.append(cart_data)

    return jsonify({'cart' : output})

@app.route('/cart', methods=['DELETE'])
@token_required
def delete_cart(current_user):
    
    cart = Cos.query.filter_by(id_utilizator = current_user.id).first()

    if not cart:
        return jsonify({'message' : 'User does not have a cart yet'})
    
    db.session.delete(cart)
    db.session.commit()

    return jsonify({'message' : 'Cart deleted!'})

#!!! RUTE PRODUSE !!!#

@app.route('/products', methods=['GET'])
def get_all_products():

    products = Produse.query.all()

    output = []

    for product in products:
        product_data = {}
        product_data['id'] = product.id
        product_data['nume'] = product.nume
        product_data['categorie'] = product.categorie
        product_data['pret'] = product.pret 
        product_data['descriere'] = product.descriere
        product_data['imagine'] = product.imagine
        product_data['data_lansare'] = product.data_lansare
        output.append(product_data)

    return jsonify({'produse' : output})
    

@app.route('/products/<id_prod>', methods=['GET'])
def get_one_product(id_prod):

    product = Produse.query.get(id_prod)
    if not product:
        return jsonify({'message' : 'Product does not exist'})
    

    product_data = {}
    product_data['id'] = product.id
    product_data['nume'] = product.nume
    product_data['categorie'] = product.categorie
    product_data['pret'] = product.pret 
    product_data['descriere'] = product.descriere
    product_data['imagine'] = product.imagine
    product_data['data_lansare'] = product.data_lansare

    return jsonify({'produse' : product_data})


@app.route('/products/create', methods=['POST'])
@token_required
def create_products(current_user):
    if not current_user.admin:
        return jsonify({'message' : 'Acces restrictionat!'})
    
    data = request.get_json()
    product = Produse(nume = data['nume'], categorie = data['categorie'], pret = data['pret'], descriere = data['descriere'], imagine = data['imagine'])

    db.session.add(product)
    db.session.commit()

    return jsonify({'message' : 'Product added succesfully!'})


@app.route('/products/<id_prod>', methods = ['OPTIONS', 'PUT'])
def update_product(id_prod):
    product = Produse.query.get(id_prod)
    data = request.get_json()
    if not product:
        return jsonify({'message' : 'Product does not exist'})

    product.nume = data['nume']
    db.session.commit()

    response = jsonify({'message' : 'Product has been updated'})
    return response

@app.route('/products/<id_prod>', methods = ['DELETE'])
def delete_product(id_prod):
    product = Produse.query.get(id_prod)
    if not product: 
        return jsonify({'message' : 'Product does not exist'})

    DetaliiCos.query.filter_by(id_produs = id_prod).delete()

    db.session.delete(product)
    db.session.commit()

    return jsonify({'message' : 'Product deleted!'})    

#!!!Pentru a adauga produse in cos!!!

@app.route('/add_product', methods = ['POST'])
@token_required
def add_to_cart(current_user):
    produs_id = request.get_json()['produs_id']
    produs = Produse.query.get(produs_id)

    if not produs:
        return jsonify({'message' : 'Product is no longer available'}), 404
    
    cos = current_user.cos

    if not cos:
        cos = Cos(id_utilizator = current_user.id)
        db.session.add(cos)
    
    detalii_cos = DetaliiCos(id_cos = cos.id, id_produs = produs.id)
    db.session.add(detalii_cos)
    db.session.commit()

    return jsonify({'message' : f'Product {produs.nume} added succesfully'})


@app.route('/cart/products', methods = ['GET'])
@token_required
def added_products(current_user):
    
    products = db.session.query(Produse).join(DetaliiCos).join(Cos).filter(Cos.id_utilizator == current_user.id).all()

    output = []

    for product in products:
        product_data = {}
        product_data['id'] = product.id
        product_data['nume'] = product.nume
        product_data['categorie'] = product.categorie
        product_data['pret'] = product.pret 
        product_data['descriere'] = product.descriere
        product_data['imagine'] = product.imagine
        product_data['data_lansare'] = product.data_lansare
        output.append(product_data)
    
    return jsonify({'produse din cos' : output})





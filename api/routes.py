from api import app, db
from flask import request, jsonify, make_response
from api.models import Utilizatori, Produse, Cos, DetaliiCos
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
import datetime
from functools import wraps

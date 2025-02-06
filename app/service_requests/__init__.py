from flask import Blueprint

bp = Blueprint('service_requests', __name__)

from app.service_requests import routes

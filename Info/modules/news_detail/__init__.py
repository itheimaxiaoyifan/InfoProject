from flask import Blueprint

news_detail_blu = Blueprint('news_detail', __name__, url_prefix='/news_detail')
from . import views

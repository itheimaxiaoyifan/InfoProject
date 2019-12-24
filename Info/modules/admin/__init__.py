from flask import Blueprint, session, redirect, request

admin_blu = Blueprint('admin', __name__, url_prefix='/admin')

from . import views


@admin_blu.before_request
def check_admin():
    is_admin = session.get('is_admin')
    if not is_admin and not request.url.endswith('/admin/login'):
        return redirect('/')

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app import db
from sqlalchemy import func
from app.models import Siswa, Invoice, User, Role, Guru, Payment

# blueprint khusus buat halaman utama/dashboard
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
@login_required  # biar gak login = auto tendang
def dashboard():
    total_siswa = db.session.scalars(db.select(func.count(Siswa.id))).first() or 0

    total_unpaid = db.session.scalars(
        db.select(func.count(Invoice.id)).where(Invoice.status == 'unpaid')
    ).first() or 0

    total_guru = db.session.scalars(
        db.select(func.count(Guru.id))
    ).first() or 0

    pembayaran_terbaru = db.session.scalars(
        db.select(Payment).order_by(Payment.id.desc()).limit(5)
    ).all()

    return render_template('main/dashboard.html',
                           total_siswa=total_siswa,
                           total_unpaid=total_unpaid,
                           total_guru=total_guru,
                           pembayaran_terbaru=pembayaran_terbaru)
from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Role
from app import db

# blueprint buat auth
auth_bp = Blueprint('auth',__name__)

@auth_bp.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = db.session.execute(db.select(User).where(User.username == username)).scalar_one_or_none()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash("Username atau password salah!")
            return redirect(url_for('auth.login'))

    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form.get('name')
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')

        user_exist = db.session.execute(db.select(User).where(User.username == username)).scalar_one_or_none()
        if user_exist:
            flash("Username udah dipake!")
            return redirect(url_for('auth.register'))

        # Karena tabel 'users' butuh 'role_id', cari role yang ada dulu.
        # Kalau tabel roles masih kosong, bikin role dummy 'Admin' biar gak error.
        role = db.session.execute(db.select(Role).limit(1)).scalar_one_or_none()
        if not role:
            role = Role(name="Admin")
            db.session.add(role)
            db.session.commit()

        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

        new_user = User(name=name, username=username, email=email, password=hashed_pw, role_id=role.id)
        db.session.add(new_user)
        db.session.commit()

        flash("Akun berhasil dibuat! Silakan login.")
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))
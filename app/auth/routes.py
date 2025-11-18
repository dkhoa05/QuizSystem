from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash

from app.auth import auth_bp
from app import db
from app.models import User
from app.auth.forms import RegisterForm, LoginForm
from functools import wraps


# -----------------------
#   ADMIN REQUIRED
# -----------------------
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "admin":
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated


# -----------------------
#    USER REGISTER
# -----------------------
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("quiz.home"))

    form = RegisterForm()
    if form.validate_on_submit():
        existing = User.query.filter(
            (User.username == form.username.data)
            | (User.email == form.email.data)
        ).first()
        if existing:
            flash("Username hoặc Email đã tồn tại", "danger")
            return render_template("auth/register.html", form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            role="student",
        )
        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()
        flash("Đăng ký thành công, hãy đăng nhập.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


# -----------------------
#         LOGIN
# -----------------------
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("quiz.home"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash("Sai username hoặc password", "danger")
            return render_template("auth/login.html", form=form)

        login_user(user, remember=form.remember.data)
        next_page = request.args.get("next") or url_for("quiz.home")
        return redirect(next_page)

    return render_template("auth/login.html", form=form)


# -----------------------
#        LOGOUT
# -----------------------
@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
    flash("Đã đăng xuất", "info")
    return redirect(url_for("auth.login"))


# -----------------------
#   ADMIN: LIST USERS
# -----------------------
@auth_bp.route("/admin/users")
@admin_required
def manage_users():
    users = User.query.order_by(User.id).all()
    return render_template("auth/manage_users.html", users=users)


# -----------------------
#   ADMIN: ADD USER
# -----------------------
@auth_bp.route("/admin/users/new", methods=["GET", "POST"])
@admin_required
def create_user():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form.get("role", "student")

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("auth.manage_users"))

    return render_template("auth/create_user.html")


# -----------------------
#   ADMIN: EDIT USER
# -----------------------
@auth_bp.route("/admin/users/<int:user_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.username = request.form["username"]
        user.email = request.form["email"]
        user.role = request.form.get("role", user.role)

        pwd = request.form.get("password")
        if pwd:
            user.password_hash = generate_password_hash(pwd)

        db.session.commit()
        return redirect(url_for("auth.manage_users"))

    return render_template("auth/edit_user.html", user=user)


# -----------------------
#   ADMIN: DELETE USER
# -----------------------
@auth_bp.route("/admin/users/<int:user_id>/delete", methods=["POST"])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()
    return redirect(url_for("auth.manage_users"))

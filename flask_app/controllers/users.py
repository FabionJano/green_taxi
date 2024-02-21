import math
import random
import smtplib
from flask_app import app
from flask_app.models.user import EMAIL_REGEX, User
from flask_app.config.mysqlconnection import connectToMySQL
import requests

from flask import jsonify, render_template, redirect, session, request, flash
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

from .env import ADMINEMAIL
from .env import PASSWORD

# @app.route("/")
# def index():
#     # if "user_id" not in session:
#     #     return redirect("/dashboard")
#     return redirect("/dashboard")

# @app.route("/dashboard")
# def dashboard():
#     if "user_id" in session:
#         data = {"user_id": session["user_id"]}
#         loggedUser = User.get_user_by_id(data)
#         if loggedUser["isVerified"] == 0:
#             return redirect("/verify/email")

#     return render_template(
#         "index.html"
#     )

# @app.route("/getTaxi")
# def getTaxi():
#     if "user_id" in session:
#         data = {"user_id": session["user_id"]}
#         loggedUser = User.get_user_by_id(data)
#         if loggedUser["isVerified"] == 0:
#             return redirect("/verify/email")

#     return render_template(
#         "get_taxi.html"
#     )

# @app.route("/blog")
# def blog():
#     if "user_id" in session:
#         data = {"user_id": session["user_id"]}
#         loggedUser = User.get_user_by_id(data)
#         if loggedUser["isVerified"] == 0:
#             return redirect("/verify/email")

#     return render_template(
#         "blog-3.html"
#     )

# @app.route("/contact")
# def contact():
#     if "user_id" in session:
#         data = {"user_id": session["user_id"]}
#         loggedUser = User.get_user_by_id(data)
#         if loggedUser["isVerified"] == 0:
#             return redirect("/verify/email")

#     return render_template(
#         "contacts.html"
#     )

# @app.route("/login")
# def login():
#     if "user_id" in session:
#         data = {"user_id": session["user_id"]}
#         loggedUser = User.get_user_by_id(data)
#         if loggedUser["isVerified"] == 0:
#             return redirect("/verify/email")

#     return render_template(
#         "login.html"
#     )
# ===========================================================

# @app.errorhandler(404)
# def invalid_route(e):
#     return render_template("404.html")


# Intro
@app.route("/")
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/')
    data = {
        'user_id': session['user_id']
    }
    loggedUser = User.get_user_by_id(data)
    if loggedUser['isVerified'] == 0:
        return redirect('/verify/email')
    return (render_template('index.html', loggedUser=loggedUser))


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/registerPage")
def registerPage():
    if "user_id" in session:
        return redirect("/")
    return render_template("signUp.html")



@app.route("/register", methods=["POST"])
def register():
    if "user_id" in session:
        return redirect("/")
    errors = {}
    if User.get_user_by_email(request.form):
        errors["email"] = "This email already exists"

    if not EMAIL_REGEX.match(request.form["email"]):
        errors["email"] = "Invalid email address!"

    if not request.form["email"]:
        errors["email"] = "Email address is required."

    if len(request.form["last_name"]) < 2:
        errors["last_name"] = "Last name should be more than 2 characters!"

    if not request.form["last_name"]:
        errors["last_name"] = "Last Name is required."

    if len(request.form["password"]) < 8:
        errors["password"] = "Password must be longer than 8 characters"

    if not request.form["password"]:
        errors["password"] = "Password is required."

    if len(request.form["first_name"]) < 2:
        errors["first_name"] = "First name should be more than 2 characters!"

    if not request.form["first_name"]:
        errors["first_name"] = "First Name is required."

    if request.form["password"] != request.form["confirmpass"]:
        errors["confirmpass"] = "Passwords do not match!"

    if not request.form["confirmpass"]:
        errors["confirmpass"] = "Confirm Password is required."
    if errors:
        return jsonify({"valid": False, "errors": errors})
    string = "0123456789ABCDEFGHIJKELNOPKQSTUV"
    vCode = ""
    length = len(string)
    for i in range(6):
        vCode += string[math.floor(random.random() * length)]
    verificationCode = vCode

    data = {
        "first_name": request.form["first_name"],
        "last_name": request.form["last_name"],
        "email": request.form["email"],
        "password": bcrypt.generate_password_hash(request.form["password"]),
        "isVerified": 0,
        "verificationCode": verificationCode,
    }
    User.save(data)

    LOGIN = ADMINEMAIL
    TOADDRS = request.form["email"]
    SENDER = ADMINEMAIL
    SUBJECT = "Verify Your Email"
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
        (SENDER),
        "".join(TOADDRS),
        SUBJECT,
    )
    msg += f"Use this verification code to activate your account: {verificationCode}"
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.login(LOGIN, PASSWORD)
    server.sendmail(SENDER, TOADDRS, msg)
    server.quit()

    user = User.get_user_by_email(data)
    session["user_id"] = user["id"]
    return redirect('/verify/email')


@app.route("/verify/email")
def verifyEmail():
    if "user_id" not in session:
        return redirect("/")
    data = {"user_id": session["user_id"]}
    user = User.get_user_by_id(data)
    if user["isVerified"] == 1:
        return redirect("/dashboard")
    return render_template("verifyEmail.html", loggedUser=user)


# Email Validation
@app.route("/activate/account", methods=["POST"])
def activateAccount():
    if "user_id" not in session:
        return redirect("/")
    data = {"user_id": session["user_id"]}
    user = User.get_user_by_id(data)
    if user["isVerified"] == 1:
        return redirect("/index")

    if not request.form["verificationCode"]:
        flash("Verification Code is required", "wrongCode")
        return redirect(request.referrer)

    if request.form["verificationCode"] != user["verificationCode"]:
        string = "0123456789"
        vCode = ""
        length = len(string)
        for i in range(6):
            vCode += string[math.floor(random.random() * length)]
        verificationCode = vCode
        dataUpdate = {
            "verificationCode": verificationCode,
            "user_id": session["user_id"],
        }
        User.updateVerificationCode(dataUpdate)
        LOGIN = ADMINEMAIL
        TOADDRS = user["email"]
        SENDER = ADMINEMAIL
        SUBJECT = "Verify Your Email"
        msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
            (SENDER),
            "".join(TOADDRS),
            SUBJECT,
        )
        msg += (
            f"Use this verification code to activate your account: {verificationCode}"
        )
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.set_debuglevel(1)
        server.ehlo()
        server.starttls()
        server.login(LOGIN, PASSWORD)
        server.sendmail(SENDER, TOADDRS, msg)
        server.quit()

        flash("Verification Code is wrong. We just sent you a new one", "wrongCode")
        return redirect(request.referrer)

    User.activateAccount(data)
    return redirect("/")


# Log In Route
@app.route('/loginPage')
def loginPage():
    if 'user_id' in session:
        return redirect('/dashboard')
    return render_template('login.html')


# Control Log In Form
@app.route('/login', methods=['POST'])
def login():
    if 'user_id' in session:
        return redirect('/dashboard')
    if not User.get_user_by_email(request.form):
        flash('This email doesnt appear to be in our system! Try another one!', 'emailLogin')
        return redirect(request.referrer)

    user = User.get_user_by_email(request.form)
    if user:
        if not bcrypt.check_password_hash(user['password'], request.form['password']):
            flash('Wrong Password', 'passwordLogin')
            return redirect(request.referrer)

    session['user_id'] = user['id']

    return redirect('/verify/email')


@app.route("/contact")
def contact():
    if "user_id" not in session:
        return render_template("contacts.html")
    data = {"user_id": session["user_id"]}
    loggedUser = User.get_user_by_id(data)
    return render_template("contacts.html", loggedUser=loggedUser)


@app.route("/sendmail", methods=["POST"])
def senadmail():
    # if "user_id" not in session:
    #     return redirect("/")
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')
    LOGIN = ADMINEMAIL
    TOADDRS = ADMINEMAIL
    SENDER = ADMINEMAIL
    SUBJECT = "Conatct"
    msg = "From: %s\r\nTo: %s\r\nSubject: %s\r\n\r\n" % (
        (SENDER),
        "".join(TOADDRS),
        SUBJECT,
    )
    msg += (
        f"Name: {name}\nEmail: {email}\nMessage: {message}"
    )
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.set_debuglevel(1)
    server.ehlo()
    server.starttls()
    server.login(LOGIN, PASSWORD)
    server.sendmail(SENDER, TOADDRS, msg)
    server.quit()
    
    return redirect(request.referrer)

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/getTaxi')
def getTaxi():
    if 'user_id' in session:
        data = {
        'user_id': session['user_id']
        }
        loggedUser = User.get_user_by_id(data)
        return render_template('get_taxi.html', loggedUser = loggedUser)
    return render_template('get_taxi.html')


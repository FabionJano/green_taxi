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

@app.route("/")
def index():
    # if "user_id" not in session:
    #     return redirect("/dashboard")
    return redirect("/dashboard")

@app.route("/dashboard")
def dashboard():
    if "user_id" in session:
        data = {"user_id": session["user_id"]}
        loggedUser = User.get_user_by_id(data)
        if loggedUser["isVerified"] == 0:
            return redirect("/verify/email")

    return render_template(
        "index.html"
    )

@app.route("/getTaxi")
def getTaxi():
    if "user_id" in session:
        data = {"user_id": session["user_id"]}
        loggedUser = User.get_user_by_id(data)
        if loggedUser["isVerified"] == 0:
            return redirect("/verify/email")

    return render_template(
        "get_taxi.html"
    )
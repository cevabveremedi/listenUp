import os

# libs from the pset distro code
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from string import punctuation
from helpers import login_required, callYT

# import difflib # this is an option for the improved checking system.
# import youtube_dl, subprocess # option for the faster video call


# next lines until "/" route are from finance pset.

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///data.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    username = db.execute("SELECT username FROM users WHERE id=:id", id=session["user_id"])[0]['username']
    score = db.execute("SELECT score FROM users WHERE id=:id", id=session["user_id"])[0]['score']
    if not score:
        print("Something is wrong")
        score = 0

    return render_template("index.html", username=username, score=score)


@app.route("/login", methods=["GET", "POST"])
def login():
    # log user in

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            flash("Enter your username!")
            return render_template("login.html")

        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("Enter your password")
            return render_template("login.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Invalid username and/or password")
            return render_template("login.html")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    #Log user out

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/play", methods=["GET", "POST"])
@login_required
def play():
    # main function for the game

    if request.method == "POST":
        # for testing purposes:
        # url = "https://www.youtube.com/embed/y8XvQNt26KI?start=128&end=130&controls=0&disablekb=1&autoplay=1&cc_load_policy=3&version=3"
        # return render_template("play.html", url=url)

        diffSelected = request.form.get("diff")
        if not diffSelected:
            flash("You have to choose difficulty")
            return render_template("play.html")

        if diffSelected == 'easy':
            vid = callYT("UCsooa4yRKGN_zEE8iknghZA")
            #vid = ['4JLNb8-LOB0', [176.704, 2.084, 'without creating any echoes.']]
            pts = 1
        elif diffSelected == 'normal':
            vid = callYT("UCsXVk37bltHxD1rDPwtNM8Q")
            #vid = ['y8XvQNt26KI', [43.92, 2.88, 'But what if we could replace the mining industry on earth,']]
            pts = 2
        elif diffSelected == 'hard':
            vid = callYT("UCeiYXex_fwgYDonaTcSIk6w")
            pts = 3
        else:
            flash("Invalid option!")
            return render_template("play.html")
        

        if not vid:
            flash("Something went wrong!")
            return render_template("play.html")

        # play the audio

        # vid example = ['WA_jIj_w12U', [268.663, 3.458, 'promoting overfishing and illegal fishing.']]
        # url = f"https://www.youtube.com/watch?v={vid[0]}"

        start = int(vid[1][0]) - 1
        end = start + int(round(vid[1][1])) + 3
        url = f"https://www.youtube.com/embed/{vid[0]}?start={start}&end={end}&controls=0&disablekb=1&autoplay=1&cc_load_policy=3&version=3"
        
        # option for later!: https://stackoverflow.com/questions/57131049/is-it-possible-to-download-a-specific-part-of-a-file

        directURL = f"https://www.youtube.com/watch?v={vid[0]}&t={start}s"
        subtitle = vid[1][2]
        return render_template("play.html", url=url, subtitle=subtitle, directURL=directURL, pts=pts)

    else:
        return render_template("play.html")


@app.route("/check", methods=["GET", "POST"])
@login_required
def check():
    if request.method == "POST":
        # I'll save OGsubtitle and OGuinput, just in case I'll need later..
        OGuinput = request.form.get("uinput")
        OGsubtitle = request.form.get("subtitle")
        directURL = request.form.get("directURL")
        pts = int(request.form.get("pts"))
        
        # get rid of the punctuation (but still, "don't" and "dont" are not same)
        uinput = ''.join((c for c in OGuinput if c not in punctuation))
        subtitle = ''.join((c for c in OGsubtitle if c not in punctuation))

        # get rid of unwanted whitespace
        uinput = ' '.join(uinput.split())
        subtitle = ' '.join(subtitle.split())

        isTrue = 0
        if subtitle.casefold() in uinput.casefold():
            isTrue = 1
            # update user score
            usr_points = db.execute("SELECT score FROM users WHERE id=:id", id=session["user_id"])
            usr_points = usr_points[0]['score']
            usr_points += pts
            db.execute("UPDATE users SET score=:usr_points WHERE id=:id", usr_points=usr_points, id=session["user_id"])
        else:
            pts = 0
        
        # add this to the history table
        db.execute("INSERT INTO history (user_id, yturl, caption, answer, point) VALUES (:user_id, :yturl, :caption, :answer, :point)", user_id=session["user_id"], yturl=directURL, caption=subtitle, answer=uinput, point=pts)

        return render_template("/play.html", checkyt=directURL, ptsearned=pts, userguess=uinput, originalcc=subtitle)
    else:
        flash("You shouldn't be there...")
        return render_template("/index")


@app.route("/report", methods=["GET", "POST"])
@login_required
def report():
    # report a buggy video.
    if request.method == "POST":
        yturl = request.form.get("checkyt")
        db.execute("UPDATE history SET isbuggy=:yes WHERE yturl=:yturl", yes=1, yturl=yturl)
        flash("Gotcha")
    else:
        flash("You shouldn't be there...")

    return redirect("/history")


@app.route("/history")
@login_required
def history():
    #show game history
    rows = db.execute("SELECT * FROM history WHERE user_id=:id", id=session["user_id"])
    return render_template("history.html", rows=rows)


@app.route("/leaderboard")
@login_required
def leaderboard():
    #show top 10 scores
    topten = 1
    rows = db.execute("SELECT id, username, score FROM users ORDER BY score DESC")
    for index, dict in enumerate(rows):
        if dict['id'] == session["user_id"]:
            break
    if index > 9:
        topten = 0

    userinfo = rows[index]
    totalPlayer = len(rows)
    if totalPlayer < 10:
        looprange = totalPlayer
    else:
        looprange = 10
        if index > 9:
            looprange = 9

    return render_template("leaderboard.html", rows=rows[:10], userinfo=userinfo, totalPlayer=totalPlayer, looprange=looprange, topten=topten, index=index)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")
        confirm = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            flash("Username cannot be empty!")
            return render_template("register.html")

        # Ensure password was submitted
        elif not password:
            flash("Password cannot be empty")
            return render_template("register.html")

        # Ensure confirmation was submitted
        elif not confirm:
            flash("You must confirm your password")
            return render_template("register.html")

        # Ensure passwords are match
        elif not password == confirm:
            flash("Passwords don't match")
            return render_template("register.html")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        # Ensure username don't exists
        if len(rows) != 0:
            flash("username already exist")
            return render_template("register.html")

        # Insert new user
        db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username=username, hash=generate_password_hash(password))

        # Remember which user has logged in
        session.clear()
        session["user_id"] = db.execute("SELECT * FROM users WHERE username = ?", username)[0]["id"]

        # Redirect user to home page
        flash("Registered!")
        return redirect("/")
    else:
        return render_template("register.html")


#changes the user password
@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    if request.method == "POST":
        # get form input
        oldpassword = request.form.get("oldpassword")
        newpassword = request.form.get("newpassword")
        confirm = request.form.get("confirm")

        # check if everything is ok
        if not oldpassword:
            flash("Enter your password!")
            return render_template("changepassword.html")

        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        if not check_password_hash(rows[0]["hash"], oldpassword):
            flash("Your password is incorrect!")
            return render_template("changepassword.html")
        
        if not newpassword:
            flash("Password can not be empty!")
            return render_template("changepassword.html")
        elif not confirm:
            flash("You must confirm your new password")
            return render_template("changepassword.html")
        elif not newpassword == confirm:
            flash("Passwords don't match!")
            return render_template("changepassword.html")
        
        # set new password
        newpassword = generate_password_hash(newpassword)
        
        db.execute("UPDATE users SET hash=:newpassword WHERE id=:id", newpassword=newpassword, id=session["user_id"])
        flash("Password updated!")

        return redirect("/")
    else:
        return render_template("changepassword.html")

#Deletes the user account.
@app.route("/remove", methods=["GET", "POST"])
@login_required
def removeAccount():
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure password was submitted
        if not request.form.get("password"):
            flash("Enter your password!")
            return render_template("delete.html")

        # Query database for current user
        rows = db.execute("SELECT * FROM users WHERE id = ?", session["user_id"])

        # Ensure password is correct
        if not check_password_hash(rows[0]["hash"], request.form.get("password")):
            flash("Your password is incorrect!")
            return render_template("delete.html")

        # Delete user from database
        db.execute("DELETE FROM history WHERE user_id = ?", session["user_id"])
        db.execute("DELETE FROM users WHERE id = ?", session["user_id"])
        #!!!!!!!!!!!!!!!
        #! Note to self: Do NOT delete the history or you'll lose the bug reports!
        #! Option: update username to something like that: deletedUser#username
        #! Option2 (long-term): Just use another table or even database to keep bug reports.

        session.clear()
        # Redirect user to home page
        flash("Account deleted permanently.")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("delete.html")


def errorhandler(e):
    #Handle error
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    username = db.execute("SELECT username FROM users WHERE id=:id", id=session["user_id"])[0]['username']
    score = db.execute("SELECT score FROM users WHERE id=:id", id=session["user_id"])[0]['score']
    flash(e.name, e.code)
    return render_template("index.html", username=username, score=score)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

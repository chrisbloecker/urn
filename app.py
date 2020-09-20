from flask              import Flask, render_template, make_response, redirect, request, url_for, abort
from flask_login        import LoginManager, UserMixin, login_user, logout_user, login_required
from flask_wtf          import FlaskForm
from jinja2             import Template
from numpy.random       import choice
from os                 import environ
from wtforms            import PasswordField, SubmitField
from wtforms.validators import DataRequired

# ==============================================================================
# App config and setup
# ==============================================================================

# get configs from environment
class Config(object):
    SECRET_KEY = environ.get('SECRET_KEY') or 'you-will-never-guess'
    SESSION_COOKIE_SECURE = True


class Urn:
    def __init__(self, balls = ["blue", "blue", "red", "red"], locked = True):
        self.id      = 0
        self.balls   = balls
        self.initial = balls
        self.locked  = locked
        self.history = []

    def removeBall(self):
        self.id     += 1
        self.balls   = choice(self.balls, size = 3, replace = False)
        self.history = []

    def draw(self):
        ball = choice(self.balls, size = 1)[0]
        self.history.append(ball)
        return ball

    def reset(self):
        self.id     += 1
        self.balls   = self.initial
        self.history = []

    def toggle(self):
        self.locked = not self.locked


app = Flask(__name__)
app.config.from_object(Config)
app.urn = Urn()


login_manager = LoginManager()
login_manager.init_app(app)


users = { "admin" : { "password" :  app.config["SECRET_KEY"]} }

class User(UserMixin):
    id = "admin"

class LoginForm(FlaskForm):
    password = PasswordField("Password", validators = [ DataRequired() ])
    submit   = SubmitField("Sign In")

@login_manager.user_loader
def user_loader(username):
    if username not in users:
        return

    user = User()
    user.id = username
    return user

# ==============================================================================
# Bayesian Inference
# ==============================================================================

def pB(history):
    blues = len([b for b in history if b == "blue"])
    reds  = len([r for r in history if r == "red"])
    return ((2/3)**blues * (1/3)**reds * 0.5) \
         / (((2/3)**blues * (1/3)**reds * 0.5) + ((1/3)**blues * (2/3)**reds * 0.5))

# ==============================================================================
# Routes
# ==============================================================================

@app.route("/login", methods = ["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        if request.form.get("password") == users["admin"]["password"]:
            login_user(User())
            return redirect(url_for("admin", showUrn = False))
        else:
            abort(403)

    return render_template("login.html", form = form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

# for the admin to manage the urn
@app.route("/admin/<int:showUrn>", methods = ["GET"])
@login_required
def admin(showUrn):
    showUrn = bool(showUrn)
    return render_template( "admin.html"
                          , urn      = app.urn
                          , balls    = app.urn.balls
                          , numBalls = len(app.urn.balls)
                          , history  = [(i,ball,pB(app.urn.history[:i])) for i,ball in enumerate(app.urn.history, start = 1)]
                          , numDraws = len(app.urn.history)
                          , showUrn  = showUrn
                          )

@app.route("/admin/removeBall/<int:showUrn>", methods = ["GET"])
@login_required
def removeBall(showUrn):
    app.urn.removeBall()
    return redirect(url_for("admin", showUrn = showUrn))


@app.route("/admin/resetUrn/<int:showUrn>", methods = ["GET"])
@login_required
def resetUrn(showUrn):
    app.urn.reset()
    return redirect(url_for("admin", showUrn = showUrn))

@app.route("/admin/toggleUrn/<int:showUrn>", methods = ["GET"])
@login_required
def toggleUrn(showUrn):
    app.urn.toggle()
    return redirect(url_for("admin", showUrn = showUrn))


# for users to draw balls
@app.route("/")
def index():
    mUrnID = request.cookies.get("urnID")
    if app.urn.locked and mUrnID:
        urnID = int(mUrnID)
        if urnID == app.urn.id:
            ball = request.cookies.get("colour")
            return render_template("index.html", ball = ball)

    ball = app.urn.draw()
    response = make_response(render_template("index.html", ball = ball))
    response.set_cookie('urnID', str(app.urn.id).encode())
    response.set_cookie('colour', str(ball).encode())
    return response

if __name__ == '__main__':
    app.run(debug = True)

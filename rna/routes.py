from flask import render_template, url_for, flash, redirect, request, abort
from rna import app, db, bcrypt
from rna.forms import RegistrationForm, LoginForm, UpdateAccountForm, RunForm
from rna.models import User, Run
from flask_login import login_user, current_user, logout_user, login_required


@app.route("/", methods=["GET", "POST"])
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    form = RunForm()
    if form.validate_on_submit():
        run = Run(
            sequence=form.sequence.data,
            option1=form.option1.data,
            option2=form.option2.data,
            option3=form.option3.data,
            author=current_user,
        )
        db.session.add(run)
        db.session.commit()
        flash("Your run has started and has been registered!", "success")
        return redirect(url_for("current_run"))
    return render_template("home.html", title="Home", form=form)


@app.route("/current_run")
@login_required
def current_run():
    return render_template("current_run.html", title="Run")


@app.route("/user_runs")
@login_required
def user_runs():
    page = request.args.get("page", 1, type=int)
    user = User.query.filter_by(username=current_user.username).first_or_404()
    runs = (
        Run.query.filter_by(author=user)
        .order_by(Run.date_time.desc())
        .paginate(page=page, per_page=1)
    )
    return render_template("user_runs.html", runs=runs, user=user)


@app.route("/run/<int:run_id>")
def run(run_id):
    run = Run.query.get_or_404(run_id)
    return render_template("run.html", title=run.sequence, run=run)


@app.route("/run/<int:run_id>/delete", methods=["POST"])  # only need POST method
@login_required
def delete_run(run_id):
    run = Run.query.get_or_404(run_id)
    if run.author != current_user:
        abort(403)
    db.session.delete(run)
    db.session.commit()
    flash("Your run has been deleted!", "success")
    return redirect(url_for("user_runs"))


@app.route("/about")
def about():
    return render_template("about.html", title="About")


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get(
                "next"
            )  # for pages trying to get access without login, after the login, redirect to these pages
            return (
                redirect(next_page) if next_page else redirect(url_for("home"))
            )  # ternary conditional if
        else:
            flash("Login Unsuccessful. Please check email and password", "danger")
    return render_template("login.html", title="Login", form=form)


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode(
            "utf-8"
        )
        user = User(
            username=form.username.data, email=form.email.data, password=hashed_password
        )
        db.session.add(user)
        db.session.commit()
        flash(
            f"Your account has been created! You are now able to log in", "success"
        )  #'success' = category from bootstrap
        return redirect(url_for("login"))
    return render_template("register.html", title="Register", form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():  # on submit update database
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account has been updated!", "success")
        return redirect(url_for("account"))  # get request (?)
    elif request.method == "GET":  # without submit
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for("static", filename="my_pics/" + current_user.image_file)
    return render_template(
        "account.html", title="Account", image_file=image_file, form=form
    )  # post request (?)

import flask
from flask import render_template, request, redirect, url_for


import models
from sqlalchemy import func

app = flask.Flask("hrms")
db = models.SQLAlchemy(model_class=models.HRDBBase)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")


@app.route("/employees")
def employees():
    query = db.select(models.employee).order_by(models.employee.firstname)
    users = db.session.execute(query).scalars()
    return render_template("userlist.html", users=users)


@app.route("/employees/<int:empid>", methods=["GET", "POST"])
def employee_details(empid):
    employee_query = db.select(models.employee).where(models.employee.empid == empid)
    user = db.session.execute(employee_query).scalar()

    leaves_count_query = (
        db.select(func.count(models.employee.empid))
        .join(models.leaves, models.employee.empid == models.leaves.empid)
        .where(models.employee.empid == empid)
    )
    leaves = db.session.execute(leaves_count_query).scalar()

    max_leaves_query = db.select(models.designation.max_leaves).where(
        models.designation.jobid == models.employee.title_id,
        models.employee.empid == empid,
    )
    max_leaves = db.session.execute(max_leaves_query).scalar()

    employee_details = {
        "employee_id": user.empid,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "title": user.title.title,
        "email": user.email,
        "phone": user.ph_no,
        "leaves": leaves,
        "max_leaves": max_leaves,
    }

    if request.method == "POST":
        date = request.form["date"]
        reason = request.form["reason"]
        new_leave = models.leaves(empid=empid, date=date, reason=reason)
        db.session.add(new_leave)
        db.session.commit()
        return redirect(url_for("employee_details", empid=empid))

    return flask.jsonify(employee_details)


@app.route("/addleave/<int:empid>", methods=["POST"])
def add_leave(empid):
    if request.method == "POST":
        date = request.form["date"]
        reason = request.form["reason"]
        new_leave = models.leaves(empid=empid, date=date, reason=reason)
        db.session.add(new_leave)
        db.session.commit()
        return redirect(url_for("employees"))


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)

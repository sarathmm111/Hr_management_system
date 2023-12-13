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
    query = db.select(models.Employee).order_by(models.Employee.firstname)
    users = db.session.execute(query).scalars()
    return render_template("userlist.html", users=users)


@app.route("/employees/<int:empid>", methods=["GET", "POST"])
def employee_details(empid):
    employee_query = db.select(models.Employee).where(models.Employee.empid == empid)
    user = db.session.execute(employee_query).scalar()

    leaves_count_query = (
        db.select(func.count(models.Employee.empid))
        .join(models.Leaves, models.Employee.empid == models.Leaves.empid)
        .where(models.Employee.empid == empid)
    )
    leaves = db.session.execute(leaves_count_query).scalar()

    max_leaves_query = db.select(models.Designation.max_leaves).where(
        models.Designation.jobid == models.Employee.title_id,
        models.Employee.empid == empid,
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
    return flask.jsonify(employee_details)


@app.route("/addleave/<int:empid>", methods=["POST"])
def add_leave(empid):
    if request.method == "POST":
        date = request.form["date"]
        reason = request.form["reason"]
        new_leave = models.Leaves(empid=empid, date=date, reason=reason)
        db.session.add(new_leave)
        db.session.commit()
        return redirect(url_for("employees"))


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)

import flask
from flask import render_template, request, redirect, url_for
from flask_cors import CORS


import models
from sqlalchemy import func

app = flask.Flask("hrms")
CORS(app)
db = models.SQLAlchemy(model_class=models.HRDBBase)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")


@app.route("/employees")
def employees():
    query = db.select(models.Employee).order_by(models.Employee.empid)
    users = db.session.execute(query).scalars()
    u_list = []
    for user in users:
        data = {
            "id": user.empid,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "title": user.title.title,
        "email": user.email,
        "phone": user.ph_no,
        }
        u_list.append(data)
    return flask.jsonify(u_list)


@app.route("/employees/<int:empid>")
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
    leaves_left = max(0, min(int(max_leaves) - int(leaves), max_leaves))
    emp_details = []
    employee_details = {
        "employee_id": user.empid,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "title": user.title.title,
        "email": user.email,
        "phone": user.ph_no,
        "leaves": leaves,
        "max_leaves": max_leaves,
        "leaves_left": leaves_left
    }
    emp_details.append(employee_details)
    return flask.jsonify(emp_details)


@app.errorhandler(500)
def page_not_found(error):
    return render_template('500.html'), 500


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


@app.route("/leave/<int:empid>", methods=["GET", "POST"])
def addleave(empid):
  if request.method == "POST":
    data = request.get_json()
    date = data.get('date')
    reason = data.get('reason')
    if not date or not reason:
       return jsonify({'error': 'Enter data'}), 400
    insert_data = models.Leaves(empid=empid ,date=date, reason=reason)
    db.session.add(insert_data)
    db.session.commit()
    return flask.jsonify({'message': 'Leave submitted successfully'}), 200
  return flask.jsonify({'error': 'Method Not Allowed'}), 405


@app.route("/about")
def about():
    return render_template("about.html")


if __name__ == "__main__":
    app.run(debug=True)

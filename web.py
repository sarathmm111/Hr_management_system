import flask
from flask import render_template,request,redirect,url_for

import models
from sqlalchemy import func


app = flask.Flask("hrms")
db = models.SQLAlchemy(model_class = models.HRDBBase)

@app.route("/",methods = ["GET","POST"])
def index():
  if flask.request.method == "GET":
    return flask.render_template("index.html")
  elif flask.request.method == "POST":
    return "POSTED!"
    
@app.route("/employees")
def employees():
  query = db.select(models.employee).order_by(models.employee.firstname)
  users =db.session.execute(query).scalars()
  return flask.render_template("userlist.html",users = users)

@app.route("/employees/<int:empid>", methods=["GET", "POST"])
def employee_details(empid):
  all_user_query = db.select(models.employee).order_by(models.employee.firstname)
  all_user =db.session.execute(all_user_query).scalars()
  query = db.select(models.employee).where(models.employee.empid == empid)
  user = db.session.execute(query).scalar()
  query1 = db.select(func.count(models.employee.empid)).join(models.leaves,models.employee.empid == models.leaves.empid).where(models.employee.empid==empid)
  leaves = db.session.execute(query1).scalar()
  query2 = db.select(models.designation.max_leaves).where(models.designation.jobid == models.employee.title_id, models.employee.empid==empid)
  max_leaves = db.session.execute(query2).scalar()
  if request.method == "POST":
    date = request.form['date']
    reason = request.form['reason'] 
    query3 = models.leaves(empid=empid ,date=date, reason=reason)
    db.session.add(query3)
    db.session.commit()
    return redirect(url_for("employee_details",empid=empid))
  return render_template("userdetails.html", user=user, leaves=leaves, max_leaves=max_leaves, all_user=all_user)

@app.route("/about")
def about():
  return render_template("about.html")
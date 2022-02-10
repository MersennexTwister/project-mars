import os

from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
import sqlite3 as sql

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///data.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

def get_connection(db_name):
    conn = sql.connect(db_name)
    cur = conn.cursor()
    return conn, cur


def set_path(id):


    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLD = 'faces\\' + str(id)

    if not os.path.isdir(UPLOAD_FOLD):
        os.chdir('faces')
        os.mkdir(str(id))
        os.chdir('..')

    UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD_FOLD)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)

    def __repr__(self):
        return '<Teacher %r>' % self.id

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer)

    def __repr__(self):
        return '<Student %r>' % self.id


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/to-do")
def instruction():
    return render_template("todo.html")


@app.route("/about")
def teacher_inf():
    return render_template("about.html")


@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":

        id = len(Teacher.query.order_by(Teacher.id).all())
        name = request.form['name']
        login = request.form['login']
        password = request.form['password']

        t = Teacher(id=id, name=name, login=login, password=password)

        try:
            db.session.add(t)
            db.session.commit()
            return redirect('/')
        except:
            return 'При регистрации произошла ошибка'

    return render_template("register.html")


user_id = None


@app.route('/enter', methods=["POST", "GET"])
def enter():
    global user_id
    if request.method == "POST":
        conn, cur = get_connection('data.db')
        login = request.form['login']
        password = request.form['password']
        ask = 'SELECT id FROM Teacher WHERE login = "' + login + '" AND password = "' + password + '"'
        print(ask)
        ok = cur.execute(ask).fetchall()
        try:
            user_id = ok[0][0]
            return redirect('/user=' + str(user_id) + '/lk')
        except:
            return 'При попытке входа произошла ошибка'


    return render_template("enter.html")


@app.route('/user=<int:id>/lk')
def lk(id):
    if id != user_id:
        return "Нет доступа"
    if request.method == "POST":
        pass
    conn, cur = get_connection('data.db')
    ask = 'SELECT name FROM Student WHERE teacher_id = ' + str(id)
    res = cur.execute(ask).fetchall()
    st = []
    for i in res:
        st.append(i[0])
    ask = 'SELECT name FROM Teacher WHERE id = ' + str(id)
    name = cur.execute(ask).fetchone()[0]
    print(name)
    return render_template('lk.html', name=name, students=st, link="/user=" + str(id) + "/add_student")


@app.route('/user=<int:id>/add_student', methods=["POST", "GET"])
def add_student(id):
    if id != user_id:
        return "Нет доступа"
    if request.method == "POST":
        name = request.form['name']
        conn, cur = get_connection('data.db')
        photo1, photo2, photo3 = request.files['photo1'], request.files['photo2'], request.files['photo3']
        ask = "SELECT COUNT(id) FROM Student"
        inf = cur.execute(ask).fetchone()[0] + 1
        set_path(inf)
        photo1.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo1.filename)))
        photo2.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo2.filename)))
        photo3.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(photo3.filename)))

        t = Student(id=inf, name=name, teacher_id=id)

        try:
            db.session.add(t)
            db.session.commit()
            return redirect('/user=' + str(id) + '/lk')
        except:
            return 'При доабвлении ученика произошла ошибка'

    return render_template('add_student.html')


if __name__ == "__main__":
    app.run(debug=True)
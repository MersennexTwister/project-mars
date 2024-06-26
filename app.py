import os, shutil, pytz, datetime, cv2
from imutils import paths
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from flask import Flask, render_template, request, redirect, session, g, url_for
from sqlalchemy import exc, func
from flask_sqlalchemy import SQLAlchemy

from face_rec import *
from utils import * 
from settings import APP_ROOT, SESSION_DUR

app = Flask(__name__)
app.secret_key = '28bee993c5553ec59b3c051d535760198f6f018ed1cca1ddadcdb570352ef05b'
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{APP_ROOT}instance/mars.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 20000000
db = SQLAlchemy(app)


def auth(login, password):
    teacher = db.session.query(Teacher).filter_by(login=login).all()

    if len(teacher) == 0:
        return 0, -1
    elif not check_password_hash(teacher[0].psw, password):
        return 1, -1
    else:
        return 2, teacher[0].id


class Teacher(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    login = db.Column(db.String(50), unique=True)
    psw = db.Column(db.String(500), unique=True)

    def __repr__(self):
        return f"<teacher {self.id}>"


class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    grade = db.Column(db.Integer)
    teacher_id = db.Column(db.Integer, db.ForeignKey("teacher.id"))

    def __repr__(self):
        return f"<student {self.id}>"


class Mark(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"))
    date = db.Column(db.Integer)
    type = db.Column(db.Integer)

    def __repr__(self):
        return f"<mark {self.id}>"


def create_teacher(teacher_id):
    open(f"{APP_ROOT}encs/face_enc_{teacher_id}", 'a').close()
    os.makedirs(f"{APP_ROOT}static/undefined_image_cache/{teacher_id}/", exist_ok=True)

def put_mark(mark_data):
    new_id = Mark.query.count()
    new_data = Mark(id=new_id, student_id=mark_data[1], date=mark_data[0], type=(1 if (mark_data[2]) else -1))
    db.session.add(new_data)
    db.session.commit()

def update(teacher_id):
    id_list = []
    our_students = db.session.query(Student).filter_by(teacher_id=teacher_id).all()
    for student in our_students:
        id_list.append(student.id)
    count_faces(teacher_id, id_list)

def put_mark_recognize(teacher_id, img, type):
    face_id = recognite_the_face(teacher_id, img)

    if face_id != -1:
        dt = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
        put_mark([form_date(int(dt.day), int(dt.month), int(dt.year)), face_id, type])

    return face_id

def put_mark_direct(id, type):
    dt = datetime.datetime.now(pytz.timezone('Europe/Moscow'))
    put_mark([form_date(int(dt.day), int(dt.month), int(dt.year)), id, type])


PHOTO_SIZE_CONST = 1

@app.before_request
def load_logged_in_user():
    session.permanent = True
    app.permanent_session_lifetime = datetime.timedelta(minutes=SESSION_DUR)
    teacher_id = session.get('user_id')
    if teacher_id is None:
        g.teacher_name = None
    else:
        g.teacher_name = db.session.get(Teacher, teacher_id).name


@app.route("/")
def main():
    return render_template("main.html")


@app.route("/instruction")
def instruction():
    return render_template("instruction.html")


@app.route("/about")
def about():
    return render_template("about.html")


@app.route('/error_no_access')
def error_no_access():
    return render_template('error_no_access.html')

@app.route('/error_register')
def error_register():
    return render_template('error_register.html')

@app.route("/register", methods=["POST", "GET"])
def register():
    error = None

    if request.method == "POST":
        id = db.session.query(Teacher).count()
        name = request.form['name']
        login = request.form['login']
        password = generate_password_hash(request.form['password'])

        if login == '' or name == '' or password == '':
            error = strings.fill_all_fields

        if not check_name(name):
            error = 'Имя содержит недопустимые символы (& и/или -)!'

        if error is None:
            try:
                session['add_student_photo_num'] = 3
                session['edit_student_photo_num'] = 3
                new_teacher = Teacher(id=id, name=name, login=login, psw=password)
                db.session.add(new_teacher)
                db.session.commit()
            except exc.IntegrityError:
                error = f'Пользватель с логином "{login}" уже зарегестрирован!'
                return render_template("register.html", error=error)
            except:
                return redirect('/error_register')
            session['user_id'] = id
            create_teacher(id)
            return redirect('/lk')


    return render_template("register.html", error=error)

@app.route('/ident100500', methods=["POST", "GET"])
def ident_url():

    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']
        res, tid = auth(login, password)
        name = ""
        if res == 2:
            name = db.session.get(Teacher, tid).name

        return { "is": res, "name": name }
    
    return render_template('login.html', error=None)


@app.route('/login', methods=["POST", "GET"])
def login():
    error = None

    if request.method == "POST":
        login = request.form['login']
        password = request.form['password']
        res, tid = auth(login, password)

        if res == 0:
            error = 'Неверный логин!'
        elif res == 1:
            error = 'Неверный пароль!'

        if error is None:
            session['user_id'] = tid
            session['add_student_photo_num'] = 3
            session['edit_student_photo_num'] = 3
            return redirect('/lk')

    return render_template("login.html", error=error)


@app.route('/lk', methods=["POST", "GET"])
def lk():
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')

    g.update = session.get('is_success_upd')
    session['is_success_upd'] = None

    g.add = session.get('is_success_add')
    session['is_success_add'] = None

    g.delete = session.get('is_success_delete')
    session['is-success-delete'] = None

    if request.method == 'POST':
        update(teacher_id)
        session['is-success-upd'] = True
        return redirect('/lk')

    our_students = sorted(db.session.query(Student).filter_by(teacher_id=teacher_id).all(), key=(lambda x: (x.grade, x.name)))
    students_info = []
    for student in our_students:
        students_info.append([student.name, student.grade, 'lk/delete_student/student_id=' + str(student.id), 'lk/edit_student/student_id=' + str(student.id)])
    return render_template('lk.html', students_info=students_info)


@app.route('/lk/add_student', methods=["POST", "GET"])
def add_student():
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')

    photo_list = []

    def form_photo_list():
        photo_list.clear()
        for i in range(PHOTO_SIZE_CONST):
            photo_list.append('photo' + str(i))
        g.photo_num = PHOTO_SIZE_CONST

    form_photo_list()

    if request.method == "POST":
        name = request.form['surname'] + ' ' + request.form['name'] + ' ' + request.form['patronymic']
        grade = request.form['class']
        students_size = db.session.query(Student).filter_by(name=name, teacher_id=teacher_id).count()

        if not check_name(name):
            return 'Имя содержит недопустимые символы (& и/или -)!'

        if students_size > 0:
            return strings.student_already_exists
        try:
            new_id = db.session.query(func.max(Student.id))[0][0] + 1
        except:
            new_id = 1

        UPLOAD_FOLD = 'static/faces/' + str(new_id)
        os.makedirs(f"{APP_ROOT}{UPLOAD_FOLD}", exist_ok=True)

        for photo in request.files:
            if not request.files[photo].filename: continue
            request.files[photo].save(
                os.path.join(APP_ROOT + UPLOAD_FOLD, secure_filename(request.files[photo].filename)))
        db.session.add(Student(id=new_id, name=name, grade=grade, teacher_id=teacher_id))
        db.session.commit()
        session['is-success-add'] = name
        return redirect('/lk')

    return render_template('add_student.html', photo_list=photo_list)


@app.route('/lk/delete_student/student_id=<int:student_id>', methods=["POST", "GET"])
def delete_student(student_id):
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')

    student = db.session.get(Student, student_id)

    if student.teacher_id != teacher_id:
        return redirect('/error_no_access')

    name = student.name

    if request.method == "POST":
        db.session.delete(student)
        shutil.rmtree(APP_ROOT + 'static/faces/' + str(student_id))
        session['is-success-delete'] = name
        db.session.commit()
        return redirect('/lk')

    return render_template('delete_student.html', name=name)


@app.route('/lk/error_recognise')
def error_recognise():
    return render_template('error_recognise.html')


@app.route('/put_mark100500', methods=['POST', 'GET'])
def put_mark_url():

    if request.method == 'POST':
        photo = request.files['photo']
        mark = request.form['mark']
        login = request.form['login']
        password = request.form['password']

        res, teacher_id = auth(login, password)

        if res < 2:
            return { "is": 0, "name": "" }

        UPLOAD_FOLD = 'site_image_cache'
        UPLOAD_FOLDER = os.path.join(APP_ROOT, UPLOAD_FOLD)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        photo.save(APP_ROOT + 'site_image_cache/1.png')
        img = cv2.imread(APP_ROOT + "site_image_cache/1.png", cv2.IMREAD_COLOR)
        face = put_mark_recognize(teacher_id, img, mark == "+")

        if face == -1:
            UPLOAD_FOLD = f'static/undefined_image_cache/{teacher_id}/'
            cnt = len(list(paths.list_images(APP_ROOT + UPLOAD_FOLD))) + 1
            os.replace(APP_ROOT + 'site_image_cache/1.png', APP_ROOT + UPLOAD_FOLD + str(cnt) + '.png')
            return { "is": 1, "name": "" }
        else:
            os.remove(APP_ROOT + 'site_image_cache/1.png')

        name = db.session.get(Student, face).name
        return { "is": 2, "name": name }

    return render_template('put_mark.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/lk/undefined_students', methods=['POST', 'GET'])
def undefined_students():
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')

    correct = session.get('is-error')
    g.error = correct
    session['is-error'] = False

    undefined_path_list = list(paths.list_images(APP_ROOT + f'static/undefined_image_cache/{teacher_id}'))
    files_list = []
    for p in undefined_path_list:
        file_name = p.split('/')[-1]
        name = file_name[:file_name.find('.')]
        ext = file_name[file_name.find('.'):]
        files_list.append((f'undefined_image_cache/{teacher_id}/' + file_name, name, name + 'mark', ext))

    if request.method == 'POST':
        for (path, file_id, mark_id, ext) in files_list:
            student_name = request.form[file_id]
            mark = request.form[mark_id]
            if student_name != 'Ошибка':
                if mark == "":
                    session['is-error'] = True
                    return redirect('/lk/undefined_students')
                student_id = db.session.query(Student).filter_by(name=student_name).first_or_404().id
                photo_id = len(list(paths.list_images(APP_ROOT + 'static/faces/' + str(id)))) + 1
                put_mark_direct(student_id, mark == "+")
                os.replace(APP_ROOT + f'static/undefined_image_cache/{teacher_id}/' + file_id + ext,
                           APP_ROOT + 'static/faces/' + str(student_id) + '/' + str(photo_id) + ext)
            else:
                os.remove(APP_ROOT + f'static/undefined_image_cache/{teacher_id}/' + file_id + ext)
        return redirect('/lk')

    queries = db.session.query(Student).filter_by(teacher_id=teacher_id).all()
    names_list = []
    for q in queries:
        names_list.append(q.name)

    return render_template('undefined_students.html', files_list=files_list, names_list=names_list)


def check_date(day, month, year):
    if year <= 0:
        return False
    leap_year = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    if month <= 0 or month > 12:
        return False
    max_day = MONTHS[month - 1] + (1 if (leap_year and month == 2) else 0)
    if day <= 0 or day > max_day:
        return False
    return True


@app.route('/lk/results/filter=<string:filter>', methods=['POST', 'GET'])
def data_results(filter):
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')

    error = None

    student_list = db.session.query(Student).filter_by(teacher_id=teacher_id).all()
    all_student_names = []

    for student in student_list:
        all_student_names.append(student.name)

    all_student_names.sort()

    if request.method == 'POST':
        str_day, str_month, str_year = request.form['day'], request.form['month'], request.form['year']
        name = request.form['name-choice']
        grade = request.form['grade-choice']
        min_date = None

        if str_day == '' and str_month == '' and str_year == '':
            min_date = 0
        else:
            try:
                day, month, year = int(str_day), int(str_month), int(str_year)
                if not check_date(day, month, year):
                    error = 'Вы ввели несуществующую дату!'
                min_date = form_date(day, month, year)
            except:
                error = 'Неправильно введена дата!'

        if name == 'Выберите ученика':
            name = '-'
        if grade == 'Выберите класс':
            grade = 0

        if not error:
            return redirect(f'/lk/results/filter={name}&{grade}&{min_date}')

    params = filter.split('&')
    if len(params) != 3:
        return 404

    name, grade, min_date = params[0], int(params[1]), int(params[2])
    query = db.session.query(Mark, Student).join(Student).filter(Mark.date >= min_date)

    query = query.filter_by(teacher_id=teacher_id)

    if name != '-':
        query = query.filter_by(name=name)
    if grade != 0:
        query = query.filter_by(grade=grade)

    all_marks_list = query.all()
    student_info_list, marks_dates_list = [], []

    for mark, student in all_marks_list:
        student_info_list.append((student.grade, student.name))
        marks_dates_list.append(mark.date)

    student_info_list = sorted(list(set(student_info_list)))

    marks_dates_list = sorted(list(set(marks_dates_list)))

    student_dict, marks_dict = {}, {}

    marks_info = [[[0, 0] for _ in range(len(marks_dates_list))] for _ in range(len(student_info_list))]

    for i in range(len(student_info_list)):
        student_dict[student_info_list[i][1]] = i
    for i in range(len(marks_dates_list)):
        marks_dict[marks_dates_list[i]] = i

    for mark, student in all_marks_list:
        marks_info[student_dict[student.name]][marks_dict[mark.date]][0 if mark.type == 1 else 1] += 1

    for i in range(len(marks_dates_list)):
        date = marks_dates_list[i]
        day = date % 100
        date //= 100
        month = date % 100
        date //= 100
        year = date
        marks_dates_list[i] = form_string_date(day, month, year)

    return render_template("results.html",
                           all_student_names=all_student_names,
                           student_info_list=student_info_list,
                           marks_dates_list=marks_dates_list,
                           student_len=len(student_info_list),
                           marks_len=len(marks_dates_list),
                           marks_info=marks_info, error=error)


@app.route('/lk/delete_all', methods=['POST', 'GET'])
def delete_all():
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')
    if request.method == 'POST':
        to_delete_list = db.session.query(Mark, Student).join(Student).filter(Student.teacher_id == teacher_id).all()
        for mark, student in to_delete_list:
            db.session.delete(mark)
        db.session.commit()
        return redirect('/lk/results/filter=-&0&0')
    return render_template('delete_all.html')


@app.route('/lk/edit_student_photo/student_id=<int:student_id>', methods=['POST', 'GET'])
def edit_photo(student_id):
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')

    name = db.session.get(Student, student_id).name
    path_list = list(paths.list_images(APP_ROOT + f'static/faces/{student_id}/'))
    files_list = []

    for p in path_list:
        file_name = p.split('/')[-1]
        files_list.append(f'faces/{student_id}/' + file_name)

    if request.method == "POST":
        for path in files_list:
            is_deleted = request.form.get(path)
            if is_deleted is not None:
                os.remove(APP_ROOT + 'static/' + path)
        return redirect(f'/lk/edit_student_photo/student_id={student_id}')

    return render_template('edit_photo.html', name=name, files_list=files_list,
                           link=f"/lk/add_student_photo/student_id={student_id}")


@app.route('/lk/add_student_photo/student_id=<int:student_id>', methods=["POST", "GET"])
def add_photo(student_id):
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')
    photo_list = []
    name = db.session.get(Student, student_id).name

    def form_photo_list():
        photo_list.clear()
        for i in range(PHOTO_SIZE_CONST):
            photo_list.append('photo' + str(i))
        g.photo_num = PHOTO_SIZE_CONST

    form_photo_list()

    if request.method == "POST":
        if 'add_student' in request.form:
            for photo in request.files:
                if not request.files[photo].filename: continue
                request.files[photo].save(
                    os.path.join(APP_ROOT + 'static/faces/' + str(student_id),
                                 secure_filename(request.files[photo].filename)))
            return redirect(f'/lk/edit_student_photo/student_id={student_id}')
        elif 'increase_photo_num' in request.form:
            session['edit_student_photo_num'] += 1
            form_photo_list()
        elif 'decrease_photo_num' in request.form:
            session['edit_student_photo_num'] = max(1, session['edit_student_photo_num'] - 1)
            form_photo_list()

    return render_template('edit_student_photo.html', photo_list=photo_list, name=name)


@app.route('/lk/edit_student/student_id=<int:student_id>', methods=['POST', 'GET'])
def edit_student(student_id):
    teacher_id = session.get('user_id')
    if teacher_id is None:
        return redirect('/error_no_access')

    student = db.session.get(Student, student_id)

    if request.method == 'POST':
        student.name = request.form["surname"] + " " + request.form["name"] + " " + request.form["patronymic"]
        student.grade = int(request.form["grade"].split()[0])
        db.session.commit()
        return redirect('/lk')

    name_list = student.name.split()
    return render_template('enter_student.html', student_name=student.name, student_grade=f"{student.grade} класс",
                           name_list=name_list, link=f"/lk/edit_student_photo/student_id={student_id}")


def init_before_requests():
    with app.app_context():
        teachers_size = db.session.query(Teacher).count() 
    for i in range(teachers_size):
        create_teacher(i)
    

init_before_requests()

if __name__ == "__main__":
    app.run(host='0.0.0.0')

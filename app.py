from flask import Flask , render_template , request, jsonify , redirect , url_for, flash
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired
from werkzeug.utils import secure_filename
from wtforms import StringField, SubmitField
from flask_sqlalchemy import SQLAlchemy

import os
import shutil

from ultralytics import YOLO


app = Flask(__name__)

app.config['SECRET_KEY'] = 'MY SUPER SAFE KEY'
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///mydatabase.db'

db = SQLAlchemy(app)


class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    files = db.relationship('File', backref='project')

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    rows = db.relationship('Row', backref='file')

class Row(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String, nullable=False)
    file_id = db.Column(db.Integer, db.ForeignKey('file.id'), nullable=False)



class MyForm(FlaskForm):

    path = StringField('Path')
    project = StringField('Project')
    submit = SubmitField('Submit')


@app.route('/yolo/<path>/<project>')
def yolo(path , project):
    
    print(f" Path : {path} , Project : {project}")

    result_path = "D:\\ai tool\\results"
    
    model = YOLO("./yolov8n.pt")
    results = model.predict(source=path , save=True, save_txt=True , project=result_path , name=project)

    dir_path = result_path + "\\" + project +  "\\labels"


    files = os.listdir(dir_path)


    pro = Project(name=project)
    db.session.add(pro)
    db.session.commit()

    
    for file in files:

        with open(dir_path + "\\" + file , "r") as f:
            data = f.readlines()

        file_ = File(name=file, project_id=pro.id)
        db.session.add(file_)
        db.session.commit()


        for i in range(len(data)):
            data[i] = data[i][3:].rstrip()
            # print(data[i])
            row = Row(content=data[i], file_id=file_.id)
            db.session.add(row)
            db.session.commit()


        print(file , data)
    
    source_dir = path
    dest_dir  = "D:\\ai tool\\static\\data" + "\\" + project 
    os.makedirs(dest_dir, exist_ok=True)

    for filename in os.listdir(source_dir):
        
        file_path = os.path.join(source_dir, filename)
        shutil.copy2(file_path, os.path.join(dest_dir, filename))

    return render_template('yolo.html', results=results , path=path, project=project)

@app.route('/tool')
def tool():
    images = ['static\\data\\new\\cat.jpg' , 'static\\data\\new\\dog.jpg']
    # images = ['static/data/new/cat.jpg']

    return render_template('tool.html' , images=images)



@app.route('/data')
def show_data():
    projects = Project.query.all()

    print(projects)
    return render_template('data.html', projects=projects)

@app.route('/project', methods=['GET', 'POST'])
def project():
    
    form = MyForm()
    if form.validate_on_submit():

        path = form.path.data
        project = form.project.data
        
        project = project.strip()
        
        existing_project = Project.query.filter_by(name=project).first()

        if existing_project:
            flash('Project already exists', "error_msg")
            return redirect(url_for('project'))
        
        return redirect(url_for('yolo', path=path , project=project))

    pro = Project.query.all()
    return render_template('project.html', form=form , pro=pro)



@app.route('/index', methods=['GET', 'POST'])
def index():
    
    return render_template('index.html')



if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True, port=5000)
    

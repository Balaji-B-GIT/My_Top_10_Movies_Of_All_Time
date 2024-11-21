from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired
import requests
from dotenv import load_dotenv
import os

load_dotenv("C:/Python/Environmental variables/.env")
## get these from TMDB----------------------------------
api_key = os.getenv("tmdb_key")
api_token = os.getenv("tmdb_token")
tmdb_url = "https://api.themoviedb.org/3/search/movie"
tmdb_img_url = "https://image.tmdb.org/t/p/w500"
##------------------------------------------------------
headers = {
    "accept": "application/json",
    "Authorization": f'Bearer {api_token}'
}
'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)



# CREATE DB
class Base(DeclarativeBase):
    pass

class Update(FlaskForm):
    rating = StringField('Your Rating out of 10',validators=[DataRequired()])
    review = StringField('Your Review', validators=[DataRequired()])
    submit = SubmitField('Done')

class Add(FlaskForm):
    movie_title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add Movie')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///top-10-movies.db'

db = SQLAlchemy(model_class=Base)
db.init_app(app)



# CREATE TABLE
class Movie(db.Model):
    id:Mapped[int] = mapped_column(Integer,primary_key=True)
    title:Mapped[str] = mapped_column(String(250),nullable=False,unique=True)
    year:Mapped[int] = mapped_column(Integer,nullable=False)
    description:Mapped[str] = mapped_column(String(500),nullable=False)
    rating:Mapped[float] = mapped_column(Float,nullable=True)
    ranking:Mapped[int] = mapped_column(Integer,nullable=True)
    review:Mapped[str] = mapped_column(String,nullable=True)
    img_url:Mapped[str] = mapped_column(String,nullable=False)

    def __repr__(self):
        return f'<Movie {self.title}>'

with app.app_context():
    db.create_all()


@app.route("/")
def home():
    all_movies = db.session.execute(db.select(Movie).order_by(Movie.title)).scalars().all()
    return render_template("index.html",movies = all_movies)

@app.route("/edit/<int:id>",methods=["POST","GET"])
def edit(id):
    form = Update()
    movie_selected = Movie.query.get(id)
    if form.validate_on_submit():
        new_rating = form.rating.data
        new_review = form.review.data
        movie_selected.rating = new_rating
        movie_selected.review = new_review
        db.session.commit()
        return redirect(url_for("home"))
    return render_template("edit.html",movie = movie_selected, form = form)

@app.route("/delete")
def delete():
    ## another way of selecting a specific row(movie) --------------
    movie_id = request.args.get("id")
    movie_selected = db.get_or_404(Movie, movie_id)
    ##--------------------------------------------------------------
    db.session.delete(movie_selected)
    db.session.commit()
    return redirect(url_for("home"))

@app.route("/add",methods=["GET","POST"])
def add_page():
    form = Add()
    if form.validate_on_submit():
        title = form.movie_title.data
        parameters = {
            "query": title,
            "api_key": api_key,
        }
        response = requests.get(url=tmdb_url,params=parameters, headers=headers)
        data = response.json()["results"]
        return render_template("select.html",results = data)
    return render_template("add.html",form = form)


@app.route("/find")
def find_movie():
    movie_id = request.args.get("movie_id")
    print(movie_id)
    movie_url = f"https://api.themoviedb.org/3/movie/{movie_id}"
    print(movie_url)
    parameters = {
        "api_key": api_key,
    }
    data = requests.get(url = movie_url, params=parameters).json()
    print(data)
    new_movie = Movie(
        title = data["title"],
        year = data["release_date"].split('-')[0],
        description = data["overview"],
        img_url = f"https://image.tmdb.org/t/p/original{data['poster_path']}"
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for("edit",id = new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)

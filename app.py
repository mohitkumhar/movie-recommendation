"""
Flask Application to Predict Movies for User 
- Connected with MongoDB
- Predict Movies based on: Collaborative and Content-Based

"""

# Importting necessary libraries and modules
from typing import Optional, List
import pickle # For loading serialized models and data
from flask import Flask, render_template, redirect, url_for, request, flash #Flask for web framework
from pymongo import  MongoClient # MongoDB Client
import pandas as pd # Pandas for Data Handling and time stamp

# -----------------------------------------------------------------------------
# Database Connection Setup
# -----------------------------------------------------------------------------
# Connecting to MongoDB running locally on default port

client = MongoClient('mongodb://localhost:27017/')
db = client['user_db']
users_collection = db['users']
logs_collection = db['user_logs']


# -----------------------------------------------------------------------------
# Utility Functions
# -----------------------------------------------------------------------------

def log_user_interaction(user: dict, action: str, details: Optional[dict] = None):
    """
    Log a user's action into the logs_collection with timestamp.
    Args: 
        username (dict): The username and user id performing the action.
        action (str): The Action type (e.g, "login", "logout", "request reocmmendation").
        details (dict, optional): Additional metadata about the action
    """

    log_entry = {
        "user": user,
        "action": action,
        "details": details if details else {},
        "timestamp": pd.Timestamp.now(),
    }

    # Insert the log entry into MongoDB
    logs_collection.insert_one(log_entry)


# Creating Flask Application
app = Flask(__name__)
app.secret_key = "secret-key" # Secret key for session management and flash message


# -----------------------------------------------------------------------------
# Loading Data and Models
# -----------------------------------------------------------------------------
# Movie metadata
with open("C_movies.pkl", "rb") as f:
    movies = pickle.load(f)

movie_list = movies['title'].tolist()

# Collaborative filtering model and ratings data

with open("C_rating.pkl", "rb") as f:
    C_ratings = pickle.load(f) # ratings for collaborative model

with open("C_filtering_model.pkl", "rb") as f:
    model = pickle.load(f) # trained collaborative filtering model

with open("C_rating.pkl", "rb") as f:
    ratings = pickle.load(f) # DataFrame of existing ratings


# Function to get Colaborative Recommendations
def get_collaborative_recommendations(user_id: int, top_n: Optional[int] = 10):
    """
    Recommend movies using colaborative filtering

    Args:
        user_id (int): ID of the user to recommend
        top_n (int): Number of recommendation to return (default 10)
    Returns:
        List[str]: Top-N recommended movie titles
    """
    all_movie_ids = C_ratings['movieId'].unique()

    rated_movies = ratings[ratings['userId'] == user_id]['movieId'].tolist()

    unseen_movies = [i for i in all_movie_ids if i not in rated_movies]

    prediction = [] #  List to store (movieId, predicted_rating)
    for movie_id in unseen_movies:
        pred = model.predict(user_id, movie_id)
        prediction.append((movie_id, pred.est))

    # Sort by predicted rating desceding
    prediction.sort(key=lambda x: x[1], reverse=True)
    top_pred = prediction[:top_n]

    # Convert movieIds back to titles
    temp_df = pd.DataFrame(top_pred, columns=['movieId', 'estimated_rating'])
    return movies[movies['movieId'].isin(temp_df['movieId'])]['title'].tolist()


# For Content Based Recommendation
with open("CB_tfidfVectorizer.pkl", "rb") as f:
    tfidfVectorizer = pickle.load(f)

with open("CB_cosine_sim_matrix.pkl", "rb") as f:
    cosine_similarity_matrix = pickle.load(f)


# Function to get Content Based Recommendations
def get_content_based_recommendations(user_history: List[int], top_n: Optional[int] = 10):
    """
    Recommend movies based on content similarity of past watched movies.

    Args:
        user_history (List[int]): List of movieIds the user has watched.
        top_n (int): Number of recommendations to return
    Return:
        List[str]: Top-N recommended movie titles.
    """
    user_indicies = movies['movieId'].isin(user_history).index.tolist()

    sim_score = cosine_similarity_matrix[user_indicies].mean(axis=0)

    sorted_indices = sim_score.argsort()[::-1]

    recommended_indices = [
        i for i in sorted_indices if movies.iloc[i]['movieId'] not in user_history
        ]

    top_recommended_movies = movies.iloc[recommended_indices[:top_n]]

    return top_recommended_movies[['title']]['title'].tolist()


def fetch_movie_id(movie: str):
    """
    Fetch movieId from title of movie
    
    Args:
        movie (str): Name of movie
    """
    return movies[movies['title'] == movie]['movieId'].tolist()[0]

def fetch_top_n_movies(n: Optional[int] = 20):
    """
    Fetch the top-n movies based on highest rating.
    It retrieves movie titles and IDs

    Args:
        n (int, optional): Number of top-rated movies to fetch. Defaults to 20.
    Returns:
        List[dict]: A list of dictionaries that contains:
            - 'id': id of Movies
            - 'title': title of movies
            - 'poster_url': A placeholder image URL for the movie poster
    """

    # Top-20 Rated Movies
    top_n_movies = ratings.sort_values(by="rating", ascending=False)[:n]
    top_movies = movies[movies["movieId"].isin(top_n_movies['movieId'])]['title'].tolist()

    top_movies_data = []
    for movie in top_movies:
        movie_ids = fetch_movie_id(movie)
        top_movies_data.append(
            {
                'id': movie_ids,
                'title': movie,
                "poster_url": f"https://picsum.photos/200/300?random={hash(movie) % 1000}"
            }
        )

    return top_movies_data

def handle_recommendation(
        user_id: int,
        user_history: List[int],
        login_user: dict,
        recommendation_type: str
        ):
    """
    Function to handle movie recommendation based on user selection of recommendation type
    It calls the function that request the model for the recommended movies and returns it
    
    Args:
        user_id (int): The unique ID of the user requesting the recommendation.
        user_history (List[int]): List of movie_ids that user watched in past.
        login_user (dict): Dictionary containing user_id and username of the user
        recommendation_type (str): Type of recommendation  requested by user
                                 - It can be either 'collab' or 'content'.
    Returns:
        List[str]: A list of recommended movie titles.
    """

    if recommendation_type == 'collab':
        log_user_interaction(
            login_user,
            action="request recommendation",
            details={"type": "Collaborative Recommendation"}
            )
        return get_collaborative_recommendations(user_id=user_id)

    log_user_interaction(
        login_user,
        action="request recommendation",
        details={"type": "Content Based Recommendation"}
    )
    return get_content_based_recommendations(user_history=user_history)


def extract_movie_inputs(form_data):
    """
    Extract watched movie IDs and rated movie data from form inputs.

    Args:
        form_data (ImmutableMultiDict): The POST form data received from the Flask request.form
    Returns:
        watched (List[str]): list of watched movies list
        rated (List[dict]): list of all movies which the user rated (returns with movie id)
    """

    watched = []
    rated = []

    for key in form_data:
        if key.startswith("watched_"):
            movie_id = key.split("_")[1]
            watched.append(movie_id)

        elif key.startswith("rating_"):
            movie_id = key.split("_")[1]
            rating_value = form_data[key]
            rated.append({"movie_id": movie_id, "rating_value": rating_value})

    return watched, rated


def recommend(recommendation_type):
    """
    Render recommendation page.
    Handle form submissions for ratings, recommendation requests, and logout.
    """
    user = request.form.get("user")

    user_details = users_collection.find_one({'username': user})

    if user_details is None:
        return redirect(url_for('home'))

    login_user = {"userId": user_details['userId'], "username": user_details['username']}

    recommendations = []
    # recommendation_type = request.form.get("recommend_type")
    if (recommendation_type != "collab" and recommendation_type != "content"):
        return redirect(url_for("home", user=user))

    if user and recommendation_type:
        user_id = users_collection.find_one({'username': user})['userId']
        user_history = users_collection.find_one({'username': user})['moviesHistory']

        if recommendation_type and (recommendation_type == "collab" or recommendation_type == "content"):
            mov_titles = handle_recommendation(
                user_id=user_id,
                login_user=login_user, 
                user_history=user_history,
                recommendation_type=recommendation_type
                )

            for movie in mov_titles:
                movie_ids = fetch_movie_id(movie)
                recommendations.append(
                    {
                        "id": movie_ids,
                        "title": movie,
                        "poster_url": 
                                    f"https://picsum.photos/200/300?random={hash(movie) % 1000}"
                    }
                )

    return recommendations
    # return redirect(url_for('home', user=user))


# -----------------------------------------------------------------------------
# Flask Routes
# -----------------------------------------------------------------------------
@app.route('/')
def source_function():
    return redirect(url_for('index'))


@app.route('/login', methods=['GET', 'POST'])
def index():
    """
    Render the login page. On POST, validate the user and redirect to recommendations.
    """
    if request.method == 'POST':
        username = request.form['username']

        user = users_collection.find_one({'username': username})
        if user:
            login_user = {"userId": user['userId'], "username": user['username']}
            log_user_interaction(login_user, "login") # saving LogIn Successful log
            return redirect(url_for('home', user=username))
        flash("Invalid userName not found")

    return render_template('index.html')


top_movies_data = fetch_top_n_movies()
@app.route('/home', methods= ['GET', 'POST'])
def home():
    # Top-n Rated Movies
    user = request.args.get("user")
    user_details = users_collection.find_one({'username': user})

    if user_details is None:
        user = None
    recommendations = []
    if request.method == 'POST':
        recommendation_type = request.form.get('recommend_type')
        recommendations =  recommend(recommendation_type)

    return render_template(
    'home.html',
    user=user,
    top_movies=top_movies_data,
    recommendations = recommendations
    )


@app.route('/saveinfo', methods= ['POST'])
def saveinfo():
    user = request.form.get("user")
    user_details = users_collection.find_one({'username': user})

    if not user_details:
        return redirect(url_for('index'))
    login_user = {"userId": user_details['userId'], "username": user_details['username']}

    watched_movies, rated_movies = extract_movie_inputs(request.form)

    if not watched_movies or not rated_movies:
        return redirect(url_for("home", user=user))

    log_user_interaction(
    login_user,
    action="save_ratings",
    details={
        "watched_movies": watched_movies,
        "rated_movies": rated_movies,
    }
    )

    return redirect(url_for('home', user=user))

@app.route('/logout')
def logout():
    return redirect(url_for('index'))

# -----------------------------------------------------------------------------
# Run the Flask development server
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True) # Debug mode for development

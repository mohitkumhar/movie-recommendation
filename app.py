# Importting necessary libraries and modules
from flask import Flask, render_template, redirect, url_for, request, flash  # Flask for web framework
from pymongo import  MongoClient # MongoDB Client
import pandas as pd # Pandas for Data Handling and time stamp
import pickle # For loading serialized models and data
from typing import Optional, List

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

def log_user_interaction(user: str, action: str, details: Optional[dict] = None):
    """
    Log a user's action into the logs_collection with timestamp.
    Args: 
        username (str): The username performing the action.
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
movies = pickle.load(open("C_movies.pkl", "rb"))
movie_list = movies['title'].tolist()

# Helper to fetch movieId from movie title
def get_movieId(movie_name: str):
    """
    Retrieve the movieId corresponding to a given movie title/

    Args:
        movie_name (str): Title of the movie
    Returns:
        int: the movieId if found, else None
    """
    if movie_name in movies['title'].values:
        return (movies[movies['title'] == movie_name]['movieId'].tolist()[0])


# Collaborative filtering model and ratings data
C_ratings = pickle.load(open("C_rating.pkl", "rb")) # ratings for collaborative model
model = pickle.load(open("C_filtering_model.pkl", "rb")) # trained collaborative filtering model
ratings = pickle.load(open("C_rating.pkl", "rb")) # DataFrame of existing ratings

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
        if movie_id in unseen_movies:
            pred = model.predict(user_id, movie_id)
            prediction.append((movie_id, pred.est))

    # Sort by predicted rating desceding
    prediction.sort(key=lambda x: x[1], reverse=True)
    top_pred = prediction[:top_n]

    # Convert movieIds back to titles
    temp_df = pd.DataFrame(top_pred, columns=['movieId', 'estimated_rating'])
    return movies[movies['movieId'].isin(temp_df['movieId'])]['title'].tolist()


# For Content Based Recommendation
tfidfVectorizer = pickle.load(open("CB_tfidfVectorizer.pkl", "rb"))
cosine_similarity_matrix = pickle.load(open("CB_cosine_sim_matrix.pkl", "rb"))


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

    recommended_indices = [i for i in sorted_indices if movies.iloc[i]['movieId'] not in user_history]

    top_recommended_movies = movies.iloc[recommended_indices[:top_n]]

    return top_recommended_movies[['title']]['title'].tolist()


def fetch_movie_id(movie: str):
    """
    Fetch movieId from title of movie
    
    Args:
        movie (str): Name of movie
    """
    return movies[movies['title'] == movie]['movieId'].tolist()[0]


# -----------------------------------------------------------------------------
# Flask Routes
# -----------------------------------------------------------------------------
@app.route('/', methods=['GET', 'POST'])
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
            return redirect(url_for('recommend', user=username))
        else:
            flash("Invalid userName not found")

    return render_template('index.html')


@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    """
    Render recommendation page. Handle form submissions for ratings, recommendation requests, and logout.
    """
    user = request.args.get("user")

    user_details = users_collection.find_one({'username': user})
    login_user = {"userId": user_details['userId'], "username": user_details['username']}
    
    recommendations = []
    recommendation_type = None

    watched_movies = []
    rated_movies = []

    # Process watched and rated inputs
    for key in request.form:
        if key.startswith("watched_"):
            movie_id = key.split("_")[1]
            watched_movies.append(movie_id)
        elif key.startswith("rating_"):
            movie_id = key.split("_")[1]
            rating_value = request.form[key]
            rated_movies.append({"movie_id": movie_id, "rating": rating_value})

    # Top-20 Rated Movies
    top_20_movies = ratings.sort_values(by="rating", ascending=False)[:20]
    top_movies = movies[movies["movieId"].isin(top_20_movies['movieId'])]['title'].tolist()

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

    if user:
        user_id = users_collection.find_one({'username': user})['userId']
        user_history = users_collection.find_one({'username': user})['moviesHistory']
        
        if request.method == 'POST':
            recommendation_type = request.form.get('recommend_type')

            action = request.form.get('action')

            if action == "save_ratings":
                log_user_interaction(
                    login_user, 
                    action="save_ratings", 
                    details={
                        "watched_movies": watched_movies,
                        "rated_movies": rated_movies,
                    }
                )

            elif recommendation_type:

                if recommendation_type == 'collab':
                    log_user_interaction(login_user, action="request recommendation", details={"type": "Collaborative Recommendation"})
                    mov_titles = get_collaborative_recommendations(user_id=user_id)
                else:
                    log_user_interaction(login_user, action="request recommendation", details={"type": "Content Based Recommendation"})
                    mov_titles = get_content_based_recommendations(user_history=user_history)

                for movie in mov_titles:
                    movie_ids = fetch_movie_id(movie)
                    recommendations.append(
                        {
                            "id": movie_ids,
                            "title": movie,
                            "poster_url": f"https://picsum.photos/200/300?random={hash(movie) % 1000}"
                        }
                    )

            # Handles the logout action
            if request.form.get("logout") == 'loging_out':
                log_user_interaction(user, action="logout")
                return redirect(url_for("index"))

    # render recommendations template with data
    return render_template('recommend.html', user=user, movie_list=movie_list, recommendations=recommendations, recommend_type=recommendation_type, top_movies=top_movies_data)


# -----------------------------------------------------------------------------
# Run the Flask development server
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True) # Debug mode for development
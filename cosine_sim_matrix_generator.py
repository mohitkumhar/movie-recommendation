"""
Code to generate the Cosine Similarity Matrix from movie dataset
"""

import pickle
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Read the movies dataset from a CSV file
movies = pd.read_csv(r'dataset\movie.csv')

# Create a combined metadata field by concatenating title and genres
movies['metadata'] = movies['title'] + ' ' + movies['genres']

# Initialize TF-IDF vectorizer, excluding English stop words
tfidf_vectorizer = TfidfVectorizer(stop_words='english')

# Fit the vectorizer on the metadata and transform it into a TF-IDF matrix
tfidf_matrix = tfidf_vectorizer.fit_transform(movies['metadata'])

# (Optional) Convert the sparse TF-IDF matrix to a dense array for inspection
tfidf_matrix.toarray()

# Compute pairwise cosine similarity between all movie vectors
cosine_sim_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)

# Function to recommend movies based on a user's watch history
def recommand_movie(user_history, top_n = 10):
    """
    Function to recommend movies based on user past watched movies
    (Content Based Recommendation Function)
    
    Args:
        user_history List[int]: It is the list List of movies id, user already watched
    """
    # Find the indices of the movies the user has watched
    user_indices = movies[movies['movieId'].isin(user_history)].index.tolist()

    # Compute the average similarity score across the user's watched movies
    sim_score = cosine_sim_matrix[user_indices].mean(axis=0)

    # Sort movie indices by similarity score in descending order
    sorted_indices = sim_score.argsort()[::-1]

    # Filter out movies the user has already watched
    recommanded_indices = [
        i for i in sorted_indices if movies.iloc[i]['movieId'] not in user_history
        ]

    # Select the top N recommended movies and return their titles
    top_recommanded_movies = movies.iloc[recommanded_indices[:top_n]]
    return top_recommanded_movies[['title']]['title'].tolist()

# Serialize and save the TF-IDF vectorizer for later reuse
with open("CB_tfidfVectorizer.pkl", "wb") as f:
    pickle.dump(tfidf_vectorizer, f)

# Save the movies DataFrame (with metadata) for later use
with open("CB_movies.pkl", "wb") as f:
    pickle.dump(movies, f)

# Save the computed cosine similarity matrix for content-based recommendations
with open("CB_cosine_sim_matrix.pkl", "wb") as f:
    pickle.dump(cosine_sim_matrix, f)

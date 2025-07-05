# Personalized Movie Recommendation System with A/B Testing

## Project Overview

This project recommends Movies based on **Collaborative Filtering** and **Content-Based Filtering** approaches. It also find the better algorithm using  **A/B Testing Approach** to statistically compare the two Algorithm based on  user interactions. The backend is built with **Flask**, and user interaction are stored in **MongoDB**.

## Objectives

-   Build collaborative filtering and content-based recommendation.
    
-   Tracking user interactions through logging.
    
-   Do A/B testing to analyze the which algorithms Perform better.
    
-   Expose APIs via Flask.
    
-   Visualize the A/B test outcomes.
    

## Recommendation Approaches

### 1. **Collaborative Filtering (Group A)**

-   Based on user-item interactions.
    
-   Implemented with `surprise` library.
    
-   Models are trained and stored as `.pkl`.
    

### 2. **Content-Based Filtering (Group B)**

-   Uses TF-IDF and cosine similarity between movie's genre.
    
-   Recommends movies similar to other and don't suggest movies the user has already watched.
    
-   It takes movies metadata from the MovieLens dataset.



##  A/B Testing Framework

-   All request of user is logged in **MongoDB** with type (`Collaborative` or `Content-Based`) and timestamp.
    
-   **Success Rate** is defined as whether the user rated the movie after getting recommendations.
    
-   **Total Clicks** are the number of recommendation requests made for each algorithm.
    


## Results

### Total Clicks by Algorithm

-   **Content-Based** algorithm was selected by user more than the Collaborative one.
    

### Success Rate by Algorithm

-   **Content-Based** again performed better, showing users rated after viewing recommendations.
    

##  Conclusion

-   The **Content-Based ** is better than Collaborative Filtering on both metrics:
    
    -   Higher total user clicks.
        
    -   Higher success rate (user rate movie getting recommendation).
        
-   Thus, Content-Based Recommendation seems to be **better  algorithm** for this use case.


## Tools & Technologies Used

-   **Flask** for backend web framework
    
-   **MongoDB** for logging user interaction and storing user data.
    
-   **pymongo** for Python-MongoDB interaction
    
-   **Pandas**, **Matplotlib** for A/B testing and analysis
    
-   **Pickle** to load saved ML model and other data
    
-   **GitHub Actions** for CI/CD (linting, testing, deployment automation)
    

----------

## Project Structure

```
movie-recommender/
│
├── app.py                        # Flask backend
├── C_filtering_model.pkl         # Collaborative filtering model
├── CB_tfidfVectorizer.pkl        # Vectorizer for content-based
├── CB_cosine_sim_matrix.pkl      # Similarity matrix for content based
├── mongo_export/                 # Sample user data & logs
├── templates/                    # HTML templates
├── requirements.txt              # Dependencies
├── requirements-linux.txt        # Linux Dependencies
├── a-b_testing.ipynb             # A/B testing & analysis Notebook
├── test.py                       # Testing file
```

## What’s Missing / Areas for Improvement

1.  **User Profile Expansion**  
    Current user profiles are Hard Coded. Allow users to dynamically build history (e.g., like/dislike, watch history updates).
    
2.  **Authentication & Authorization**  
    The login system is basic. Consider adding full authentication for security in production.
    
3.  **A/B Testing**  
    A/B testing can be done with better approaches for better result and for finding better algorithm.
    
4.  **API Tests**  
    Very Minimal use of **pytest** for testing Flask routes and logic. Adding test coverage increases maintainability.
    
5.  **Metrics Logging Dashboard**  
    Currently MongoDB stores logs, integrating a dashboard, We should the Database which works on real-time and better.
   
6. **Collaborative  Enhancement** 
	Should update model that suggest the Movies based on the similar user intrest.
    
7.  **Movie Metadata**  
    The content-based model only considers text similarity. We should Add  genres, actors, or directors that would make it better.
    

## Future Enhancements

-   **Hybrid Recommendation System**: Combine both collaborative and content-based methods for better results
    
-   **Recommendation Feedback Loop**: Let users provide feedback and learn from it in real-time.
    
-   **Cloud Hosting**: Deploy on cloud to serve ML model and data faster to user.
    
-   **Mobile or React Frontend**: Make a modern frontend with a responsive UI.
  

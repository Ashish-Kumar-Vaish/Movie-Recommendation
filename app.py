from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import joblib
import difflib
import numpy as np

app = Flask(__name__)
app.secret_key = "any-secret-key"

data = joblib.load('data.pkl')
similarity = joblib.load('similarity.pkl')

def to_serializable(val):
    if isinstance(val, (np.integer, np.int64)):
        return int(val)
    if isinstance(val, (np.floating, np.float64)):
        return float(val)
    if isinstance(val, (np.ndarray,)):
        return val.tolist()
    return val

def recommend(movie_name, limit=20, offset=0):
    movie_list = data['title'].tolist()
    match = difflib.get_close_matches(movie_name, movie_list)

    if not match:
        return []

    match_title = match[0]
    index = int(data[data.title == match_title].index.values[0])
    similarity_scores = list(enumerate(similarity[index]))
    sorted_scores = sorted(similarity_scores, key=lambda x: x[1], reverse=True)

    results = []
    start = offset + 1
    end = offset + limit + 1
    for i in range(start, min(end, len(sorted_scores))):
        movie = data.iloc[sorted_scores[i][0]]
        results.append({
            'title': str(movie['title']),
            'overview': str(movie['overview']),
            'genres': str(movie['genres']).replace(' ', ', '),
            'director': str(movie.get('director', '')),
            'cast': str(movie.get('cast', '')),
            'vote_average': to_serializable(movie.get('vote_average', 'N/A')),
            'vote_count': to_serializable(movie.get('vote_count', 0)),
        })

    return results

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user_input = request.form.get("movie")
        session['user_input'] = user_input
        return redirect(url_for('home'))  

    user_input = session.get('user_input', '') 
    recommendations = recommend(user_input, limit=20, offset=0) if user_input else []

    return render_template("index.html", recommendations=recommendations, user_input=user_input)

@app.route("/load_more")
def load_more():
    movie_name = request.args.get("movie", "")
    offset = int(request.args.get("offset", 0))
    limit = int(request.args.get("limit", 20))
    recs = recommend(movie_name, limit=limit, offset=offset)
    return jsonify(recs)

if __name__ == "__main__":
    app.run(debug=True)
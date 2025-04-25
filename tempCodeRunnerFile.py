from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from database import register_user, get_user_by_email  # MongoDB logic
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "carecraze123")

# === Load the nutrition CSV globally ===
nutrition_df = pd.read_csv("nutrition_db_100.csv")

# === Home Page ===
@app.route('/')
def home():
    user = session.get('user')  # Check if user is logged in
    return render_template("home.html", user=user)

# === Register Page ===
@app.route('/register', methods=['GET'])
def register_page():
    return render_template("register.html")

# === Register Form Submission ===
@app.route('/register', methods=['POST'])
def register_submit():
    user_data = {
        "name": request.form.get("name"),
        "email": request.form.get("email"),
        "password": request.form.get("password"),
        "age": int(request.form.get("age")),
        "height": float(request.form.get("height")),
        "weight": float(request.form.get("weight")),
        "gender": request.form.get("gender")
    }

    success = register_user(user_data)

    if success:
        session['user'] = {
            "name": user_data["name"],
            "email": user_data["email"]
        }
        flash("✅ Registration successful!")
        return redirect(url_for('home'))
    else:
        flash("⚠️ Email already exists. Please log in.")
        return redirect(url_for('register_page'))

# === Login Submission ===
@app.route('/login', methods=['POST'])
def login_submit():
    email = request.form.get("login_email")
    password = request.form.get("login_password")

    user = get_user_by_email(email)
    if user and user["password"] == password:
        session['user'] = {
            "name": user["name"],
            "email": user["email"]
        }
        flash(f"👋 Welcome back, {user['name']}!")
        return redirect(url_for('home'))
    else:
        flash("❌ Invalid email or password.")
        return redirect(url_for('register_page'))

# === Logout ===
@app.route('/logout')
def logout():
    session.clear()
    flash("👋 You have been logged out.")
    return redirect(url_for('home'))

# === Nutrition Search API ===
@app.route("/search_food")
def search_food():
    query = request.args.get("query", "").lower()
    match = nutrition_df[nutrition_df["food"].str.lower() == query]

    if not match.empty:
        item = match.iloc[0]
        return jsonify({
            "food": {
                "name": item["food"],
                "protein": float(item["protein"]),
                "carbs": float(item["carbs"]),
                "fats": float(item["fats"]),
                "fiber": float(item["fiber"])
            }
        })
    else:
        return jsonify({
            "food": {
                "name": query,
                "protein": 0,
                "carbs": 0,
                "fats": 0,
                "fiber": 0
            }
        })

# === Meal Log Page ===
@app.route("/search_food")
def search_food():
    query = request.args.get("query", "").lower()

    # Try exact match first (for nutrient fetching)
    exact_match = nutrition_df[nutrition_df["food"].str.lower() == query]
    if not exact_match.empty:
        item = exact_match.iloc[0]
        return jsonify({
            "food": {
                "name": item["food"],
                "protein": float(item["protein"]),
                "carbs": float(item["carbs"]),
                "fats": float(item["fats"]),
                "fiber": float(item["fiber"])
            },
            "matches": nutrition_df[nutrition_df["food"].str.lower().str.startswith(query)]["food"].tolist()
        })

    # If no exact match, return just suggestions
    suggestions = nutrition_df[nutrition_df["food"].str.lower().str.startswith(query)]
    return jsonify({
        "food": {
            "name": query,
            "protein": 0,
            "carbs": 0,
            "fats": 0,
            "fiber": 0
        },
        "matches": suggestions["food"].tolist()
    })
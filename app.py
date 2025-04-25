from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify

import os
import pandas as pd
from database import register_user, get_user_by_email, save_meal_entry, get_today_meals

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET", "carecraze123")

# === Load the nutrition CSV globally ===
nutrition_df = pd.read_csv("nutrition_db_100.csv")

# === Home Page ===
@app.route('/')
def home():
    user = session.get('user')
    return render_template("home.html", user=user)

# === Register Page (GET)
@app.route('/register', methods=['GET'])
def register_page():
    return render_template("register.html")

# === Register Form Submission (POST)
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

# === Login Handler
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

# === Logout
@app.route('/logout')
def logout():
    session.clear()
    flash("👋 You have been logged out.")
    return redirect(url_for('home'))

# === Nutrition Search API with Suggestions
@app.route("/search_food")
def search_food():
    query = request.args.get("query", "").lower()

    # Exact match for adding food
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

    # Suggestions only
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

# === Meal Log Page


@app.route('/submit_meal', methods=['POST'])
def submit_meal():
    if 'user' not in session:
        return jsonify({"success": False, "error": "Not logged in"}), 401

    data = request.get_json()
    user_email = session['user']['email']

    meal_data = {
        "meal": data.get("meal"),
        "food": data.get("food"),
        "quantity": data.get("quantity"),
        "protein": float(data.get("protein", 0)),
        "carbs": float(data.get("carbs", 0)),
        "fats": float(data.get("fats", 0)),
        "fiber": float(data.get("fiber", 0))
    }

    save_meal_entry(user_email, meal_data)
    return jsonify({"success": True})

@app.route('/meal_log')
def macro_tracker():
    if 'user' not in session:
        return redirect(url_for('register_page'))
    
    meals = get_today_meals(session['user']['email'])
    return render_template("meal_log.html", user=session['user'], meals=meals)

@app.route('/get_today_meals')
def get_today_meals_route():
    if 'user' not in session:
        return jsonify([])

    email = session['user']['email']
    entries = get_today_meals(email)
    return jsonify(entries)

@app.route("/api/dashboard_nutrition")
def dashboard_nutrition():
    if 'user' not in session:
        return jsonify({"error": "Not logged in"}), 401

    user = get_user_by_email(session['user']['email'])
    weight = user.get("weight", 60)  # fallback default

    today_meals = get_today_meals(user['email'])

    totals = {"protein": 0, "carbs": 0, "fats": 0, "fiber": 0}
    for meal in today_meals:
        totals["protein"] += float(meal.get("protein", 0))
        totals["carbs"] += float(meal.get("carbs", 0))
        totals["fats"] += float(meal.get("fats", 0))
        totals["fiber"] += float(meal.get("fiber", 0))

    return jsonify({
        "weight": weight,
        "total": totals
    })
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('register_page'))
    return render_template('dashboard.html', user=session['user'])

# === Run the App
if __name__ == "__main__":
    app.run(debug=True)
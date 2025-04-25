from pymongo import MongoClient
from datetime import datetime
import os

# Connect to your MongoDB Atlas cluster
client = MongoClient("mongodb+srv://vandanwadhwa07:AllAboutCars%407@vandan.hbt0x2x.mongodb.net/?retryWrites=true&w=majority")

# Select database and collection
db = client["carecraze"]
users_collection = db["users"]
meals = db["meals"]

# === Save Meal Entry (with upsert-like logic) ===
def save_meal_entry(user_email, meal_data):
    today = datetime.now().strftime("%Y-%m-%d")

    query = {
        "user_email": user_email,
        "date": today,
        "meal": meal_data["meal"],
        "food": meal_data["food"]
    }

    existing = meals.find_one(query)

    if existing:
        # Add new values to existing ones
        updated_values = {
            "quantity": existing["quantity"] + meal_data["quantity"],
            "protein": existing["protein"] + meal_data["protein"],
            "carbs": existing["carbs"] + meal_data["carbs"],
            "fats": existing["fats"] + meal_data["fats"],
            "fiber": existing["fiber"] + meal_data["fiber"],
            "timestamp": datetime.now()
        }
        meals.update_one(query, {"$set": updated_values})
    else:
        # Insert new meal entry
        meal_data["user_email"] = user_email
        meal_data["date"] = today
        meal_data["timestamp"] = datetime.now()
        meals.insert_one(meal_data)

# === Get Today's Meals for User ===
def get_today_meals(user_email):
    today = datetime.now().strftime("%Y-%m-%d")
    return list(meals.find({
        "user_email": user_email,
        "date": today
    }))

# === Register a new user ===
def register_user(user_data):
    existing = users_collection.find_one({"email": user_data["email"]})
    if existing:
        return False
    users_collection.insert_one(user_data)
    return True

# === Get user by email (used for login) ===
def get_user_by_email(email):
    return users_collection.find_one({"email": email})
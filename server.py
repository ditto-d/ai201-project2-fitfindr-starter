"""
server.py — Flask API backend for FitFindr
Run with: python server.py
Then open http://localhost:5000
"""
from flask import Flask, request, jsonify, send_from_directory
import os, sys

# Make sure your project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent import run_agent
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

app = Flask(__name__, static_folder="static")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")

@app.route("/search", methods=["POST"])
def search():
    data = request.get_json()
    query = data.get("query", "").strip()
    use_wardrobe = data.get("wardrobe", True)

    if not query:
        return jsonify({"error": "Please enter a search query."}), 400

    wardrobe = get_example_wardrobe() if use_wardrobe else get_empty_wardrobe()
    session = run_agent(query, wardrobe)

    if session.get("error"):
        return jsonify({"error": session["error"]}), 404

    item = session["selected_item"]
    return jsonify({
        "listing": {
            "title": item["title"],
            "price": item["price"],
            "size": item["size"],
            "condition": item["condition"],
            "platform": item["platform"],
            "brand": item.get("brand") or "Unknown",
            "description": item["description"],
        },
        "price_analysis": session["price_analysis"],
        "outfit": session["outfit_suggestion"],
        "fit_card": session["fit_card"],
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)
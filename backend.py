from flask import Flask, jsonify, request
from flask_cors import CORS
import database

app = Flask(__name__)
CORS(app)

# Initialize DB on startup
database.init_db()

@app.route("/api/items", methods=["GET"])
def list_items():
    q = request.args.get("q")
    data = database.search_items(q) if q else database.get_all_items()
    return jsonify(data), 200

@app.route("/api/items", methods=["POST"])
def create_item():
    d = request.json or {}
    if not d.get("title"):
        return jsonify({"error": "Title is required"}), 400
    
    new_item = database.add_item(
        title=d.get("title"),
        creator=d.get("creator", "Unknown"),
        category=d.get("category", "General"),
        date=d.get("date"),
        description=d.get("description", "")
    )
    return jsonify(new_item), 201

@app.route("/api/items/<int:item_id>", methods=["GET"])
def get_item(item_id):
    item = database.get_item_by_id(item_id)
    return (jsonify(item), 200) if item else (jsonify({"error": "Not found"}), 404)

@app.route("/api/items/<int:item_id>", methods=["PUT"])
def update_item(item_id):
    success = database.update_item(item_id, request.json)
    return (jsonify({"msg": "Updated"}), 200) if success else (jsonify({"error": "Failed"}), 400)

@app.route("/api/items/<int:item_id>", methods=["DELETE"])
def delete_item(item_id):
    success = database.delete_item(item_id)
    return (jsonify({"msg": "Deleted"}), 200) if success else (jsonify({"error": "Not found"}), 404)

@app.route("/api/items/<int:item_id>/borrow", methods=["POST"])
def borrow(item_id):
    borrower = request.json.get("borrower")
    if not borrower: return jsonify({"error": "Borrower name missing"}), 400
    ok, msg = database.borrow_item(item_id, borrower)
    return (jsonify({"msg": msg}), 200) if ok else (jsonify({"error": msg}), 400)

@app.route("/api/items/<int:item_id>/return", methods=["POST"])
def return_it(item_id):
    ok, msg = database.return_item(item_id)
    return (jsonify({"msg": msg}), 200) if ok else (jsonify({"error": msg}), 400)

@app.route("/api/items/<int:item_id>/history", methods=["GET"])
def history(item_id):
    return jsonify(database.get_history(item_id)), 200

if __name__ == "__main__":
    app.run(port=5000, debug=True)
# app/app.py
from flask import Flask, request, jsonify
from models import db, Item
from redis_client import cache 
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/cruddb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()
    print("Database tables created")

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

@app.route('/items', methods=['POST'])
def create_item():
    data = request.get_json()
    
    if not data or not data.get('name') or not data.get('price'):
        return jsonify({"error": "Name and price are required"}), 400
    
    new_item = Item(
        name=data['name'],
        description=data.get('description', ''),
        price=data['price']
    )
    
    db.session.add(new_item)
    db.session.commit()
    
    cache.invalidate('items')
    
    return jsonify(new_item.to_dict()), 201

@app.route('/items', methods=['GET'])
def get_items():
    items_list = cache.get_or_set(
        'items',
        lambda: [item.to_dict() for item in Item.query.all()],
        timeout=300
    )
    
    return jsonify(items_list), 200

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    item_data = cache.get_or_set(
        'item',
        lambda: Item.query.get(item_id).to_dict() if Item.query.get(item_id) else None,
        item_id=item_id,
        timeout=300
    )
    
    if not item_data:
        return jsonify({"error": "Item not found"}), 404
    
    return jsonify(item_data), 200

@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    data = request.get_json()
    
    if 'name' in data:
        item.name = data['name']
    if 'description' in data:
        item.description = data['description']
    if 'price' in data:
        item.price = data['price']
    
    db.session.commit()
    
    cache.invalidate('items', item_id)
    
    return jsonify(item.to_dict()), 200

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    cache.invalidate('items', item_id)
    
    return jsonify({"message": "Item deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
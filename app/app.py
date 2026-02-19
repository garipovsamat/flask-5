from flask import Flask, request, jsonify
from models import db, Item
import redis
import json
import os

app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/cruddb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Redis configuration
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST', 'redis'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    db=0,
    decode_responses=True
)

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()

# Helper function to get cache key
def get_cache_key(endpoint, item_id=None):
    if item_id:
        return f"{endpoint}:{item_id}"
    return endpoint

# Routes
@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200

# Create item
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
    
    # Invalidate cache for items list
    redis_client.delete(get_cache_key('items'))
    
    return jsonify(new_item.to_dict()), 201

# Get all items (with caching)
@app.route('/items', methods=['GET'])
def get_items():
    cache_key = get_cache_key('items')
    
    # Try to get from cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify(json.loads(cached_data)), 200
    
    # If not in cache, get from database
    items = Item.query.all()
    items_list = [item.to_dict() for item in items]
    
    # Store in cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(items_list))
    
    return jsonify(items_list), 200

# Get single item (with caching)
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    cache_key = get_cache_key('item', item_id)
    
    # Try to get from cache
    cached_data = redis_client.get(cache_key)
    if cached_data:
        return jsonify(json.loads(cached_data)), 200
    
    # If not in cache, get from database
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    # Store in cache for 5 minutes
    redis_client.setex(cache_key, 300, json.dumps(item.to_dict()))
    
    return jsonify(item.to_dict()), 200

# Update item
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
    
    # Invalidate caches
    redis_client.delete(get_cache_key('items'))
    redis_client.delete(get_cache_key('item', item_id))
    
    return jsonify(item.to_dict()), 200

# Delete item
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    # Invalidate caches
    redis_client.delete(get_cache_key('items'))
    redis_client.delete(get_cache_key('item', item_id))
    
    return jsonify({"message": "Item deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import Flask, request, jsonify
from models import db, Item
import redis
import json
import os

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@db:5432/cruddb')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

redis_client = None
try:
    redis_client = redis.Redis(
        host='redis_cache',
        port=6379,
        db=0,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    redis_client.ping()
    print("Redis connected successfully")
except Exception as e:
    print(f"Redis connection failed: {e}")
    redis_client = None

db.init_app(app)

with app.app_context():
    db.create_all()
    print("Database tables created")

def get_cache_key(endpoint, item_id=None):
    if item_id:
        return f"{endpoint}:{item_id}"
    return endpoint

def get_from_cache(key):
    if redis_client:
        try:
            data = redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            print(f"Redis get error: {e}")
    return None

def set_in_cache(key, data, timeout=300):
    if redis_client:
        try:
            redis_client.setex(key, timeout, json.dumps(data))
        except Exception as e:
            print(f"Redis set error: {e}")

def delete_from_cache(key):
    if redis_client:
        try:
            redis_client.delete(key)
        except Exception as e:
            print(f"Redis delete error: {e}")

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
    
    delete_from_cache(get_cache_key('items'))
    
    return jsonify(new_item.to_dict()), 201

@app.route('/items', methods=['GET'])
def get_items():
    cache_key = get_cache_key('items')
    
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return jsonify(cached_data), 200
    
    items = Item.query.all()
    items_list = [item.to_dict() for item in items]
    
    set_in_cache(cache_key, items_list, 300)
    
    return jsonify(items_list), 200

@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    cache_key = get_cache_key('item', item_id)
    
    cached_data = get_from_cache(cache_key)
    if cached_data:
        return jsonify(cached_data), 200
    
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    set_in_cache(cache_key, item.to_dict(), 300)
    
    return jsonify(item.to_dict()), 200

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
    
    delete_from_cache(get_cache_key('items'))
    delete_from_cache(get_cache_key('item', item_id))
    
    return jsonify(item.to_dict()), 200

@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    item = Item.query.get(item_id)
    if not item:
        return jsonify({"error": "Item not found"}), 404
    
    db.session.delete(item)
    db.session.commit()
    
    delete_from_cache(get_cache_key('items'))
    delete_from_cache(get_cache_key('item', item_id))
    
    return jsonify({"message": "Item deleted successfully"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
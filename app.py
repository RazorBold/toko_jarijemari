# app.py - JariJemari Handmade Shop Backend
import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, jsonify, request, g

app = Flask(__name__)
app.config['SECRET_KEY'] = 'jarijemari_secret_2026!'
DATABASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'jarijemari.db')

# ──────────────────────────────────────────────
# Database Helper Functions
# ──────────────────────────────────────────────
def get_db():
    """Open a database connection for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception):
    """Close database connection at the end of request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Initialize the database with schema and seed data."""
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    cursor = db.cursor()

    # Create tables
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            emoji TEXT DEFAULT '🧶',
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT NOT NULL UNIQUE,
            description TEXT,
            price REAL NOT NULL,
            sale_price REAL,
            category_id INTEGER,
            image_url TEXT,
            badge TEXT,
            is_featured INTEGER DEFAULT 0,
            is_available INTEGER DEFAULT 1,
            stock INTEGER DEFAULT 10,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        );

        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            customer_name TEXT NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            customer_email TEXT,
            customer_phone TEXT NOT NULL,
            customer_address TEXT NOT NULL,
            total_amount REAL NOT NULL,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            price REAL NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS testimonials (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            avatar_emoji TEXT DEFAULT '🐰',
            comment TEXT NOT NULL,
            rating INTEGER DEFAULT 5,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')

    # Check if data already seeded
    existing = cursor.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
    if existing == 0:
        # Seed categories
        categories = [
            ('Rajutan', 'rajutan', '🧶', 'Produk rajut handmade yang lembut dan menggemaskan'),
            ('Bordir', 'bordir', '🪡', 'Aksesoris dengan bordiran cantik dan detail'),
            ('Clay & Frame', 'clay-frame', '🎨', 'Bingkai foto & dekorasi dari clay handmade'),
            ('Buket & Gift', 'buket-gift', '💐', 'Buket rajut dan paket hadiah spesial'),
            ('Aksesoris', 'aksesoris', '✨', 'Aksesoris imut untuk sehari-hari'),
        ]
        cursor.executemany(
            'INSERT INTO categories (name, slug, emoji, description) VALUES (?, ?, ?, ?)',
            categories
        )

        # Seed products
        products = [
            ('Bunny Keychain', 'bunny-keychain', 
             'Gantungan kunci kelinci rajut yang super menggemaskan! Terbuat dari benang katun premium dengan detail wajah yang adorable. Cocok untuk hadiah atau koleksi pribadi 🐰',
             45000, 35000, 1, '/static/images/product_bunny_keychain.png', 'SALE', 1, 1, 25),
            ('Tote Bag Bordir Bunga', 'tote-bag-bordir',
             'Tote bag kanvas dengan bordiran bunga-bunga cantik. Setiap jahitan dibuat dengan penuh cinta dan ketelitian. Perfect untuk daily use! 🌸',
             185000, None, 2, '/static/images/product_tote_bag.png', 'NEW', 1, 1, 10),
            ('Bucket Hat Rajut Awan', 'bucket-hat-rajut',
             'Bucket hat rajut dengan motif awan kawaii. Hangat, nyaman, dan bikin kamu makin imut! Dibuat dari benang akrilik lembut 🌤️',
             95000, 79000, 1, '/static/images/product_bucket_hat.png', 'BEST', 1, 1, 15),
            ('Buket Bunga Rajut', 'buket-bunga-rajut',
             'Buket bunga rajut yang tidak akan pernah layu! Terdiri dari mawar, daisy, dan bunga-bunga cantik dalam warna pastel. Gift yang sempurna 💐',
             250000, None, 4, '/static/images/product_flower_bouquet.png', 'POPULAR', 1, 1, 8),
            ('Scrunchie Bordir Set', 'scrunchie-bordir',
             'Set 3 scrunchie dengan bordiran bunga mini. Tersedia dalam warna biru, putih, dan pink. Lembut di rambut dan cantik banget! 🎀',
             65000, 55000, 2, '/static/images/product_scrunchie.png', 'SALE', 1, 1, 30),
            ('Phone Case Rajut Bear', 'phone-case-bear',
             'Pouch HP rajut dengan motif beruang kawaii. Melindungi HP kamu dengan penuh gaya! Cocok untuk berbagai ukuran HP 🐻',
             75000, None, 1, '/static/images/product_phone_case.png', None, 0, 1, 20),
            ('Clay Photo Frame Bunga', 'clay-photo-frame',
             'Bingkai foto dari clay yang dihias dengan bunga-bunga dan bintang mini. Setiap frame unik karena 100% handmade! Ukuran foto 4x6 📸',
             120000, 99000, 3, '/static/images/product_photo_frame.png', 'SALE', 1, 1, 12),
            ('Coin Purse Daisy', 'coin-purse-daisy',
             'Dompet koin rajut dengan hiasan bunga daisy. Ada tali pergelangan tangan dan resleting. Mungil, praktis, dan super cute! 🌼',
             55000, None, 5, '/static/images/product_coin_purse.png', 'NEW', 0, 1, 18),
        ]
        cursor.executemany(
            '''INSERT INTO products 
               (name, slug, description, price, sale_price, category_id, image_url, badge, is_featured, is_available, stock)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            products
        )

        # Seed testimonials
        testimonials = [
            ('Dinda', '🐰', 'Bunny keychain-nya gemessss banget! Rapih banget rajutannya, langsung beli 3 buat temen-temen 💕', 5),
            ('Rika', '🌸', 'Tote bag bordirnya cantik parah, semua orang nanya beli dimana. Thank you JariJemari! ✨', 5),
            ('Maya', '🧸', 'Buket bunganya awet dan cantik banget, pacar aku suka banget dikasih ini 🥰', 5),
            ('Ayu', '🎀', 'Scrunchie-nya lembut dan bordirnya detail banget. Worth it sih harganya!', 5),
            ('Sarah', '☁️', 'Bucket hat-nya lucu banget dipake, banyak yang muji. Bahannya juga nyaman!', 5),
            ('Nisa', '🌼', 'Coin purse daisy-nya imut banget! Pas buat taruh koin dan lipstick mini 💖', 4),
        ]
        cursor.executemany(
            'INSERT INTO testimonials (customer_name, avatar_emoji, comment, rating) VALUES (?, ?, ?, ?)',
            testimonials
        )

    db.commit()
    db.close()

# ──────────────────────────────────────────────
# Page Routes
# ──────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')

# ──────────────────────────────────────────────
# API Routes - Products
# ──────────────────────────────────────────────
@app.route('/api/products', methods=['GET'])
def api_get_products():
    """Get all products with optional filtering."""
    db = get_db()
    category = request.args.get('category')
    featured = request.args.get('featured')
    search = request.args.get('search')
    sort = request.args.get('sort', 'newest')

    query = '''
        SELECT p.*, c.name as category_name, c.slug as category_slug
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.is_available = 1
    '''
    params = []

    if category:
        query += ' AND c.slug = ?'
        params.append(category)
    if featured:
        query += ' AND p.is_featured = 1'
    if search:
        query += ' AND (p.name LIKE ? OR p.description LIKE ?)'
        params.extend([f'%{search}%', f'%{search}%'])

    if sort == 'price_low':
        query += ' ORDER BY COALESCE(p.sale_price, p.price) ASC'
    elif sort == 'price_high':
        query += ' ORDER BY COALESCE(p.sale_price, p.price) DESC'
    elif sort == 'name':
        query += ' ORDER BY p.name ASC'
    else:
        query += ' ORDER BY p.created_at DESC'

    products = db.execute(query, params).fetchall()
    result = []
    for p in products:
        result.append({
            'id': p['id'],
            'name': p['name'],
            'slug': p['slug'],
            'description': p['description'],
            'price': p['price'],
            'sale_price': p['sale_price'],
            'category': p['category_name'],
            'category_slug': p['category_slug'],
            'image_url': p['image_url'],
            'badge': p['badge'],
            'is_featured': bool(p['is_featured']),
            'stock': p['stock'],
        })

    return jsonify({'success': True, 'data': result, 'count': len(result)})

@app.route('/api/products/<slug>', methods=['GET'])
def api_get_product(slug):
    """Get single product by slug."""
    db = get_db()
    product = db.execute('''
        SELECT p.*, c.name as category_name
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.slug = ?
    ''', [slug]).fetchone()

    if not product:
        return jsonify({'success': False, 'error': 'Produk tidak ditemukan'}), 404

    # Get reviews
    reviews = db.execute(
        'SELECT * FROM reviews WHERE product_id = ? ORDER BY created_at DESC',
        [product['id']]
    ).fetchall()

    return jsonify({
        'success': True,
        'data': {
            'id': product['id'],
            'name': product['name'],
            'slug': product['slug'],
            'description': product['description'],
            'price': product['price'],
            'sale_price': product['sale_price'],
            'category': product['category_name'],
            'image_url': product['image_url'],
            'badge': product['badge'],
            'stock': product['stock'],
            'reviews': [{'name': r['customer_name'], 'rating': r['rating'], 'comment': r['comment']} for r in reviews]
        }
    })

# ──────────────────────────────────────────────
# API Routes - Categories
# ──────────────────────────────────────────────
@app.route('/api/categories', methods=['GET'])
def api_get_categories():
    """Get all categories with product count."""
    db = get_db()
    categories = db.execute('''
        SELECT c.*, COUNT(p.id) as product_count
        FROM categories c
        LEFT JOIN products p ON c.id = p.category_id AND p.is_available = 1
        GROUP BY c.id
        ORDER BY c.name
    ''').fetchall()

    return jsonify({
        'success': True,
        'data': [{
            'id': c['id'],
            'name': c['name'],
            'slug': c['slug'],
            'emoji': c['emoji'],
            'description': c['description'],
            'product_count': c['product_count']
        } for c in categories]
    })

# ──────────────────────────────────────────────
# API Routes - Testimonials
# ──────────────────────────────────────────────
@app.route('/api/testimonials', methods=['GET'])
def api_get_testimonials():
    """Get all testimonials."""
    db = get_db()
    testimonials = db.execute(
        'SELECT * FROM testimonials ORDER BY created_at DESC'
    ).fetchall()

    return jsonify({
        'success': True,
        'data': [{
            'id': t['id'],
            'name': t['customer_name'],
            'avatar': t['avatar_emoji'],
            'comment': t['comment'],
            'rating': t['rating']
        } for t in testimonials]
    })

# ──────────────────────────────────────────────
# API Routes - Orders
# ──────────────────────────────────────────────
@app.route('/api/orders', methods=['POST'])
def api_create_order():
    """Create a new order."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Data tidak valid'}), 400

    required = ['customer_name', 'customer_phone', 'customer_address', 'items']
    for field in required:
        if field not in data:
            return jsonify({'success': False, 'error': f'{field} harus diisi'}), 400

    db = get_db()
    total = 0
    items_data = []

    for item in data['items']:
        product = db.execute('SELECT * FROM products WHERE id = ?', [item['product_id']]).fetchone()
        if not product:
            return jsonify({'success': False, 'error': f'Produk ID {item["product_id"]} tidak ditemukan'}), 404

        price = product['sale_price'] if product['sale_price'] else product['price']
        qty = item.get('quantity', 1)
        total += price * qty
        items_data.append((item['product_id'], qty, price))

    cursor = db.execute(
        '''INSERT INTO orders (customer_name, customer_email, customer_phone, customer_address, total_amount, notes)
           VALUES (?, ?, ?, ?, ?, ?)''',
        [data['customer_name'], data.get('customer_email', ''), data['customer_phone'],
         data['customer_address'], total, data.get('notes', '')]
    )
    order_id = cursor.lastrowid

    for product_id, qty, price in items_data:
        db.execute(
            'INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)',
            [order_id, product_id, qty, price]
        )
        db.execute('UPDATE products SET stock = stock - ? WHERE id = ?', [qty, product_id])

    db.commit()

    return jsonify({
        'success': True,
        'data': {
            'order_id': order_id,
            'total': total,
            'message': 'Pesanan berhasil dibuat! Terima kasih 💕'
        }
    }), 201

# ──────────────────────────────────────────────
# API Routes - Reviews
# ──────────────────────────────────────────────
@app.route('/api/reviews', methods=['POST'])
def api_create_review():
    """Create a new review for a product."""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'error': 'Data tidak valid'}), 400

    db = get_db()
    db.execute(
        'INSERT INTO reviews (product_id, customer_name, rating, comment) VALUES (?, ?, ?, ?)',
        [data['product_id'], data['customer_name'], data['rating'], data.get('comment', '')]
    )
    db.commit()

    return jsonify({'success': True, 'message': 'Review berhasil ditambahkan! ✨'}), 201

# ──────────────────────────────────────────────
# API Routes - Stats (for fun)
# ──────────────────────────────────────────────
@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """Get shop statistics."""
    db = get_db()
    products_count = db.execute('SELECT COUNT(*) FROM products WHERE is_available = 1').fetchone()[0]
    categories_count = db.execute('SELECT COUNT(*) FROM categories').fetchone()[0]
    orders_count = db.execute('SELECT COUNT(*) FROM orders').fetchone()[0]

    return jsonify({
        'success': True,
        'data': {
            'products': products_count,
            'categories': categories_count,
            'orders': orders_count,
            'happy_customers': 500 + orders_count
        }
    })


# ──────────────────────────────────────────────
# Initialize & Run
# ──────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    print("🧶 JariJemari server is running!")
    print("🌐 Open http://localhost:5008")
    app.run(debug=True, port=5008)
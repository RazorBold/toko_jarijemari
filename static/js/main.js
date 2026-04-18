/* ═══════════════════════════════════════════════
   JariJemari - Main JavaScript
   Handles: Products, Cart, UI interactions
   ═══════════════════════════════════════════════ */

// ── State Management ──
const state = {
    products: [],
    categories: [],
    testimonials: [],
    cart: JSON.parse(localStorage.getItem('jj_cart') || '[]'),
    activeCategory: 'all',
    searchQuery: '',
    sortBy: 'newest'
};

// ── DOM Ready ──
document.addEventListener('DOMContentLoaded', () => {
    initNavbar();
    loadCategories();
    loadProducts();
    loadTestimonials();
    loadStats();
    initScrollAnimations();
    updateCartUI();
});

// ══════════════════════════════════════
// NAVBAR
// ══════════════════════════════════════
function initNavbar() {
    const navbar = document.querySelector('.navbar');
    const toggle = document.getElementById('navbar-toggle');
    const menu = document.getElementById('navbar-menu');

    // Scroll effect
    window.addEventListener('scroll', () => {
        navbar.classList.toggle('scrolled', window.scrollY > 50);
    });

    // Mobile menu toggle
    if (toggle) {
        toggle.addEventListener('click', () => {
            menu.classList.toggle('open');
            toggle.textContent = menu.classList.contains('open') ? '✕' : '☰';
        });
    }

    // Smooth scroll for nav links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({ behavior: 'smooth', block: 'start' });
                if (menu) menu.classList.remove('open');
                if (toggle) toggle.textContent = '☰';
            }
        });
    });
}

// ══════════════════════════════════════
// API CALLS
// ══════════════════════════════════════
async function loadCategories() {
    try {
        const res = await fetch('/api/categories');
        const json = await res.json();
        if (json.success) {
            state.categories = json.data;
            renderCategories();
        }
    } catch (err) {
        console.error('Failed to load categories:', err);
    }
}

async function loadProducts() {
    try {
        let url = '/api/products?';
        if (state.activeCategory !== 'all') url += `category=${state.activeCategory}&`;
        if (state.searchQuery) url += `search=${encodeURIComponent(state.searchQuery)}&`;
        url += `sort=${state.sortBy}`;

        const res = await fetch(url);
        const json = await res.json();
        if (json.success) {
            state.products = json.data;
            renderProducts();
        }
    } catch (err) {
        console.error('Failed to load products:', err);
    }
}

async function loadTestimonials() {
    try {
        const res = await fetch('/api/testimonials');
        const json = await res.json();
        if (json.success) {
            state.testimonials = json.data;
            renderTestimonials();
        }
    } catch (err) {
        console.error('Failed to load testimonials:', err);
    }
}

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        const json = await res.json();
        if (json.success) {
            animateCounter('stat-products', json.data.products);
            animateCounter('stat-customers', json.data.happy_customers);
            animateCounter('stat-handmade', 100);
        }
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ══════════════════════════════════════
// RENDER FUNCTIONS
// ══════════════════════════════════════
function renderCategories() {
    const grid = document.getElementById('categories-grid');
    if (!grid) return;

    let html = `
        <div class="category-card ${state.activeCategory === 'all' ? 'active' : ''}" 
             onclick="filterCategory('all')">
            <span class="category-emoji">✨</span>
            <div class="category-name">Semua</div>
            <div class="category-count">${state.categories.reduce((sum, c) => sum + c.product_count, 0)} produk</div>
        </div>
    `;

    state.categories.forEach(cat => {
        html += `
            <div class="category-card ${state.activeCategory === cat.slug ? 'active' : ''}" 
                 onclick="filterCategory('${cat.slug}')">
                <span class="category-emoji">${cat.emoji}</span>
                <div class="category-name">${cat.name}</div>
                <div class="category-count">${cat.product_count} produk</div>
            </div>
        `;
    });

    grid.innerHTML = html;
}

function renderProducts() {
    const grid = document.getElementById('products-grid');
    if (!grid) return;

    if (state.products.length === 0) {
        grid.innerHTML = `
            <div style="grid-column: 1/-1; text-align: center; padding: 60px 20px;" class="animate-on-scroll visible">
                <div style="font-size: 4rem; margin-bottom: 16px;">🔍</div>
                <h3 style="color: var(--text-light); font-weight: 600;">Produk tidak ditemukan</h3>
                <p style="color: var(--text-muted);">Coba cari dengan kata kunci lain ya~ ✨</p>
            </div>
        `;
        return;
    }

    let html = '';
    state.products.forEach((product, index) => {
        const price = product.sale_price || product.price;
        const discount = product.sale_price 
            ? Math.round((1 - product.sale_price / product.price) * 100) 
            : 0;

        let badgeClass = '';
        if (product.badge) {
            badgeClass = `badge-${product.badge.toLowerCase()}`;
        }

        html += `
            <div class="product-card animate-on-scroll" style="animation-delay: ${index * 0.08}s" 
                 onclick="openProductModal('${product.slug}')">
                <div class="product-image">
                    <img src="${product.image_url}" alt="${product.name}" loading="lazy">
                    ${product.badge ? `<span class="product-badge ${badgeClass}">${product.badge}</span>` : ''}
                    <button class="product-wishlist" onclick="event.stopPropagation(); toggleWishlist(${product.id})">🤍</button>
                    <div class="product-quick-add">
                        <button class="quick-add-btn" onclick="event.stopPropagation(); addToCart(${product.id})">
                            🛒 Tambah ke Keranjang
                        </button>
                    </div>
                </div>
                <div class="product-info">
                    <div class="product-category">${product.category || ''}</div>
                    <h3 class="product-name">${product.name}</h3>
                    <div class="product-price">
                        <span class="price-current">Rp ${formatPrice(price)}</span>
                        ${product.sale_price ? `
                            <span class="price-original">Rp ${formatPrice(product.price)}</span>
                            <span class="price-discount">-${discount}%</span>
                        ` : ''}
                    </div>
                </div>
            </div>
        `;
    });

    grid.innerHTML = html;
    initScrollAnimations();
}

function renderTestimonials() {
    const slider = document.getElementById('testimonials-slider');
    if (!slider) return;

    let html = '';
    state.testimonials.forEach(t => {
        const stars = '★'.repeat(t.rating) + '☆'.repeat(5 - t.rating);
        html += `
            <div class="testimonial-card">
                <div class="testimonial-avatar">${t.avatar}</div>
                <div class="testimonial-stars">${stars}</div>
                <p class="testimonial-text">"${t.comment}"</p>
                <div class="testimonial-name">— ${t.name}</div>
            </div>
        `;
    });

    slider.innerHTML = html;
}

// ══════════════════════════════════════
// FILTERING & SORTING
// ══════════════════════════════════════
function filterCategory(slug) {
    state.activeCategory = slug;
    loadProducts();
    renderCategories();
    
    // Scroll to products
    document.getElementById('products').scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function handleSearch(value) {
    state.searchQuery = value;
    clearTimeout(window._searchTimeout);
    window._searchTimeout = setTimeout(() => loadProducts(), 300);
}

function handleSort(value) {
    state.sortBy = value;
    loadProducts();
}

// ══════════════════════════════════════
// PRODUCT MODAL
// ══════════════════════════════════════
async function openProductModal(slug) {
    const modal = document.getElementById('product-modal');
    if (!modal) return;

    try {
        const res = await fetch(`/api/products/${slug}`);
        const json = await res.json();
        if (!json.success) return;

        const product = json.data;
        const price = product.sale_price || product.price;
        const discount = product.sale_price 
            ? Math.round((1 - product.sale_price / product.price) * 100) 
            : 0;

        document.getElementById('modal-image').src = product.image_url;
        document.getElementById('modal-image').alt = product.name;
        document.getElementById('modal-category').textContent = product.category || '';
        document.getElementById('modal-title').textContent = product.name;
        document.getElementById('modal-desc').textContent = product.description;
        document.getElementById('modal-stock-text').textContent = `Stok tersedia: ${product.stock} pcs`;
        document.getElementById('modal-qty').textContent = '1';
        document.getElementById('modal-qty').dataset.productId = product.id;
        document.getElementById('modal-qty').dataset.max = product.stock;

        let priceHTML = `<span class="price-current" style="font-size:1.5rem">Rp ${formatPrice(price)}</span>`;
        if (product.sale_price) {
            priceHTML += `<span class="price-original">Rp ${formatPrice(product.price)}</span>`;
            priceHTML += `<span class="price-discount">-${discount}%</span>`;
        }
        document.getElementById('modal-price').innerHTML = priceHTML;

        // WhatsApp link
        const waText = encodeURIComponent(`Halo JariJemari! 🧶\nSaya tertarik dengan produk: ${product.name}\nHarga: Rp ${formatPrice(price)}\n\nApakah masih tersedia?`);
        document.getElementById('modal-wa-btn').href = `https://wa.me/6281234567890?text=${waText}`;

        modal.classList.add('active');
        document.body.style.overflow = 'hidden';
    } catch (err) {
        console.error('Failed to load product detail:', err);
    }
}

function closeProductModal() {
    const modal = document.getElementById('product-modal');
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

function changeQty(delta) {
    const qtyEl = document.getElementById('modal-qty');
    let qty = parseInt(qtyEl.textContent);
    const max = parseInt(qtyEl.dataset.max) || 99;
    qty = Math.max(1, Math.min(max, qty + delta));
    qtyEl.textContent = qty;
}

function addToCartFromModal() {
    const qtyEl = document.getElementById('modal-qty');
    const productId = parseInt(qtyEl.dataset.productId);
    const qty = parseInt(qtyEl.textContent);
    addToCart(productId, qty);
    closeProductModal();
}

// ══════════════════════════════════════
// CART FUNCTIONALITY
// ══════════════════════════════════════
function addToCart(productId, qty = 1) {
    const product = state.products.find(p => p.id === productId);
    if (!product) return;

    const existing = state.cart.find(item => item.id === productId);
    if (existing) {
        existing.qty += qty;
    } else {
        state.cart.push({
            id: product.id,
            name: product.name,
            price: product.sale_price || product.price,
            image: product.image_url,
            qty: qty
        });
    }

    saveCart();
    updateCartUI();
    showToast(`${product.name} ditambahkan ke keranjang! 🛒`);
}

function removeFromCart(productId) {
    state.cart = state.cart.filter(item => item.id !== productId);
    saveCart();
    updateCartUI();
    renderCartItems();
}

function updateCartItemQty(productId, delta) {
    const item = state.cart.find(i => i.id === productId);
    if (!item) return;
    item.qty += delta;
    if (item.qty <= 0) {
        removeFromCart(productId);
        return;
    }
    saveCart();
    updateCartUI();
    renderCartItems();
}

function saveCart() {
    localStorage.setItem('jj_cart', JSON.stringify(state.cart));
}

function getCartTotal() {
    return state.cart.reduce((sum, item) => sum + item.price * item.qty, 0);
}

function getCartCount() {
    return state.cart.reduce((sum, item) => sum + item.qty, 0);
}

function updateCartUI() {
    const countEl = document.getElementById('cart-count');
    const totalEl = document.getElementById('cart-total-amount');
    if (countEl) countEl.textContent = getCartCount();
    if (totalEl) totalEl.textContent = `Rp ${formatPrice(getCartTotal())}`;
}

function toggleCart() {
    const sidebar = document.querySelector('.cart-sidebar');
    const overlay = document.querySelector('.cart-overlay');
    const isOpen = sidebar.classList.contains('open');

    sidebar.classList.toggle('open');
    overlay.classList.toggle('open');
    document.body.style.overflow = isOpen ? '' : 'hidden';

    if (!isOpen) renderCartItems();
}

function renderCartItems() {
    const container = document.getElementById('cart-items');
    if (!container) return;

    if (state.cart.length === 0) {
        container.innerHTML = `
            <div class="cart-empty">
                <span class="cart-empty-icon">🛒</span>
                <p>Keranjang masih kosong nih~</p>
                <p style="font-size: 0.85rem; margin-top: 8px;">Yuk jelajahi produk handmade kami! ✨</p>
            </div>
        `;
        return;
    }

    let html = '';
    state.cart.forEach(item => {
        html += `
            <div class="cart-item">
                <div class="cart-item-img">
                    <img src="${item.image}" alt="${item.name}">
                </div>
                <div class="cart-item-info">
                    <div class="cart-item-name">${item.name}</div>
                    <div class="cart-item-price">Rp ${formatPrice(item.price * item.qty)}</div>
                </div>
                <div class="cart-item-qty">
                    <button onclick="updateCartItemQty(${item.id}, -1)">−</button>
                    <span style="font-weight:700; font-size:0.9rem;">${item.qty}</span>
                    <button onclick="updateCartItemQty(${item.id}, 1)">+</button>
                    <button class="cart-item-remove" onclick="removeFromCart(${item.id})">✕</button>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
    updateCartUI();
}

function checkout() {
    if (state.cart.length === 0) {
        showToast('Keranjang masih kosong! 🛒');
        return;
    }

    // Build WhatsApp order message
    let message = '🧶 *Pesanan Baru dari JariJemari* 🧶\n\n';
    state.cart.forEach((item, i) => {
        message += `${i + 1}. ${item.name} x${item.qty} = Rp ${formatPrice(item.price * item.qty)}\n`;
    });
    message += `\n💰 *Total: Rp ${formatPrice(getCartTotal())}*\n\n`;
    message += 'Mohon konfirmasi pesanan ini ya~ 💕';

    const waUrl = `https://wa.me/6281234567890?text=${encodeURIComponent(message)}`;
    window.open(waUrl, '_blank');
}

// ══════════════════════════════════════
// WISHLIST (Visual only)
// ══════════════════════════════════════
function toggleWishlist(productId) {
    const btn = event.currentTarget;
    const isLiked = btn.textContent === '❤️';
    btn.textContent = isLiked ? '🤍' : '❤️';
    btn.style.transform = 'scale(1.3)';
    setTimeout(() => { btn.style.transform = ''; }, 300);
    
    if (!isLiked) {
        showToast('Ditambahkan ke wishlist! 💕');
    }
}

// ══════════════════════════════════════
// TOAST NOTIFICATIONS
// ══════════════════════════════════════
function showToast(message) {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `
        <span class="toast-icon">✨</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
}

// ══════════════════════════════════════
// UTILITY FUNCTIONS
// ══════════════════════════════════════
function formatPrice(num) {
    return Math.round(num).toLocaleString('id-ID');
}

function animateCounter(elementId, target) {
    const el = document.getElementById(elementId);
    if (!el) return;

    let current = 0;
    const step = Math.ceil(target / 50);
    const interval = setInterval(() => {
        current += step;
        if (current >= target) {
            current = target;
            clearInterval(interval);
        }
        el.textContent = current.toLocaleString('id-ID');
    }, 30);
}

// ══════════════════════════════════════
// SCROLL ANIMATIONS
// ══════════════════════════════════════
function initScrollAnimations() {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.animate-on-scroll').forEach(el => observer.observe(el));
}

// Parallax-like floating decorations on mouse move
document.addEventListener('mousemove', (e) => {
    const decos = document.querySelectorAll('.floating-deco');
    const x = (e.clientX / window.innerWidth - 0.5) * 20;
    const y = (e.clientY / window.innerHeight - 0.5) * 20;
    
    decos.forEach((deco, i) => {
        const factor = (i + 1) * 0.5;
        deco.style.transform = `translate(${x * factor}px, ${y * factor}px)`;
    });
});

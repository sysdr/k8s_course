import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

interface Product {
  id: string;
  name: string;
  description: string;
  price: number;
  stock: number;
  category: string;
}

interface OrderItem {
  product_id: string;
  quantity: number;
}

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function App() {
  const [products, setProducts] = useState<Product[]>([]);
  const [cart, setCart] = useState<OrderItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [orderStatus, setOrderStatus] = useState<string | null>(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/v1/products`);
      setProducts(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Failed to fetch products:', error);
      setLoading(false);
    }
  };

  const addToCart = (productId: string) => {
    const existingItem = cart.find(item => item.product_id === productId);
    
    if (existingItem) {
      setCart(cart.map(item =>
        item.product_id === productId
          ? { ...item, quantity: item.quantity + 1 }
          : item
      ));
    } else {
      setCart([...cart, { product_id: productId, quantity: 1 }]);
    }
  };

  const placeOrder = async () => {
    if (cart.length === 0) {
      alert('Cart is empty!');
      return;
    }

    try {
      setOrderStatus('Processing...');
      const response = await axios.post('http://localhost:8001/api/v1/orders', {
        user_id: 'demo-user',
        items: cart
      });
      
      setOrderStatus(`Order placed successfully! Order ID: ${response.data.id}`);
      setCart([]);
    } catch (error) {
      setOrderStatus('Order failed. Please try again.');
      console.error('Order failed:', error);
    }
  };

  if (loading) {
    return <div className="loading">Loading products...</div>;
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>E-Commerce Platform</h1>
        <p>Built with Kubernetes & Microservices</p>
      </header>

      <main className="main-content">
        <section className="products-section">
          <h2>Products</h2>
          <div className="products-grid">
            {products.map(product => (
              <div key={product.id} className="product-card">
                <h3>{product.name}</h3>
                <p className="description">{product.description}</p>
                <p className="price">${product.price.toFixed(2)}</p>
                <p className="stock">Stock: {product.stock}</p>
                <button 
                  onClick={() => addToCart(product.id)}
                  disabled={product.stock === 0}
                  className="add-to-cart-btn"
                  id="add-to-cart"
                >
                  Add to Cart
                </button>
              </div>
            ))}
          </div>
        </section>

        <aside className="cart-section">
          <h2>Shopping Cart</h2>
          {cart.length === 0 ? (
            <p>Cart is empty</p>
          ) : (
            <>
              <ul className="cart-items">
                {cart.map(item => {
                  const product = products.find(p => p.id === item.product_id);
                  return (
                    <li key={item.product_id}>
                      {product?.name} x {item.quantity}
                    </li>
                  );
                })}
              </ul>
              <button onClick={placeOrder} className="checkout-btn" id="checkout">
                Place Order
              </button>
            </>
          )}
          
          {orderStatus && (
            <div className="order-status order-confirmation">
              {orderStatus}
            </div>
          )}
        </aside>
      </main>
    </div>
  );
}

export default App;

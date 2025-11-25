import React from 'react';
import './ProductList.css';

function ProductList({ products }) {
  if (!products || products.length === 0) {
    return (
      <div className="products">
        <h2>📦 Products</h2>
        <p className="no-products">No products available</p>
      </div>
    );
  }

  return (
    <div className="products">
      <h2>📦 Products ({products.length})</h2>
      <div className="product-grid">
        {products.map(product => (
          <div key={product.id} className="product-card">
            <div className="product-header">
              <h3>{product.name}</h3>
              <span className="product-category">{product.category}</span>
            </div>
            <p className="product-description">{product.description}</p>
            <div className="product-footer">
              <span className="product-price">${product.price.toFixed(2)}</span>
              <span className="product-stock">Stock: {product.stock}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default ProductList;

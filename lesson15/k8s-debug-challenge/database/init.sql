-- Initialize e-commerce database with sample data

CREATE TABLE IF NOT EXISTS products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INTEGER NOT NULL DEFAULT 0,
    category VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert sample products
INSERT INTO products (name, description, price, stock, category) VALUES
('Laptop Pro 15"', 'High-performance laptop with 16GB RAM', 1299.99, 45, 'Electronics'),
('Wireless Mouse', 'Ergonomic wireless mouse with USB receiver', 29.99, 150, 'Electronics'),
('Office Chair', 'Comfortable ergonomic office chair', 249.99, 30, 'Furniture'),
('Desk Lamp', 'LED desk lamp with adjustable brightness', 39.99, 80, 'Furniture'),
('Coffee Maker', 'Programmable coffee maker with thermal carafe', 89.99, 60, 'Appliances'),
('Water Bottle', 'Insulated stainless steel water bottle', 24.99, 200, 'Accessories'),
('Backpack', 'Durable laptop backpack with multiple compartments', 59.99, 100, 'Accessories'),
('Headphones', 'Noise-cancelling over-ear headphones', 199.99, 75, 'Electronics'),
('Notebook Set', 'Set of 3 premium notebooks', 14.99, 250, 'Stationery'),
('Pen Collection', 'Professional pen collection (5 pens)', 34.99, 120, 'Stationery');

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ecommerce;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ecommerce;

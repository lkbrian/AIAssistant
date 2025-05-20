-- Create extension if not exists
CREATE EXTENSION IF NOT EXISTS vector;

-- Insert categories
INSERT INTO public.categories (name, description)
VALUES 
  ('Electronics', 'Latest gadgets and electronic devices'),
  ('Footwear', 'Comfortable and stylish shoes'),
  ('Apparel', 'Fashion clothing and accessories'),
  ('Home & Living', 'Home decor and furniture'),
  ('Sports & Fitness', 'Sports equipment and fitness gear');

-- Insert products
INSERT INTO public.products (name, description, price, category, stock, image_url, rating) 
VALUES 
  -- Original demo products
  ('Wireless Noise-Cancelling Headphones', 'Premium wireless headphones with active noise cancellation', 199.99, 1, 50, 'https://images.unsplash.com/photo-1505740420928-5e560c06d30e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Ultra-Light Running Shoes', 'Lightweight and comfortable running shoes for professional athletes', 89.99, 2, 75, 'https://images.unsplash.com/photo-1542291026-7eec264c27ff?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
  ('Premium Leather Sneakers', 'Classic leather sneakers with modern design', 129.99, 2, 60, 'https://images.unsplash.com/photo-1549298916-b41d501d3772?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Smart 4K TV', '55-inch 4K Ultra HD Smart TV with HDR', 699.99, 1, 30, 'https://images.unsplash.com/photo-1593359677879-a4bb92f829d1?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
  ('Casual Denim Jacket', 'Classic denim jacket with modern fit', 79.99, 3, 100, 'https://images.unsplash.com/photo-1576871337632-b9aef4c17ab9?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  
  -- Additional products
  ('Mechanical Gaming Keyboard', 'RGB mechanical keyboard with custom switches', 149.99, 1, 40, 'https://images.unsplash.com/photo-1511478156903-9aa2c6ac3459?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
  ('Wireless Gaming Mouse', 'High-precision wireless gaming mouse', 79.99, 1, 45, 'https://images.unsplash.com/photo-1527814050087-3793815479db?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Leather Hiking Boots', 'Waterproof leather hiking boots for outdoor adventures', 159.99, 2, 35, 'https://images.unsplash.com/photo-1520639888713-7851133b1ed0?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
  ('Smart Watch Series X', 'Advanced smartwatch with health monitoring', 299.99, 1, 55, 'https://images.unsplash.com/photo-1579586337278-3befd40fd17a?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Premium Yoga Mat', 'Eco-friendly non-slip yoga mat', 49.99, 5, 80, 'https://images.unsplash.com/photo-1601925260368-ae2f83cf8b7f?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
  ('Adjustable Dumbbell Set', 'Space-saving adjustable weight dumbbell set', 299.99, 5, 25, 'https://images.unsplash.com/photo-1638536532686-d610adfc8e5c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
  ('Modern Coffee Table', 'Minimalist wooden coffee table', 199.99, 4, 20, 'https://images.unsplash.com/photo-1532372320572-cda25653a26d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Designer Desk Lamp', 'Adjustable LED desk lamp with wireless charging', 89.99, 4, 40, 'https://images.unsplash.com/photo-1507473885765-e6ed057f782c?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Wool Blend Sweater', 'Comfortable wool blend sweater for winter', 69.99, 3, 65, 'https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Premium Backpack', 'Water-resistant laptop backpack with USB charging', 89.99, 3, 50, 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 5),
  ('Wireless Earbuds', 'True wireless earbuds with noise cancellation', 159.99, 1, 70, 'https://images.unsplash.com/photo-1605464315542-bda3e2f4e605?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Smart Home Hub', 'Central control for your smart home devices', 129.99, 1, 35, 'https://images.unsplash.com/photo-1558089687-f282ffcbc126?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4),
  ('Fitness Tracker', 'Advanced fitness and sleep tracking device', 79.99, 1, 60, 'https://images.unsplash.com/photo-1576243345690-4e4b79b63288?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80', 4);

-- Insert product images for each product
INSERT INTO public.product_images (product_id, url)
SELECT 
    id,
    image_url
FROM public.products;

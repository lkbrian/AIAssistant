-- Clear all existing data
TRUNCATE TABLE 
    entity_media,
    products, 
    food,
    accomodation,
    property,
    m_business,
    app_users,
    user_types,
    business_types,
    property_types,
    room_types,
    entity_media_types,
    categories CASCADE;

-- Reset all sequences
ALTER SEQUENCE user_types_id_seq RESTART WITH 1;
ALTER SEQUENCE business_types_id_seq RESTART WITH 1;
ALTER SEQUENCE property_types_id_seq RESTART WITH 1;
ALTER SEQUENCE room_types_id_seq RESTART WITH 1;
ALTER SEQUENCE categories_id_seq RESTART WITH 1;
ALTER SEQUENCE products_id_seq RESTART WITH 1;
ALTER SEQUENCE food_id_seq RESTART WITH 1;
ALTER SEQUENCE property_id_seq RESTART WITH 1;
ALTER SEQUENCE accomodation_id_seq RESTART WITH 1;
ALTER SEQUENCE entity_media_id_seq RESTART WITH 1;

-- Insert User Types
INSERT INTO user_types (name, description) VALUES
('admin', 'System administrator with full access'),
('business_owner', 'Owner of business accounts'),
('customer', 'Regular customer user');

-- Insert Business Types
INSERT INTO business_types (name, description) VALUES
('ecommerce', 'Online retail business'),
('restaurant', 'Food and beverage service'),
('property', 'Real estate and property management'),
('hotel', 'Accommodation and hospitality services');

-- Insert Property Types
INSERT INTO property_types (name, description) VALUES
('land', 'Undeveloped land parcels'),
('apartment', 'Residential apartments'),
('house', 'Residential houses'),
('commercial', 'Commercial properties'),
('villa', 'Luxury villas and mansions'),
('townhouse', 'Row houses and townhouses');

-- Insert Room Types
INSERT INTO room_types (name, description) VALUES
('single', 'Single occupancy room with basic amenities'),
('double', 'Double occupancy room with enhanced comfort'),
('suite', 'Luxury suite with premium amenities'),
('studio', 'Compact studio apartment style'),
('penthouse', 'Top-floor luxury accommodation'),
('villa', 'Standalone luxury accommodation');

-- Insert Categories
INSERT INTO categories (name, description) VALUES
-- Food Categories
('main_course', 'Primary dishes and entrees'),
('appetizers', 'Starters and small plates'),
('beverages', 'Drinks and refreshments'),
('desserts', 'Sweet dishes and treats'),
('breakfast', 'Morning meals and brunch items'),
('salads', 'Fresh salads and healthy options'),
('soups', 'Soups and broths'),
('sides', 'Side dishes and accompaniments'),
-- Product Categories
('electronics', 'Electronic devices and gadgets'),
('furniture', 'Home and office furniture'),
('fashion', 'Clothing and accessories'),
('beauty', 'Beauty and personal care'),
('sports', 'Sports equipment and gear'),
('books', 'Books and stationery'),
('home_appliances', 'Home and kitchen appliances'),
('toys', 'Toys and games');

-- Insert Users (20 business owners)
INSERT INTO app_users (id, first_name, middle_name, last_name, username, user_type_id, email, password, created_at) 
SELECT 
    'usr_' || LPAD(CAST(generate_series AS text), 3, '0'),
    (ARRAY['John','Jane','Michael','Sarah','David','Emma','James','Lisa','Robert','Mary','William','Elizabeth','Richard','Linda','Thomas','Patricia','Joseph','Jennifer','Charles','Margaret'])[generate_series],
    CASE WHEN random() < 0.5 THEN (ARRAY['A','B','C','D','E','F','G','H','I','J'])[floor(random()*10+1)] ELSE NULL END,
    (ARRAY['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin'])[generate_series],
    lower((ARRAY['John','Jane','Michael','Sarah','David','Emma','James','Lisa','Robert','Mary','William','Elizabeth','Richard','Linda','Thomas','Patricia','Joseph','Jennifer','Charles','Margaret'])[generate_series]) || 
    (ARRAY['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin'])[generate_series],
    2,
    lower((ARRAY['John','Jane','Michael','Sarah','David','Emma','James','Lisa','Robert','Mary','William','Elizabeth','Richard','Linda','Thomas','Patricia','Joseph','Jennifer','Charles','Margaret'])[generate_series]) || 
    '.' || 
    lower((ARRAY['Smith','Johnson','Williams','Brown','Jones','Garcia','Miller','Davis','Rodriguez','Martinez','Hernandez','Lopez','Gonzalez','Wilson','Anderson','Thomas','Taylor','Moore','Jackson','Martin'])[generate_series]) || 
    '@example.com',
    'hashed_password',
    NOW()
FROM generate_series(1, 20);

-- Insert Businesses (40 businesses, 2 per user on average)
INSERT INTO m_business (id, name, business_type_id, location, hospitality_type, phone_number, email, user_id)
SELECT 
    'biz_' || LPAD(CAST(generate_series AS text), 3, '0'),
    CASE 
        WHEN business_type = 1 THEN (ARRAY['Tech','Smart','Digital','Elite','Prime','Global','Metro','Urban','City','Modern'])[floor(random()*10+1)] || ' ' ||
                                   (ARRAY['Electronics','Gadgets','Mart','Store','Shop','Retail','Market','Emporium','Hub','Zone'])[floor(random()*10+1)]
        WHEN business_type = 2 THEN (ARRAY['Tasty','Delicious','Gourmet','Fresh','Royal','Golden','Silver','Crystal','Diamond','Pearl'])[floor(random()*10+1)] || ' ' ||
                                   (ARRAY['Bites','Kitchen','Restaurant','Cafe','Diner','Eatery','Bistro','Grill','Cuisine','Foods'])[floor(random()*10+1)]
        WHEN business_type = 3 THEN (ARRAY['Premium','Luxury','Elite','Royal','Prime','Global','Metro','Urban','City','Modern'])[floor(random()*10+1)] || ' ' ||
                                   (ARRAY['Properties','Homes','Estates','Realty','Housing','Living','Residences','Spaces','Habitat','Dwellings'])[floor(random()*10+1)]
        ELSE (ARRAY['Comfort','Luxury','Royal','Grand','Elite','Premium','Stellar','Divine','Majestic','Imperial'])[floor(random()*10+1)] || ' ' ||
             (ARRAY['Hotel','Suites','Resort','Inn','Lodge','Retreat','Haven','Oasis','Palace','Residency'])[floor(random()*10+1)]
    END,
    business_type,
    (ARRAY['Nairobi','Mombasa','Kisumu','Nakuru','Eldoret','Malindi','Naivasha','Nyeri','Machakos','Kitale'])[floor(random()*10+1)],
    CASE WHEN business_type = 2 OR business_type = 4 THEN floor(random()*3+1) ELSE NULL END,
    '+2547' || LPAD(CAST(floor(random()*100000000) AS text), 8, '0'),
    'business' || generate_series || '@example.com',
    'usr_' || LPAD(CAST(floor(random()*20+1) AS text), 3, '0')
FROM (
    SELECT generate_series, 
           CASE 
               WHEN generate_series <= 10 THEN 1  -- ecommerce
               WHEN generate_series <= 20 THEN 2  -- restaurant
               WHEN generate_series <= 30 THEN 3  -- property
               ELSE 4                            -- hotel
           END AS business_type
    FROM generate_series(1, 40)
) AS series;

-- Generate 400+ Properties
INSERT INTO property (
    business_id, property_type_id, name, description, 
    bedrooms, bathrooms, land_size, price, location, 
    status, year_built
)
SELECT 
    'biz_' || LPAD(CAST(floor(random() * 10 + 21) AS text), 3, '0'),  -- business_id (from property businesses)
    floor(random() * 6 + 1),  -- property_type_id (1-6)
    CASE floor(random() * 6 + 1)
        WHEN 1 THEN (ARRAY['Sunset','Riverside','Mountain','Lake','Ocean','Valley','Forest','City','Garden','Park'])[floor(random()*10+1)] || ' ' ||
                    (ARRAY['View','Heights','Meadows','Estate','Residences','Gardens','Plaza','Court','Place','Square'])[floor(random()*10+1)]
        WHEN 2 THEN (ARRAY['Modern','Luxury','Elite','Premium','Urban','Metro','Royal','Grand','Classic','Smart'])[floor(random()*10+1)] || ' ' ||
                    (ARRAY['Apartments','Towers','Suites','Lofts','Condos','Heights','Residence','Living','Haven','Complex'])[floor(random()*10+1)]
        ELSE (ARRAY['Green','Blue','Golden','Silver','Crystal','Diamond','Pearl','Emerald','Ruby','Sapphire'])[floor(random()*10+1)] || ' ' ||
             (ARRAY['Gardens','Heights','Park','Plaza','Court','Square','Place','Point','View','Ridge'])[floor(random()*10+1)]
    END AS name,
    CASE floor(random() * 6 + 1)
        WHEN 1 THEN 'Spacious ' || floor(random() * 4 + 1) || ' bedroom property featuring modern amenities, ' ||
                    (ARRAY['open-plan living areas','gourmet kitchen','premium finishes','smart home features','panoramic views'])[floor(random()*5+1)] || ' and ' ||
                    (ARRAY['private garden','swimming pool','rooftop terrace','secure parking','fitness center'])[floor(random()*5+1)]
        ELSE 'Prime ' || (ARRAY['residential','commercial','mixed-use','retail','office'])[floor(random()*5+1)] || ' property offering ' ||
             (ARRAY['excellent investment opportunity','prime location advantages','modern infrastructure','flexible spaces','strategic positioning'])[floor(random()*5+1)]
    END AS description,
    CASE 
        WHEN floor(random() * 6 + 1) IN (1, 2, 3, 5, 6) THEN floor(random() * 6 + 1)  -- bedrooms for residential
        ELSE NULL  -- no bedrooms for commercial
    END AS bedrooms,
    CASE 
        WHEN floor(random() * 6 + 1) IN (1, 2, 3, 5, 6) THEN floor(random() * 5 + 1)  -- bathrooms for residential
        ELSE NULL  -- no bathrooms for commercial
    END AS bathrooms,
    CASE 
        WHEN floor(random() * 6 + 1) = 1 THEN floor(random() * 10 + 1) || ' acres'  -- land
        ELSE floor(random() * 500 + 50) || ' sq.m'  -- built-up area
    END AS land_size,
    CASE 
        WHEN floor(random() * 6 + 1) IN (1, 4) THEN (random() * 50 + 1) * 1000000  -- expensive properties
        ELSE (random() * 20 + 1) * 1000000  -- moderate properties
    END AS price,
    (ARRAY['Nairobi','Mombasa','Kisumu','Nakuru','Eldoret','Malindi','Naivasha','Nyeri','Machakos','Kitale'])[floor(random()*10+1)] || ', ' ||
    (ARRAY['CBD','Westlands','Karen','Kileleshwa','Kilimani','Lavington','Runda','Muthaiga','Parklands','South B'])[floor(random()*10+1)] AS location,
    (ARRAY['for_sale','for_rent','sold','leased'])[floor(random()*4+1)] AS status,
    CAST(floor(random() * 30 + 1990) AS text) AS year_built
FROM generate_series(1, 450);

-- Generate 400+ Accommodations
INSERT INTO accomodation (
    business_id, room_type_id, name, description, 
    bedrooms, price, location, status,
    check_in_time, check_out_time
)
SELECT 
    'biz_' || LPAD(CAST(floor(random() * 10 + 31) AS text), 3, '0'),  -- business_id (from hotel businesses)
    floor(random() * 6 + 1) AS room_type_id,  -- room_type_id (1-6 from room_types)
    CASE floor(random() * 3 + 1)
        WHEN 1 THEN (ARRAY['Deluxe','Premium','Standard','Executive','Classic'])[floor(random()*5+1)] || ' ' ||
                    (ARRAY['Single','Double','Twin','Queen','King'])[floor(random()*5+1)] || ' Room'
        WHEN 2 THEN (ARRAY['Luxury','Royal','Presidential','Ambassador','Grand'])[floor(random()*5+1)] || ' ' ||
                    (ARRAY['Suite','Villa','Penthouse','Chamber','Apartment'])[floor(random()*5+1)]
        ELSE (ARRAY['Ocean','Garden','Pool','City','Mountain'])[floor(random()*5+1)] || ' ' ||
             (ARRAY['View','Facing','Side','Front','Deluxe'])[floor(random()*5+1)] || ' ' ||
             (ARRAY['Room','Suite','Studio','Apartment','Villa'])[floor(random()*5+1)]
    END AS name,
    'Elegant ' || 
    (ARRAY['modern','contemporary','classic','luxury','premium'])[floor(random()*5+1)] || ' accommodation featuring ' ||
    (ARRAY['comfortable bedding','modern amenities','scenic views','spacious layout','luxury furnishings'])[floor(random()*5+1)] AS description,
    CASE floor(random() * 3 + 1)
        WHEN 1 THEN 1  -- single room
        WHEN 2 THEN 2  -- double room
        ELSE 3  -- suite
    END AS bedrooms,
    CASE floor(random() * 3 + 1)
        WHEN 1 THEN (random() * 5000 + 3000)  -- standard rooms
        WHEN 2 THEN (random() * 8000 + 6000)  -- deluxe rooms
        ELSE (random() * 15000 + 10000)  -- suites
    END AS price,
    (ARRAY['Nairobi','Mombasa','Kisumu','Nakuru','Eldoret','Malindi','Naivasha','Nyeri','Machakos','Kitale'])[floor(random()*10+1)] AS location,
    (ARRAY['available','unavailable','booked','maintenance'])[floor(random()*4+1)] AS status,
    (ARRAY['12:00','13:00','14:00','15:00'])[floor(random()*4+1)] AS check_in_time,
    (ARRAY['10:00','11:00','12:00'])[floor(random()*3+1)] AS check_out_time
FROM generate_series(1, 450);

-- Generate 400+ Food items
INSERT INTO food (
    business_id, category_id, name, description, 
    price, is_available
)
SELECT 
    'biz_' || LPAD(CAST(floor(random() * 10 + 11) AS text), 3, '0'),  -- business_id (from restaurant businesses)
    floor(random() * 8 + 1),  -- category_id (1-8 from our food categories)
    CASE floor(random() * 8 + 1)
        WHEN 1 THEN -- Main Course
            (ARRAY['Grilled','Pan-Seared','Roasted','Braised','Slow-Cooked'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Chicken','Beef','Fish','Lamb','Pork'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['with','served with','accompanied by'])[floor(random()*3+1)] || ' ' ||
            (ARRAY['Garlic Sauce','Red Wine Reduction','Herb Butter','Special Sauce','Mushroom Gravy'])[floor(random()*5+1)]
        WHEN 2 THEN -- Appetizers
            (ARRAY['Crispy','Fresh','Spicy','Homemade','Traditional'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Spring Rolls','Samosas','Bruschetta','Calamari','Wings'])[floor(random()*5+1)]
        WHEN 3 THEN -- Beverages
            (ARRAY['Fresh','Iced','Hot','Signature','Classic'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Coffee','Tea','Juice','Smoothie','Cocktail'])[floor(random()*5+1)]
        WHEN 4 THEN -- Desserts
            (ARRAY['Decadent','Homemade','Classic','Signature','Fresh'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Chocolate Cake','Cheesecake','Ice Cream','Tiramisu','Apple Pie'])[floor(random()*5+1)]
        ELSE -- Other Categories
            (ARRAY['House','Chef''s','Seasonal','Special','Signature'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Salad','Soup','Side','Breakfast','Specialty'])[floor(random()*5+1)]
    END AS name,
    CASE floor(random() * 8 + 1)
        WHEN 1 THEN 'Tender and juicy ' || lower((ARRAY['chicken','beef','fish','lamb','pork'])[floor(random()*5+1)]) || 
                    ' prepared with ' || (ARRAY['fresh herbs','special spices','house marinade','secret recipe','premium ingredients'])[floor(random()*5+1)]
        WHEN 2 THEN 'Fresh and flavorful ' || 
                    (ARRAY['appetizer','starter','dish','specialty','creation'])[floor(random()*5+1)] || ' made with ' ||
                    (ARRAY['local ingredients','seasonal produce','premium components','fresh herbs','house-made sauce'])[floor(random()*5+1)]
        ELSE 'Delicious ' || (ARRAY['house specialty','chef''s creation','seasonal offering','signature dish','classic recipe'])[floor(random()*5+1)] ||
             ' prepared with ' || (ARRAY['care','attention to detail','premium ingredients','traditional methods','modern techniques'])[floor(random()*5+1)]
    END AS description,
    CASE 
        WHEN floor(random() * 8 + 1) IN (1, 4) THEN (random() * 1500 + 500)::numeric(10,2)  -- main courses and premium items
        WHEN floor(random() * 8 + 1) IN (2, 3) THEN (random() * 500 + 200)::numeric(10,2)   -- mid-range items
        ELSE (random() * 300 + 100)::numeric(10,2)                                          -- sides and small items
    END AS price,
    random() < 0.9 AS is_available  -- 90% of items are available
FROM generate_series(1, 450);

-- Generate 400+ Products
INSERT INTO products (
    business_id, name, description, price, 
    category_id, stock, image_url, rating, embedding
)
SELECT 
    'biz_' || LPAD(CAST(floor(random() * 10 + 1) AS text), 3, '0'),  -- business_id (from ecommerce businesses)
    CASE floor(random() * 8 + 9)  -- categories 9-16 are product categories
        WHEN 9 THEN -- Electronics
            (ARRAY['Smart','Wireless','Premium','Pro','Ultra'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Headphones','Smartwatch','Laptop','Tablet','Speaker'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Pro','Elite','Max','Plus','X'])[floor(random()*5+1)]
        WHEN 10 THEN -- Furniture
            (ARRAY['Modern','Classic','Luxury','Designer','Contemporary'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Sofa','Chair','Table','Bed','Cabinet'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Set','Collection','Piece','Edition','Series'])[floor(random()*5+1)]
        ELSE -- Other categories
            (ARRAY['Premium','Deluxe','Professional','Advanced','Ultimate'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Home','Office','Sports','Beauty','Gaming'])[floor(random()*5+1)] || ' ' ||
            (ARRAY['Essential','Kit','Set','Package','Solution'])[floor(random()*5+1)]
    END AS name,
    CASE floor(random() * 8 + 9)
        WHEN 9 THEN 'High-quality ' || lower((ARRAY['electronic','smart','wireless','digital','premium'])[floor(random()*5+1)]) || 
                    ' device featuring ' || (ARRAY['advanced technology','smart features','premium quality','innovative design','superior performance'])[floor(random()*5+1)]
        WHEN 10 THEN 'Elegant ' || lower((ARRAY['modern','classic','designer','contemporary','luxury'])[floor(random()*5+1)]) || 
                     ' furniture with ' || (ARRAY['premium materials','superior comfort','stylish design','durability','versatile functionality'])[floor(random()*5+1)]
        ELSE 'Premium quality ' || (ARRAY['product','item','solution','essential','accessory'])[floor(random()*5+1)] || 
             ' offering ' || (ARRAY['excellent value','superior quality','amazing features','great performance','perfect solution'])[floor(random()*5+1)]
    END AS description,
    CASE 
        WHEN floor(random() * 8 + 9) = 9 THEN (random() * 100000 + 20000)::numeric(10,2)  -- electronics
        WHEN floor(random() * 8 + 9) = 10 THEN (random() * 50000 + 10000)::numeric(10,2)  -- furniture
        ELSE (random() * 10000 + 1000)::numeric(10,2)                                      -- other items
    END AS price,
    floor(random() * 8 + 9) AS category_id,  -- category_id (9-16 from our product categories)
    floor(random() * 100 + 1) AS stock,
    'https://source.unsplash.com/800x600/?product&sig=' || generate_series AS image_url,
    floor(random() * 5 + 1) AS rating,
    'embedding_' || generate_series AS embedding
FROM generate_series(1, 450);


INSERT INTO entity_media_types (id, name, description) VALUES
(1, 'property', 'Media related to properties like homes, land, apartments, etc.'),
(2, 'accommodation', 'Media showcasing hotel rooms, suites, and accommodation units.'),
(3, 'food', 'Images of food dishes served in restaurants.'),
(4, 'product', 'Media of products listed in the e-commerce section.');

-- Add media for all entities
INSERT INTO entity_media (entity_type_id, entity_id, url, storage_type)
SELECT 
    1 AS entity_type_id,  -- 1 for property
    p.id AS entity_id,
    'https://source.unsplash.com/800x600/?property,real,estate,house,apartment&sig=' || p.id || '_' || gs AS url,
    1 AS storage_type
FROM property p
CROSS JOIN generate_series(1, floor(random() * 3 + 2)::int) AS gs;

INSERT INTO entity_media (entity_type_id, entity_id, url, storage_type)
SELECT 
    2 AS entity_type_id,  -- 2 for accommodation
    a.id AS entity_id,
    'https://source.unsplash.com/800x600/?hotel,room,accommodation,suite&sig=' || a.id || '_' || gs AS url,
    1 AS storage_type
FROM accomodation a
CROSS JOIN generate_series(1, floor(random() * 2 + 2)::int) AS gs;

INSERT INTO entity_media (entity_type_id, entity_id, url, storage_type)
SELECT 
    3 AS entity_type_id,  -- 3 for food
    f.id AS entity_id,
    'https://source.unsplash.com/800x600/?food,cuisine,restaurant,dish&sig=' || f.id || '_' || gs AS url,
    1 AS storage_type
FROM food f
CROSS JOIN generate_series(1, floor(random() * 2 + 1)::int) AS gs;


INSERT INTO entity_media (entity_type_id, entity_id, url, storage_type)
SELECT 
    4 AS entity_type_id,  -- 4 for product
    p.id AS entity_id,
    'https://source.unsplash.com/800x600/?product,electronics,furniture,fashion&sig=' || p.id || '_' || gs AS url,
    1 AS storage_type
FROM products p
CROSS JOIN generate_series(1, floor(random() * 2 + 2)::int) AS gs;


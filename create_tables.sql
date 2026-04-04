CREATE TABLE 'Products' (
    'id' INTEGER AUTOINCREMENT,
    'name' VARCHAR(100) NOT NULL,
    'description' TEXT,
    'price' DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (id)
)

CREATE TABLE 'Customers' (
    'id' INTEGER AUTOINCREMENT,
    'first_name' VARCHAR(20) NOT NULL,
    'last_name' VARCHAR(20) NOT NULL,
    'email' VARCHAR(50) NOT NULL UNIQUE,
    'username' VARCHAR(20) NOT NULL UNIQUE,
    'password' VARCHAR(255) NOT NULL,
    'created_at' DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
)

CREATE TABLE 'Orders' (
    'id' INTEGER AUTOINCREMENT,
    'num_items' INTEGER NOT NULL,
    'total_cost' DECIMAL(10, 2) NOT NULL,
    'order_date' DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    'order_status' ENUM('pending', 'sold') NOT NULL DEFAULT 'pending',
    PRIMARY KEY (id),
    FOREIGN KEY (product_id) REFERENCES Products(id),
    FOREIGN KEY (customer_id) REFERENCES Customers(id)
)

CREATE TABLE 'Subscriptions' (
    'id' INTEGER AUTOINCREMENT,
    'license_key' VARCHAR(20) NOT NULL UNIQUE,
    'start_date' DATETIME NOT NULL,
    'end_date' DATETIME,
    PRIMARY KEY (id),
    FOREIGN KEY (product_id) REFERENCES Products(id),
    FOREIGN KEY (customer_id) REFERENCES Customers(id)
)
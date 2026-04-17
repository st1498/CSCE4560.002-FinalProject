CREATE TABLE Products (
    id INT AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE Customers (
    id INT AUTO_INCREMENT,
    first_name VARCHAR(20) NOT NULL,
    last_name VARCHAR(20) NOT NULL,
    email VARCHAR(50) NOT NULL UNIQUE,
    username VARCHAR(20) NOT NULL UNIQUE,
    password_hash VARCHAR(250) NOT NULL,
    date_registered DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id)
);

CREATE TABLE Orders (
    id INT AUTO_INCREMENT,
    num_items INT NOT NULL,
    total_cost DECIMAL(10, 2) NOT NULL,
    order_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status ENUM('pending', 'sold') NOT NULL DEFAULT 'pending',
    product_id INT NOT NULL,
    customer_id INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (product_id) REFERENCES Products(id),
    FOREIGN KEY (customer_id) REFERENCES Customers(id)
);

CREATE TABLE Subscriptions (
    id INT AUTO_INCREMENT,
    license_key VARCHAR(20) NOT NULL UNIQUE,
    start_date DATETIME NOT NULL,
    end_date DATETIME,
    product_id INT NOT NULL,
    customer_id INT NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (product_id) REFERENCES Products(id),
    FOREIGN KEY (customer_id) REFERENCES Customers(id)
);

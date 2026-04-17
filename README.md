# Cybermax E-Commerce Project

## I. Project Structure

```text
CSCE4560.002-FinalProject/
└─static
    └─style.css
└─templates
    ├─cart.html
    ├─change-password.html
    ├─checkout.html
    ├─confirmation.html
    ├─forgot-password.html
    ├─index.html
    ├─product1.html
    ├─product2.html
    ├─profile.html
    ├─signin.html
    └─signup.html
└─.gitignore
├─app.py
├─models.py
├─paypal_backend.py
├─README.md
└─requirements.txt
```

## II. How to setup up MySQL server

### Download and install MySQL

- Install MariaDB

```bash
sudo apt-get install mariadb-server
```

- Check that the server is running

```bash
sudo systemctl status mysql
```

### Create a new user and a database

#### 1. Log in to MySQL as root

```bash
sudo mysql
```

#### 2. Create a new database (e.g., testdb

```
MariaDB [(none)]> CREATE DATABASE testdb;
```

#### 3. Create a new user with a password (e.g., user=test, password=test)

```
MariaDB [(none)]> CREATE USER 'test'@'localhost' IDENTIFIED VIA mysql_native_password USING PASSWORD('test');
```

#### 4. Grant privileges

```
MariaDB [(none)]> GRANT ALL PRIVILEGES ON testdb.* TO 'test'@'localhost';
```

#### 5. Apply changes and exit

```
FLUSH PRIVILEGES;
EXIT;
```

#### 6. Verify the new user

- Use the new user's password when prompted for a password ('test' in this case)

```bash
mysql -u test -p
```

- Check that the database exists

```
MariaDB [(none)]>SHOW DATABASES;
```

- Example output

```text
+--------------------+
| Database           |
+--------------------+
| information_schema |
| testdb             |
+--------------------+
```

- Exit the console

```
MariaDB [(none)]>EXIT
```

##### 7. CREATE THE TABLES FOR THE DATABASE

- Create the tables for testdb from the terminal

```bash
mysql -u test -p testdb < create_tables.sql
```

- Verify that the tables were successfully created

```bash
mysql -u test -p testDB -e "SHOW TABLES"
```

## III. Format for the .env file

### 1. Generate a random secret key for MySQL using Python's secrets library

```bash
python3 -c "import secrets; print(secrets.token_bytes(32).hex())"
```

- Example output

```text

```

### 2. Create the .env file and add the credentials

```text
HOST="localhost"
USER="test"
PASSWORD="test"
PORT="3306"
DB_NAME="testdb"
SECRET_KEY="07140666f2a8ab96075b01c9780e1ede7508c08184fe92af4394fb724615c6b3"
PAYPAL_CLIENT_ID=""
PAYPAL_SECRET=""
GOOGLE_CLIENT_ID=""
GOOGLE_CLIENT_SECRET=""
```

## IV. How to run the project





Open `.env` and assign the generated 32-byte key to the SECRET_KEY variable.

```text```

### Start the Flask app

```bash
python3 app.py
```

## V. Screenshots of each templates being rendered

### Home page

![Home page](./Screenshots/home%20page.png)

### VPN product page

![Product 1](./Screenshots/product1%20page.png)

### SaS product page

![Product 2](./Screenshots/product2%20page.png)

### Change Password page

![Change Password](./Screenshots/change%20password%20page.png)

### Forgot Password page

![Forgot Password](./Screenshots/forgot%20password%20page.png)

### Sign In page

![Sign In](./Screenshots/signin%20page.png)

### Sign Up page

![Sign Up](./Screenshots/signup%20page.png)

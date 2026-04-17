# Cybermax E-Commerce Project

## Project Structure

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

## How to setup up MySQL server

### Download and install MySQL

- Download the APT Repository

```bash
wget https://dev.mysql.com/get/mysql-apt-config_0.8.36-1_all.deb
```

- Install the MySQL Server

```bash
sudo apt install mysql-server -y
```

- If the above command fails, try installing MariaDB instead

```bash
sudo apt-get install mariadb-server
```

- Check that the server is running

```bash
sudo systemctl status mysq
```

### Add a new user and password

- Connect to MySQL

```bash
mysql -u root -p
```

- In the MySQL console, set a new user and password and exit the console.
- In this example, we create user 'root' with password 'root'.

```
> ALTER USER root@localhost IDENTIFIED BY 'root';
> QUIT;
```

### Create a new database

- Create a new database called "safelock_sec"

```bash
mysql -u root -p cyber_max -p -e "CREATE DATABASE safelock_sec;"
```

- Verify that the database exists

```bash
mysql -u root -p cyber_max -p -e "SHOW DATABASES;"
```

```text
# Example output

+--------------------+
| Database           |
+--------------------+
| information_schema |
| mysql              |
| performance_schema |
| safelock_sec       |
| sys                |
+--------------------+
```

- Create the tables for the new database

```bash
mysql -u root -p safelock_sec < create_tables.sql
```

- Verify that the tables have been successfully created

```bash
mysql -u root -p safelock_secx -p -e "SHOW TABLES;"
```

```text
# Example output

+------------------------+
| Tables_in_safelock_sec |
+------------------------+
| Customers              |
| Orders                 |
| Products               |
| Subscriptions          |
+------------------------+
```

## How to run the project

```bash
python3 app.py
```

## Screenshots of each templates being rendered

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

# How to setup up a MySQL server

## Download the APT Repository

```bash
wget https://dev.mysql.com/get/mysql-apt-config_0.8.36-1_all.deb
```

## Install the MySQL Server

```bash
sudo apt install mysql-server -y
```

### If the above command fails, try installing MariaDB instead

```bash
sudo apt-get install mariadb-server
```

### Check that the server is running

```bash
sudo systemctl status mysq
```

## Setup a new user and a new password

```bash
mysql -u root -p
```

### In the MySQL console, type this command to set a new user and password:

```
> ALTER USER root@localhost IDENTIFIED BY 'root';
```

### Create a new database

```
> CREATE DATABASE cyber_max;
```

### Exit MySQL Server

```
> QUIT;
```
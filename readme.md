# METAL ACCOUNTING
![](https://media.giphy.com/media/gui67fZ3xIneM/giphy.gif)

### Metal Accounting is a tool for aggregating journal entries into financial statements.

## Installation

### Python
Install python3.6.X from <a href="https://www.python.org">python.org</a>

### MySQL
Install an instance of MySQL locally.
If you want to use docker (swap out `YOUR_PASSWORD_GOES_HERE` and  `YOUR_DATABASE_NAME_GOES_HERE`)
```
docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=YOUR_PASSWORD_GOES_HERE -v /tmp:/tmp --name YOUR_DATABASE_NAME_GOES_HERE -d mysql --default-authentication-plugin=mysql_native_password
```
Create a new database on the MySQL server.


### Python Virtual Environment and Install Packages
```bash
# from the project root run
$ pip install virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt

# If running on Ubuntu/Debian
$ sudo apt-get install python3.6-dev
```

### Add Local Environment Variales
Add `applocals.py` file to the django project directory (`metalacc/metalacc/applocals.py`)

example `applocals.py`
```python
SECRET_KEY = 'ADD A SECRET KEY HERE'

ADDITIONAL_ALLOWED_HOSTS = []

ENV = 'DEV'

DB_NAME = 'YOUR DATABASE NAME GOES HERE'
DB_HOSTNAME = '127.0.0.1'
DB_USERNAME = 'root'
DB_PASSWORD = 'YOUR DATABASE PASSWORD GOES HERE'
```

To create a secret key
```bash
$ python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```


### Initialize your database
```
$ ./manage.py migrate
```

### Start the dev server
```bash
$ ./manage.py runserver

# or to allow devices on your network to test the site
$ ./manage.py runserver 0.0.0.0:8000
```
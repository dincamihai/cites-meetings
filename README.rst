Quick installation
------------------

1. Clone the repository::

    git clone git@github.com:eaudeweb/cites-meetings.git -o github
    cd cites-meetings

2. Create & activate a virtual environment::

    virtualenv sandbox
    echo '*' > sandbox/.gitignore
    . sandbox/bin/activate

3. Install dependencies::

    pip install -r requirements-dev.txt

4. Create a configuration file::

    mkdir -p instance
    echo 'SECRET_KEY = "something random"' >> instance/settings.py
    echo 'ACCOUNTS = [ ("tester@example.com", "secretpw") ]' >> instance/settings.py

5. Set up the PostgreSQL database::

    createdb cites
    psql cites -c 'create extension hstore'
    python manage.py syncdb

6. Create a testing database and run the unit tests::

    createdb cites_test
    psql cites_test -c 'create extension hstore'
    nosetests

7. Run a test server::

    python manage.py runserver

8. Deploy (after customizing `local_fabfile.py`)::

    fab deploy


Debian deployment
-----------------

To set up the PostgreSQL database in Debian, you need to install the
packages `postgresql-9.1`, `postgresql-contrib-9.1` and
`postgresql-server-dev-9.1`. Then create a database, enable the `hstore`
extension, and grant access to a user::

    root # su - postgres
    postgres $ psql template1
    psql (9.1.2)
    Type "help" for help.

    template1=# CREATE USER edw WITH PASSWORD 'edw';
    CREATE ROLE
    template1=# CREATE DATABASE cites;
    CREATE DATABASE
    template1=# GRANT ALL PRIVILEGES ON DATABASE cites TO edw;
    GRANT
    template1=# \q
    postgres $ psql cites
    cites=# create extension hstore;

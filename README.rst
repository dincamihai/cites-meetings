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

5. Set up the database::

    mysql -u root -e 'create database cites'
    mysql -u root -e 'grant all privileges on cites.* to cites@localhost identified by "cites";'
    ./app.py syncdb

6. Create a testing database and run the unit tests::

    mysql -u root -e 'create database cites_test'
    mysql -u root -e 'grant all privileges on cites_test.* to cites@localhost identified by "cites";'
    nosetests

7. Run a test server::

    ./app.py runserver

8. Deploy (after customizing `local_fabfile.py`)::

    fab deploy

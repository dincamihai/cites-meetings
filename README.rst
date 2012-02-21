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

    pip install -r requirements.txt

4. Set up the database::

    mysql -u root -e 'create database cites'
    mysql -u root -e 'grant all privileges on cites.* to cites@localhost identified by "cites";'
    ./app.py syncdb

5. Run a test server::

    ./app.py runserver
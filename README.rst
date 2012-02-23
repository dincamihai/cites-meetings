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

4. Set up the PostgreSQL database::

    createdb cites
    ./app.py syncdb

5. Create a testing database and run the unit tests::

    createdb cites_test
    nosetests

6. Run a test server::

    ./app.py runserver

7. Deploy (after customizing `local_fabfile.py`)::

    fab deploy

"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import SQLAlchemyError

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        # Sample Data Below

        # User table
        u = User(
            email="test@test.com",
            username="testuser",
            password="password"
        )
        u2 = User(
            email="test1@test.com",
            username="test1user",
            password="HASHED1_PASSWORD"
        )
        db.session.add(u, u2)

        db.session.commit()
        # Message table
        m = Message(
            text="testtext",
            user_id=u.id
        )
        
        db.session.commit()
        #Follows Table
        u.followers.append(u2)

        db.session.commit()

        # End of Sample Data

        self.client = app.test_client()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test2@test.com",
            username="test2user",
            password="HASHED2_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_repr(self):
        """Does __repr__ work as expected?"""

        u = User.query.first()
        self.assertEqual(str(u), f"<User #{u.id}: testuser, test@test.com>")

    def test_user_is_followed(self):
        """Does is_following() successfully detect when user1 is following user2?"""

        u = User.query.filter_by(username="testuser").first()
        u2 = User.query.filter_by(username="test1user").first()

        self.assertTrue(u.is_followed_by(u2))
        self.assertFalse(u.is_following(u2))
        self.assertFalse(u2.is_followed_by(u))
        self.assertTrue(u2.is_following(u))

    def test_user_signup(self):
        """Does User.create successfullly create a new user given valid creds?"""

        User.query.filter_by(username="testuser").delete()
        u = User.signup("testuser", "test@test.com", "password", "/static/images/default-pic.png")
        db.session.commit()

        u = User.query.filter_by(username="testuser").first()
        self.assertTrue(u)

        self.assertRaises(SQLAlchemyError, User.signup, "testuser", "test@test2.com", "HASHED2_PW", "somepic.jpg")
            
        u2 = User.query.filter_by(email="test@test2.com").first()
        self.assertEqual(u2, None)

    
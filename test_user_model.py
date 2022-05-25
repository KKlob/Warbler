"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import exc

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app


class UserModelTestCase(TestCase):
    """Test User model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        # Sample Data Below

        # User table
        u1 = User.signup("testuser1", "test1@test.com", "password", None)
        u1_id = 11
        u1.id = u1_id

        u2 = User.signup("testuser2", "test2@test.com", "password", None)
        u2_id = 22
        u2.id = u2_id

        db.session.commit()

        u1 = User.query.get(u1_id)
        u2 = User.query.get(u2_id)

        self.u1 = u1
        self.u1_id = u1_id

        self.u2 = u2
        self.u2_id = u2_id

        # End of Sample Data

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_repr(self):
        """Does __repr__ work as expected?"""

        u = User.query.get(self.u1_id)
        self.assertEqual(str(u), f"<User #11: testuser1, test1@test.com>")

    def test_user_follow_funcs(self):
        """Does is_following() successfully detect when user1 is following user2?"""

        self.u1.following.append(self.u2)
        db.session.commit()

        self.assertEqual(len(self.u2.following), 0)
        self.assertEqual(len(self.u2.followers), 1)
        self.assertEqual(len(self.u1.following), 1)
        self.assertEqual(len(self.u1.followers), 0)

        self.assertEqual(self.u2.followers[0].id, self.u1.id)
        self.assertEqual(self.u1.following[0].id, self.u2.id)

        # Test User.is_following
        self.assertTrue(self.u1.is_following(self.u2))
        self.assertFalse(self.u2.is_following(self.u1))

        # Test User.is_followed_by
        self.assertTrue(self.u2.is_followed_by(self.u1))
        self.assertFalse(self.u1.is_followed_by(self.u2))

    def test_user_signup(self):
        """Does User.create successfullly create a new user given valid creds?"""

        #Test valid signup
        testuser = User.signup("testtest", "testtest@test.com", "password", None)
        test_id = 999
        testuser.id = test_id
        db.session.commit()

        testuser = User.query.get(test_id)
        self.assertIsNotNone(testuser)
        self.assertEqual(testuser.username, "testtest")
        self.assertEqual(testuser.email, "testtest@test.com")
        self.assertNotEqual(testuser.password, "password")
        self.assertTrue(testuser.password.startswith("$2b$"))


        # For Following Tests:
        # Does User.signup fail to create an user given invalid creds?

    def test_invalid_username_singup(self):
        """Test invalid username signup"""
        invalid_user = User.signup(None, "test3@test.com", "password", None)
        iu_id = 376
        invalid_user.id = iu_id
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_email_singup(self):
        """Test invalid email signup"""
        invalid_user = User.signup("testuser3", None, "password", None)
        iu_id = 333
        invalid_user.id = iu_id
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_singup(self):
        """Test invalide password signup"""
        with self.assertRaises(ValueError) as context:
            User.signup("testuser3", "test3@test.com", None, None)

    def test_user_auth_valid_creds(self):
        """Test User.authenticate when passed valid creds"""
        user = User.authenticate(self.u1.username, "password")

        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.u1_id)

    def test_user_auth_invalid_username(self):
        """Test User.authenticate when passed invalid username"""
        self.assertFalse(User.authenticate("nonusername", "password"))

    def test_user_auth_invalide_password(self):
        """Test User.authenticate when passed invalide password"""
        self.assertFalse(User.authenticate(self.u1.username, "badpassword"))
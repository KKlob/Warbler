"""Message model tests"""

import os
from unittest import TestCase
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import except_

from models import db, User, Message, Follows, Likes

# Set database url for warbler-test db
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app

class MessageModelTestCase(TestCase):
    """Test Message model"""

    def setUp(self):
        """Create test tabgles, add sample data"""

        db.drop_all()
        db.create_all()

        # Sample Data Below

        #User table
        u1 = User.signup("testuser1", "test1@test.com", "password", None)
        self.u1id = 333
        u1.id = self.u1id
        db.session.commit()

        self.u1 = User.query.get(self.u1id)

        u2 = User.signup("testuser2", "test2@test.com", "password", None)
        self.u2id = 444
        u2.id = self.u2id
        db.session.commit()

        self.u2 = User.query.get(self.u2id)

        #Message table
        m1 = Message(text="user1 warble", user_id=self.u1id)

        m2 = Message(text="user2 warble", user_id=self.u2id)

        db.session.add_all([m1, m2])
        db.session.commit()

        #Add m2 to u1 likes
        user1 = self.u1
        user1.likes.append(m2)
        db.session.commit()

        # End of sample data
        self.client = app.test_client()

    def tearDown(self):
        """Reset the db after each test"""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message_creation(self):
        """Test that Message model correctly creates + stores message"""

        m3 = Message(text="user2 2nd warble", user_id=self.u2id)
        db.session.add(m3)
        db.session.commit()

        self.assertEqual(len(self.u2.messages), 2)
        self.assertEqual(self.u2.messages[1].text, "user2 2nd warble")

    def test_message_likes(self):
        """Test that self.u1 has a liked message and that it matches the correct message.id"""

        u1_likes = Likes.query.filter(Likes.user_id == self.u1id).all()
        self.assertEqual(len(u1_likes), 1)

        message = Message.query.filter(Message.user_id == self.u2id).first()
        self.assertEqual(u1_likes[0].message_id, message.id)    
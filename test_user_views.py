"""User view tests"""

import os
from unittest import TestCase
from flask_sqlalchemy import SQLAlchemy
from models import db, connect_db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

# Disable wtforms CSRF, pain to test. Security not necessary for these tests
app.config['WTF_CSRF_ENABLED'] = False

class UserViewsTestCase(TestCase):
    """Test User views"""

    def setUp(self):
        """Create test client, add sample data"""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        #Sample Data Start
        #User table
        u1 = User.signup("testuser1", "test1@test.com", "password", None)
        u1_id = 11
        u1.id = u1_id

        u2 = User.signup("testuser2", "test2@test.com", "password", None)
        u2_id = 22
        u2.id = u2_id

        u3 = User.signup("testuser3", "test3@test.com", "password", None)
        u3_id = 33
        u3.id = u3_id

        db.session.add_all([u1, u2, u3])
        db.session.commit()

        u1 = User.query.get(u1_id)
        u2 = User.query.get(u2_id)
        u3 = User.query.get(u3_id)

        self.u1 = u1
        self.u1_id = u1_id

        self.u2 = u2
        self.u2_id = u2_id

        self.u3 = u3
        self.u3_id = u3_id

        #Set u2 to follow u1
        u2.following.append(u1)
        db.session.commit()

        #Message table
        m1 = Message(text="user1 warble", user_id=self.u1_id)

        m2 = Message(text="user2 warble", user_id=self.u2_id)

        m3 = Message(text="user3 warble", user_id=self.u3_id)

        db.session.add_all([m1, m2, m3])
        db.session.commit()

        self.m3 = m3

        #Add m2 to u1 likes
        user1 = self.u1
        user1.likes.append(m2)
        db.session.commit()

        #End of Sample Data

    def tearDown(self):
        """Reset the db after each test"""
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_users_index(self):
        """Test route '/users'"""

        with self.client as c:
            resp = c.get('/users')

            self.assertIn("@testuser1", str(resp.data))
            self.assertIn("@testuser2", str(resp.data))
            self.assertIn("@testuser3", str(resp.data))

    def test_users_show(self):
        """Test route '/users/<user_id>'"""

        with self.client as c:
            resp = c.get(f'/users/{self.u1_id}')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))

    def test_users_show_following(self):
        """Test route '/users/<user_id>/following"""

        # testuser2 is following testuser1
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            user2 = User.query.get(self.u2_id)

            resp = c.get(f'/users/{user2.id}/following')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))

            # Make u2 follow u3, refresh following page and check u3 is included
            user2.following.append(self.u3)
            db.session.commit()

            resp = c.get(f'/users/{user2.id}/following')
            self.assertIn("@testuser3", str(resp.data))

    def test_users_add_remove_follow(self):
        """Test that POST route '/users/follow/<follow_id>' works correctly"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u3_id

            # First check testuser1 is not being followed by testuser3
            resp = c.get(f'/users/{self.u3_id}/following')
            self.assertNotIn("@testuser1", str(resp.data))
            
            # Have self.u3 follow u1
            resp = c.post(f'/users/follow/{self.u1_id}',
                            follow_redirects=True)

            # check testuser1 is being followed by testuser3
            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser1", str(resp.data))

            # remove testuser1 from testuser3's followings
            resp = c.post(f'/users/stop-following/{self.u1_id}',
                            follow_redirects=True)
            
            # check testuser1 is not being followed by testuser3
            self.assertEqual(resp.status_code, 200)
            self.assertNotIn("@testuser1", str(resp.data))


    def test_users_show_followers(self):
        """Test route '/users/<user_id>/followers"""

        # testuser1 has a follower testuser2
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            user1 = User.query.get(self.u1_id)

            resp = c.get(f'/users/{user1.id}/followers')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("@testuser2", str(resp.data))

            # make u3 follow u1, refresh page and check u3 is included

            user1.followers.append(self.u3)
            db.session.commit()

            resp = c.get(f'/users/{user1.id}/followers')

            self.assertIn("@testuser3", str(resp.data))

    def test_users_likes(self):
        """Test route '/users/<user_id>/likes' page"""

        # testuser1 has one liked message
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            
            user1 = User.query.get(self.u1_id)
            msg2 = Message.query.filter(Message.user_id == self.u2_id).first()

            resp = c.get(f'/users/{user1.id}/likes')

            self.assertEqual(resp.status_code, 200)
            self.assertIn(msg2.text, str(resp.data))

            # Add testuser3 message to testuser1 likes, refresh page and check m3 is included
            user1.likes.append(self.m3)
            db.session.commit()

            m3 = Message.query.filter(Message.user_id == self.u3_id).first()

            resp = c.get(f'/users/{user1.id}/likes')

            self.assertIn(m3.text, str(resp.data))

    def test_users_profile(self):
        """Test route '/users/profile' POST route"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id
            
            #Logged in as testuser1
            resp = c.get('/users/profile')

            self.assertEqual(resp.status_code, 200)
            self.assertIn("testuser1", str(resp.data))


            # Change testuser1 username to 1testuser and check for change
            user1 = User.query.get(self.u1_id)

            resp = c.post('/users/profile',
                        data={'username': '1testuser', 'email': user1.email, 'image_url': user1.image_url, 'header_image_url': user1.header_image_url, 'bio': user1.bio},
                        follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("1testuser", str(resp.data))

    def test_users_delete(self):
        """Test route '/users/delete' POST route"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            #Logged in as testuser1. Delete self

            resp = c.post('/users/delete', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Join Warbler today.", str(resp.data))

    def test_users_add_remove_like(self):
        """Test route '/users'/add_like/<message_id>' POST route"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1_id

            #Logged in as testuser1

            msg = Message.query.filter(Message.user_id == self.u3_id).first()

            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)

            self.assertEqual(resp.status_code, 200)
            # redirects to '/' which only shows messages of followed users.

            resp = c.get(f'/users/{self.u1_id}/likes')

            msg = Message.query.filter(Message.user_id == self.u3_id).first()

            self.assertEqual(resp.status_code, 200)
            self.assertIn(msg.text, str(resp.data))

            # remove like, then check it has been removed from testuser1's likes page

            resp = c.post(f'/users/add_like/{msg.id}', follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            resp = c.get(f'/users/{self.u1_id}/likes')

            msg = Message.query.filter(Message.user_id == self.u3_id).first()

            self.assertEqual(resp.status_code, 200)
            self.assertNotIn(msg.text, str(resp.data))
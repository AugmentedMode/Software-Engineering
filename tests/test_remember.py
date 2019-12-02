import unittest
from unittest import mock
from flask import Flask
from flask_testing import TestCase
from OOZero import create_app
from OOZero.model import db
import OOZero.user_model as user
import OOZero.event_model as event
import datetime
import tests.generateDB as generateDB

class TestUser(TestCase, unittest.TestCase):

    def create_app(self):
        app = create_app("OOZero.config.TestingConfig")
        return app

    @classmethod
    def setUpClass(cls):
        """This optional method is called once for this test class
        """
        pass

    @classmethod
    def tearDownClass(cls):
        """This optional method is called once for this test class
        """
        pass

    def setUp(self):
        """This optional method is called before every test method
        """
        generateDB.generatePopulateDB()
        

    def tearDown(self):
        """This optional method is called after every test method
        """
        db.drop_all()

    def test_addRemember(self):
        cookie = user.addRemember(user.getUser("test"))
        self.assertEqual(len(user.RememberUser.query.filter_by(user_id=user.getUser("test").id).all()), 1)

    def test_checkRemember(self):
        cookie = user.addRemember(user.getUser("test"))
        self.assertEqual(user.checkRemember(cookie), user.getUser("test"))
        self.assertIsNone(user.checkRemember("Not a cookie"))
        remember = user.RememberUser.query.filter_by(cookie=cookie).first()
        remember.timestamp = datetime.datetime.utcnow() - datetime.timedelta(days=31)
        db.session.commit()
        self.assertIsNone(user.checkRemember(cookie))
        

if __name__ == '__main__':
    unittest.main()
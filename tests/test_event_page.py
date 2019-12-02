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

    def test_add(self):
        page1 = event.createPage("pagepage", user.getUser("test"))
        self.assertIsNotNone(page1)
        self.assertRaises(ValueError, lambda: event.createPage("", user.getUser("test").id))

    def test_getPagesByOwner(self):
        pages = event.getPagesByOwner(user.getUser("test"))
        self.assertEqual(len(pages), 2)

    def test_getPage(self):
        pages = event.getPagesByOwner(user.getUser("test"))
        self.assertEqual(pages[0], event.getPageById(pages[0].id))
        self.assertEqual(pages[1], event.getPageById(pages[1].id))
        self.assertIsNone(event.getPageById(2000))

    def test_deletePage(self):
        pages = event.getPagesByOwner(user.getUser("test"))
        event.deletePage(pages[0])
        self.assertIsNone(event.getPageById(pages[0].id))
        self.assertEqual(len(event.getPagesByOwner(user.getUser("test"))), 1)
        pages = event.getPagesByOwner(user.getUser("username"))
        eventid = pages[0].events[0].id
        self.assertIsNotNone(event.getEventById(eventid))
        event.deletePage(pages[0])
        self.assertIsNone(event.getEventById(eventid))

    def test_removeEventFromPage(self):
        pages = event.getPagesByOwner(user.getUser("username"))
        self.assertEqual(len(pages[0].events), 1)
        event.removeEventFromPage(pages[0].events[0])
        pages = event.getPagesByOwner(user.getUser("username"))
        self.assertEqual(len(pages[0].events), 0)
        self.assertEqual(len(event.getEventsByOwner(user.getUser("username"))), 2)

    def test_editPage(self):
        pages = event.getPagesByOwner(user.getUser("test"))
        pageId = pages[0].id
        oldName = pages[0].name
        pageNew = event.editPage(pageId, name="A new name")
        self.assertNotEqual(pageNew.name, oldName)
        self.assertEqual(pageNew.name, event.getPageById(pageId).name)
        jeffsPages = len(user.getUser("Jeff").pages)
        pageNew = event.editPage(pageId, name="A newer name", owner=user.getUser("Jeff"))
        self.assertEqual(jeffsPages + 1, len(user.getUser("Jeff").pages))
        pageNew = event.editPage(pageId, discription="an indecisive page")
        self.assertEqual(pageNew.discription, "an indecisive page")
        

if __name__ == '__main__':
    unittest.main()
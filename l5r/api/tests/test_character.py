# -*- coding: utf-8 -*-
__author__ = 'Daniele Simonetti'

import unittest
from collections import namedtuple
import api
import api.character
import api.data

import dal

TestClanMock = namedtuple('Clan', ['id', 'name'])
TestFamilyMock = namedtuple('Family', ['id', 'name', 'clanid', 'trait'])
TestSchoolMock = namedtuple(
    'School',
    ['id', 'name', 'clanid', 'trait', 'tags'])


def test_clan():
    return TestClanMock(id='test_clan', name='Test Clan')


def test_family():
    return TestFamilyMock(id='test_family', clanid='test_clan', name='Test Family', trait='test_trait')


def test_school():
    return TestSchoolMock(
        id='test_school',
        clanid='test_clan',
        name='Test School',
        trait='test_trait',
        tags=['tag1', 'tag2'])


class TestCharacterBll(unittest.TestCase):

    def setUp(self):
        # inject some data
        data_ = dal.Data([], [])
        api.data.set_model(data_)

        # a clan
        data_.clans.append(test_clan())
        # a family
        data_.families.append(test_family())
        # a school
        data_.schools.append(test_school())

        # create new character
        api.character.new()

    def tearDown(self):
        pass

    def test_set_family(self):
        """
        test the set_family method
        :return:
        """
        api.character.set_family('test_family')
        self.assertEqual('test_family', api.character.model().family)

    def test_get_family(self):
        """
        get_family should return 'test_family'
        :return:
        """
        api.character.model().family = 'test_family'
        self.assertEqual('test_family', api.character.get_family())

    def test_get_family_no_family(self):
        """
        get_family should return None
        :return:
        """
        self.assertEqual(None, api.character.get_family())

    def test_get_clan_no_family(self):
        """
        get_clan should return None
        :return:
        """
        self.assertEqual(None, api.character.get_clan())

    def test_get_clan(self):
        """
        get_clan should return test_clan
        :return:
        """

        api.character.set_family('test_family')
        self.assertEqual('test_clan', api.character.get_clan())

    def test_get_family_tags(self):
        """
        get_family_tags() should returns the family and the clan id
        :return:
        """

        api.character.set_family('test_family')
        self.assertEqual(['test_family', 'test_clan'], api.character.get_family_tags())

    def test_get_family_tags_no_family(self):
        """
        get_family_tags() should returns an empty list
        :return:
        """

        self.assertEqual([], api.character.get_family_tags())

    def test_set_school(self):
        """

        :return:
        """
# coding=utf-8
# Copyright 2016 Mystopia.


from django.test import SimpleTestCase


class TestTrue(SimpleTestCase):
    def test_true_is_not_false(self):
        self.assertTrue(True is not False)

    def test_false_is_true_raises(self):
        with self.assertRaises(AssertionError):
            self.assertTrue(False)

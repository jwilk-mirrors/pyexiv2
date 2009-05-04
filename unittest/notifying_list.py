# -*- coding: utf-8 -*-

# ******************************************************************************
#
# Copyright (C) 2009 Olivier Tilloy <olivier@tilloy.net>
#
# This file is part of the pyexiv2 distribution.
#
# pyexiv2 is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# pyexiv2 is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with pyexiv2; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, 5th Floor, Boston, MA 02110-1301 USA.
#
# Author: Olivier Tilloy <olivier@tilloy.net>
#
# ******************************************************************************

import unittest
from pyexiv2 import ListenerInterface, NotifyingList
import random


class SimpleListener(ListenerInterface):

    # Total number of notifications
    notifications = 0
    # Last notification: (method_name, args)
    last = None

    def _notify(self, method_name, *args):
        self.notifications += 1
        self.last = (method_name, args)

    def items_changed(self, start_index, items):
        self._notify('items_changed', start_index, items)

    def items_deleted(self, start_index, end_index):
        self._notify('items_deleted', start_index, end_index)

    def items_inserted(self, start_index, items):
        self._notify('items_inserted', start_index, items)

    def reordered(self):
        self._notify('reordered')


class TestNotifyingList(unittest.TestCase):

    def setUp(self):
        self.values = NotifyingList([5, 7, 9, 14, 57, 3, 2])

    def test_no_listener(self):
        # No listener is registered, nothing should happen.
        self.values[3] = 13
        # TODO: test all operations (insertion, deletion, slicing, ...)

    def test_listener_interface(self):
        self.values.register_listener(ListenerInterface())
        self.failUnlessRaises(NotImplementedError, self.values.__setitem__, 3, 13)
        self.failUnlessRaises(NotImplementedError, self.values.__delitem__, 5)
        self.failUnlessRaises(NotImplementedError, self.values.append, 17)
        self.failUnlessRaises(NotImplementedError, self.values.extend, [11, 22])
        self.failUnlessRaises(NotImplementedError, self.values.insert, 4, 24)
        self.failUnlessRaises(NotImplementedError, self.values.pop)
        self.failUnlessRaises(NotImplementedError, self.values.remove, 9)
        # TODO: test all operations (insertion, slicing, ...)

    def test_multiple_listeners(self):
        # Register a random number of listeners
        listeners = [SimpleListener() for i in xrange(random.randint(3, 20))]
        for listener in listeners:
            self.values.register_listener(listener)

        self.values[3] = 13
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 3, 2])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 1)
            self.failUnlessEqual(listener.last, ('items_changed', (3, [13])))

        self.failUnlessRaises(IndexError, self.values.__setitem__, 9, 27)
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 3, 2])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 1)
            self.failUnlessEqual(listener.last, ('items_changed', (3, [13])))

        del self.values[5]
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 2])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 2)
            self.failUnlessEqual(listener.last, ('items_deleted', (5, 6)))

        self.failUnlessRaises(IndexError, self.values.__delitem__, 9)
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 2])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 2)
            self.failUnlessEqual(listener.last, ('items_deleted', (5, 6)))

        self.values.append(17)
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 2, 17])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 3)
            self.failUnlessEqual(listener.last, ('items_inserted', (6, [17])))

        self.values.extend([11, 22])
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 2, 17, 11, 22])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 4)
            self.failUnlessEqual(listener.last, ('items_inserted', (7, [11, 22])))

        self.failUnlessRaises(TypeError, self.values.extend, 26)
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 2, 17, 11, 22])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 4)
            self.failUnlessEqual(listener.last, ('items_inserted', (7, [11, 22])))

        self.values.insert(4, 24)
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 24, 57, 2, 17, 11, 22])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 5)
            self.failUnlessEqual(listener.last, ('items_inserted', (4, [24])))

        self.values.pop()
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 24, 57, 2, 17, 11])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 6)
            self.failUnlessEqual(listener.last, ('items_deleted', (9, 10)))

        self.values.pop(4)
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 2, 17, 11])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 7)
            self.failUnlessEqual(listener.last, ('items_deleted', (4, 5)))

        self.failUnlessRaises(IndexError, self.values.pop, 33)
        self.failUnlessEqual(self.values, [5, 7, 9, 13, 57, 2, 17, 11])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 7)
            self.failUnlessEqual(listener.last, ('items_deleted', (4, 5)))

        self.values.remove(9)
        self.failUnlessEqual(self.values, [5, 7, 13, 57, 2, 17, 11])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 8)
            self.failUnlessEqual(listener.last, ('items_deleted', (2, 3)))

        self.failUnlessRaises(ValueError, self.values.remove, 33)
        self.failUnlessEqual(self.values, [5, 7, 13, 57, 2, 17, 11])
        for listener in listeners:
            self.failUnlessEqual(listener.notifications, 8)
            self.failUnlessEqual(listener.last, ('items_deleted', (2, 3)))

        # TODO: test all operations (slicing, ...)

#!/usr/bin/env python

"""Tests for `map_widgets` module."""
import unittest

from geemap.core import core_map


class TestLeafletMap(unittest.TestCase):
    """Tests for the LeafletMap."""

    def setUp(self):
        self.leaflet_map = core_map.LeafletMap()

    def test_defaults(self):
        leaflet_map = core_map.LeafletMap()
        self.assertEqual(leaflet_map.width, "100%")
        self.assertEqual(leaflet_map.height, "600px")
        self.assertEqual(leaflet_map.center, (0, 0))
        self.assertEqual(leaflet_map.zoom, 2)

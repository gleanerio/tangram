"""
Tests for sotools methods

Run with::

  $ pytest

"""

from .. import *
import os
import tempfile

class TestCommon:


    def test_filenameFromUrl(self):
        url = "https://some.server/path/1/a/test.ttl"
        assert(filenameFromUrl(url) == "test.ttl")
        url = "https://some.server/path/1/a/"
        assert(filenameFromUrl(url) == "some.server-path_1_a")
        url = "https://search.dataone.org/view/https%3A%2F%2Fpasta.lternet.edu%2Fpackage%2Fmetadata%2Feml%2Fknb-lter-nwt%2F181%2F2.xml"
        assert (filenameFromUrl(url) == "2.xml")


    def test_downloadRdf(self):
        url = "http://www.w3.org/2000/01/rdf-schema"
        with tempfile.TemporaryDirectory() as tmpdirname:
            filename = os.path.join(tmpdirname, "test.ttl")
            downloadRDF(url, filename, src_format="n3", dest_format="turtle")
            assert(os.path.exists(filename))
            assert(os.stat(filename).st_size > 3000)


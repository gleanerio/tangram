'''
Tests for the app

Can be run with $ pytest app_tests

Assumes that app.py is running
'''
import pytest
import _pytest.capture
import requests


class TestTangram:

    def test_index(self):
        '''
        Check the service is running
        '''
        res = requests.get('http://localhost:8080')
        assert(res.status_code == 200)

    def test_upload(self, capsys):
        data = {
            "format":"bogus"
        }
        files = {
            "datagraph": open("../science-on-schema.org/validation/testingDataGraphs/ds_badns1.json","rb"),
            "shapegraph": open("../science-on-schema.org/validation/shapes/so_namespace.ttl","rb"),
        }
        url = "http://localhost:8080/verify"
        res = requests.post(url ,data=data, files=files)
        assert(res.status_code == 422)

        data = {
            "format":"turtle"
        }
        files = {
            "datagraph": open("../science-on-schema.org/validation/testingDataGraphs/ds_badns1.json","rb"),
            "shapegraph": open("../science-on-schema.org/validation/shapes/so_namespace.ttl","rb"),
        }
        res = requests.post(url ,data=data, files=files)
        with capsys.disabled():
            print("Tangram output = " + res.text)
        assert(res.status_code == 200)

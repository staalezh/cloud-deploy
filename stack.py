import json

class Stack:
    def __init__(self, root):
        self.root = root
        self.conf = {
            "AWSTemplateFormatVersion" : "2010-09-09",
            "Resources": {}
        }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def __str__(self):
        return json.dumps(self.conf)

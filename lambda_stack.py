#!/usr/bin/env python

import json
import glob
import os
import re

from stack import Stack

from os.path import dirname, basename, join

BUCKET = "gallereel-dev"

def camel2cstyle(name):
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

class LambdaStack(Stack):
    def __init__(self):
        Stack.__init__(self, "lambda")

    def create(self):
        for dir_path in glob.glob("{}/*".format(lambda_dir)):
            resource  = basename(dir_path)
            file_path = camel2cstyle(resource)

            template["Resources"][resource] = {
                "Type": "AWS::Lambda::Function",
                "Properties": {
                    "Code": {
                        "S3Bucket": BUCKET,
                        "S3Key": "lambda/{}.zip".format(resource)
                    },
                    "Handler": "{}.main".format(file_path),
                    "Role": "arn:aws:iam::858316877486:role/lambda",
                    "Runtime": "python2.7",
                    "Timeout": "5"
                }
            }

        target_path = join(self.root, 'lambda/dev.template')
        if not os.path.exists(os.path.dirname(target_path)):
            os.makedirs(os.path.dirname(target_path))

        with open(target_path, "w") as outfile:
            outfile.write(json.dumps(template,
                sort_keys=True,
                indent=4,
                separators=(',', ': ')))
 

    def deploy_code(self, code_dir):
        for dir_path in glob.glob(join(code_dir, "*")):
            dir_name = basename(dir_path)
            os.system(self.cmd(dir_path, dir_name, BUCKET))


    def cmd(self, dir_path, dir_name, bucket):
        cmd = """
            cd {Dir} && \
            zip {DirName}.zip *.py && \
            aws s3 cp {DirName}.zip s3://{Bucket}/lambda/ && \
            rm {DirName}.zip
            """.format(Dir=dir_path, DirName=dir_name, Bucket=bucket) 

        return cmd

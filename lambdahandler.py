# -*- coding: utf-8 -*-
import boto3
import ConfigParser
import datetime
import json
import os
import re

from os.path import join, basename, relpath
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED

s3 = boto3.resource('s3')

class LambdaHandler:
    def __init__(self, config):
        self.config = config

    def __call__(self, args):
        target = args.target
        function_name = self.config.get(target, 'name')
        handler = self.config.get(target, 'handler')

        if args.create:
            key = self.deploy(function_name, target)
            self.create_lambda(function_name, handler, key, target)

        if args.update:
            key = self.deploy(function_name, target)
            self.update_lambda(function_name, key, target)

        if args.publish:
            self.publish(function_name, args.alias)

        if args.destroy:
            self.destroy_lambda(function_name)

        return True

    def deploy(self, function_name, target):
        bucket = self.config.get(target, 'bucket')
        upload_key = "lambda/{}.zip".format(function_name)

        pyfile  = '^(.*)\.(py|cfg)$'
        libfile = '^(\.\/)?lib\/.*$'

        fileset = []
        for root, dirnames, filenames in os.walk(".", followlinks = True):
            for filename in filenames:
                path = join(root, filename)
                if re.match(pyfile, path) or re.match(libfile, path):
                    fileset += [path]

        zip_path = 'tmp.zip'
        with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zipfile:
            for path in fileset:
                print("Adding {} to archive...".format(path))
                zipfile.write(path, path)

            print("Writing aws.cfg...")
            info = ZipInfo('aws.cfg')
            info.external_attr = 0644 << 16L
            zipfile.writestr(info, "[AWS]\nenv = {}\n".format(target))

        print("Uploading zip file to S3...")
        s3.Bucket(bucket).upload_file(zip_path, upload_key)
        os.remove(zip_path)

        return upload_key

    def create_lambda(self, function_name, handler, upload_key, target):
        client = boto3.client('lambda')
        bucket = self.config.get(target, 'bucket')

        print("Creating lambda {}... \n".format(function_name))
        response = client.create_function(
                FunctionName = function_name,
                Runtime = 'python2.7',
                Role = 'arn:aws:iam::858316877486:role/lambda',
                Handler = handler,
                Code = { 'S3Bucket': bucket, 'S3Key': upload_key },
                Timeout = 5)

        print(self.format(response))

    def publish(self, function_name, alias):
        client = boto3.client('lambda')

        print("Publishing lambda...")
        response = client.publish_version(FunctionName = function_name)
        version  = response['Version']

        if alias is not None:
            print("Creating alias {} for version {}...".format(alias, version))
            client.delete_alias(FunctionName=function_name, Name=alias)

            client.create_alias(
                    FunctionName = function_name,
                    Name = alias,
                    FunctionVersion = version)

    def update_lambda(self, function_name, key, target):
        client = boto3.client('lambda')
        bucket = self.config.get(target, 'bucket')

        print("Updating lambda {}... \n".format(function_name))
        response = client.update_function_code(
                FunctionName = function_name,
                S3Bucket = bucket,
                S3Key = key)

        print(self.format(response))


    def destroy_lambda(self, function_name):
        client = boto3.client('lambda')

        print("Destroying lambda {}... \n".format(function_name))
        response = client.delete_function(FunctionName = function_name)

        print(self.format(response))

    def format(self, response):
        return json.dumps(response, sort_keys=True, indent=4, separators=(',', ': '))

from flask import Flask
import boto3


# Init Flask application object
app = Flask(__name__)
app.config.from_object('app.settings')

ec2 = boto3.resource('ec2', region_name='us-east-1')
ec2_client = boto3.client('ec2', region_name='us-east-1')
s3 = boto3.resource('s3', region_name='us-east-1')
cw = boto3.client('cloudwatch', region_name='us-east-1')
elb = boto3.client('elbv2', region_name='us-east-1')

# Register all blueprints
from .controllers import home
app.register_blueprint(home.bp, url_prefix='/')



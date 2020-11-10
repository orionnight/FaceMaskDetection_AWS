from flask import Blueprint, render_template
from flask import request, flash, redirect, url_for
import boto3
from datetime import timedelta, datetime

from app import cw


bp = Blueprint('home', __name__, template_folder='../templates')


@bp.route('/', methods=['GET', 'POST'])
def root():
    
    # instances = get_running_instances()

    # number of workers for the past 30 minutes

    # return render_template('home.html', instances=instances)
    return render_template('home.html')


@bp.route('/manager', methods=['GET', 'POST'])
def manager():
    
    # instances = get_running_instances()

    # number of workers for the past 30 minutes

    # return render_template('home.html', instances=instances)
    return render_template('manager.html')

def get_running_instances():
    ec2 = boto3.resource('ec2')
    instances = ec2.instances.filter(
        Filters=[{'Name': 'instance-state-name', 'Values': ['running','pending']},
                 {'Name': 'tag:Name', 'Values': ['worker']}])
    return instances


def get_num_workers():
    workers = cw.get_metric_statistics(
        Period = 60,
        StartTime = datetime.utcnow() - timedelta(seconds=30*60),
        EndTime = datetime.utcnow(),
        MetricName = 'NumWorkers',
        Namespace = 'AWS/EC2',
        Statistics = ['Average'],
        Dimensions = [{'Name': 'InstanceId', 'Value': 'i-078f69c8c9c0097d6'}]
    )

    return return_label_values(workers, 'Average')


def get_total_cpu_utilization(id):
    cpu = cw.get_metric_statistics(
        Period = 60,
        StartTime = datetime.utcnow() - timedelta(seconds=30*60),
        EndTime = datetime.utcnow(),
        MetricName = 'CPUUtilization',
        Namespace = 'AWS/EC2',
        Statistics = ['Average'],
        Dimensions = [{'Name': 'InstanceId', 'Value': id}]
    )
    return return_label_values(cpu, 'Average')


def get_http_request_rate(id):
    http = cw.get_metric_statistics(
        Period = 60,
        StartTime = datetime.utcnow() - timedelta(seconds=30*60),
        EndTime = datetime.utcnow(),
        MetricName = 'HTTPRequestRate',
        Namespace='AWS/EC2',
        Statistics = ['Sum'],
        Dimensions = [{'Name': 'InstanceId', 'Value': id}]
    )

    return return_label_values(http, 'Sum')

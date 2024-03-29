import time
from datetime import datetime, timedelta
import csv
import logging
import boto3

import os
import sys


ami_id = 'ami-0bf618774e7879c6a'
REGION = 'us-east-1'
#TEMPLATE_ID = 
#placement_group_name = 
#ELB_DNS =
#TARGET_ARN = 
#s3_bucketName = 

dir_path = os.path.dirname(os.path.realpath(__file__))
sys.path.append('../../')
sys.path.append(dir_path)

def get_auto_scale():
    folder = os.path.dirname(os.path.realpath(__file__))
    file_path = folder + '/auto_scale.txt'

    pool_size_upper_limit = 8
    pool_size_lower_limit = 1
    max_threshold = 0.0
    min_threshold = 0.0
    increase_rate = 0.0
    decrease_rate = 0.0
    auto_scale = 0

    flag = None

    #print(file_path)
    if os.path.exists(file_path):
        with open(file_path, newline ='') as csvfile:
            reader = csv.reader(csvfile, delimiter = ',')
            for row in reader:
                max_threshold = float(row[0])
                min_threshold = float(row[1])
                increase_rate = float(row[2])
                decrease_rate = float(row[3])
                auto_scale = int(row[4])
    else:
        logging.error('No file found')
        return None

    if int(auto_scale) == 1:
        ec2 = boto3.recource('ec2')     
        instances = ec2.instances.filter(
          Filters=[
              {'Name': 'placement-group-name',
               'Values': [placement_group_name]
               },
              {'Name': 'instance-state-name',
               'Values': ['running']
               },
          ]
        )

        cpu_stats_1min = []
        ids = []

        for instance in instances:
            ids.append(instance.id)
            client = boto3.client('cloudwatch')
            cpu_1min = client.get_metric_statistics(
                Namespace = 'AWS/EC2',
                MetricName = 'CPUUtilization',
                Dimensions = [
                    {
                        'Name': 'InstanceId',
                        'Value': instance.id
                    },
                ],
                StartTime = datetime.utcnow() - timedelta(seconds=2*60),
                EndTime = datetime.utcnow() - timedelta(seconds=1*60),
                Period = 60,
                Statistics = ['Average']
            )
            for datapoint in cpu_1min['Datapoints']:
                load = round(datapoint['Average'], 2)
                cpu_stats_1min.append(load)

        if len(cpu_stats_1min) == 0:
            average_load = 0
        else:
            average_load = sum(cpu_stats_1min)/len(cpu_stats_1min)
        
        #print(average_load)
        current_pool_size = len(ids)
        #print(ids)

        if average_load == -1:
            logging.error('No workers in the pool')
            return None 
        elif average_load > max_threshold:
            add_instance_num = int(current_pool_size * (increase_rate-1))
            if int(current_pool_size) >= pool_size_upper_limit:
                logging.warning('Pool size had reached upper limit') 
                return None 
            elif int(current_pool_size + add_instance_num) >= pool_size_upper_limit:
                logging.warning('Grow to the limit')
                add_instance_num = int(pool_size_upper_limit - current_pool_size)
            else:
                logging.warning('Grow {} instance'.format(add_instance_num))

            for i in range(add_instance_num):
                instances = ec2.create_instances(ImageId = ami_id, InstanceType = 't2.micro', MinCount = 1, MaxCount = 1,
                                                 Monitoring = {'Enable':True},
                                                 Placement = {'AvailabilityZone':'us-east-1c','GroupName':placement_group_name},
                                                 SecurityGroups = ['launch-wizard-02'],
                                                 KeyName = 'ece1779a2',
                                                 TagSpecifications = [
                                                     {
                                                         'ResourceType':'instance',
                                                         'Tags':[
                                                             {
                                                                 'Key':'Name',
                                                                 'Value':'add_workers'
                                                             },
                                                        ]
                                                     }, ], )

            #resize ELB
            for instance in instances:
                ec2 = boto3.recource('ec2')  
                instance.wait_until_running(
                    Filters=[
                        {
                            'Name': 'instance-id',
                            'Values': [
                                instance.id,
                            ]
                        },
                    ],
                )

                client = boto3.client('elbv2')
                client.register_targets(
                    TargetGroupArn = TARGET_ARN,
                    Targets = [
                        {
                            'Id':instance.id,
                        },
                    ],
                )

                waiter = client.get_waiter('target_in_service')
                waiter.wait(
                    TargetGroupArn = TARGET_ARN,
                    Targets = [
                        {
                            'Id':instance.id,
                        },
                    ],
                )
        elif average_load < min_threshold:
            minus_instance_num = int(current_pool_size) - int(current_pool_size/decrease_rate)
            if int(current_pool_size) <= pool_size_lower_limit:
                logging.warning('Pool size had reached lower limit')
                return None 
            elif int(current_pool_size - minus_instance_num) <= pool_size_lower_limit:
                logging.warning('Shrink to the limit')
                minus_instance_num = int(current_pool_size - pool_size_lower_limit)
            else:
                logging.warning('Shrink {} instance'.format(minus_instance_num))
            if minus_instance_num > 0:
                ids_delete = ids[:minus_instance_num]
                #resize ELB
                for id in ids_delete:
                    client = boto3.client('elbv2')
                    client.deregister_targets(
                        TargetGroupArn = TARGET_ARN,
                        Targets = [
                            {
                                'Id': id,
                            },
                        ],
                    )
                    waiter = client.get_waiter('target_deregistered')
                    waiter.wait(
                        TargetGroupArn = TARGET_ARN,
                        Targets = [
                            {
                                'Id': id,
                            },
                        ],
                    )
                for id in ids_delete:
                    ec2.instance.filter(InstanceIds=[id]).terminate()
    else:
        logging.error('Auto Scaler is unabled')
        return None 
    
    time.sleep(60)
    flag = 'Success'
    return 'Success'

if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    while True:
        #response = auto_scaling(aws_client)
        response = get_auto_scale()
        if response == 'Success':
            logging.info('Pool size grow or shrink succeeded, wait for 3 minutes')
            time.sleep(180)
        else:
            time.sleep(60)

import io
import os
import sys
import json
import boto3
import urllib3
import datetime
import pandas as pd
import awswrangler as wr
from awsglue.utils import getResolvedOptions


class Utils:
    def __init__(self):
        # Create connections
        self.s3_client = boto3.client('s3')
        self.glue_client = boto3.client('glue')
        self.event_client = boto3.client('cloudtrail')

    def get_data_from_s3(self):
        # Get event ID
        self.args = getResolvedOptions(sys.argv, ['WORKFLOW_NAME', 'WORKFLOW_RUN_ID'])
        self.event_id = self.glue_client.get_workflow_run_properties(Name=self.args['WORKFLOW_NAME'],
                                                                     RunId=self.args['WORKFLOW_RUN_ID'])[
                            'RunProperties'][
                            'aws:eventIds'][1:-1]
        # Get all NotifyEvent events for the last five minutes
        response = self.event_client.lookup_events(LookupAttributes=[{'AttributeKey': 'EventName',
                                                                      'AttributeValue': 'NotifyEvent'}],
                                                   StartTime=(datetime.datetime.now() - datetime.timedelta(minutes=5)),
                                                   EndTime=datetime.datetime.now())['Events']
        # Get the file name from event
        for i in range(len(response)):
            event_payload = json.loads(response[i]['CloudTrailEvent'])['requestParameters']['eventPayload']
            if event_payload['eventId'] == self.event_id:
                self.object_key = json.loads(event_payload['eventBody'])['detail']['object']['key']
                self.bucket_name = json.loads(event_payload['eventBody'])['detail']['bucket']['name']
        obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=self.object_key)

        return pd.read_csv(io.BytesIO(obj['Body'].read()))

    def send_notification(self, message):
        '''Send notification about failure to Slack channel.'''
        _url = 'https://hooks.slack.com/YOUR_HOOK'
        _msg = {'text': message}
        http = urllib3.PoolManager()
        resp = http.request(method='POST', url=_url, body=json.dumps(_msg).encode('utf-8'))


# Get file from S3
utils = Utils()
coffee_data = utils.get_data_from_s3()

# Make simple transformations with columns
if (coffee_data['Currency'] != 'USD').any():
    utils.send_notification('Unexpected currency was received.')
coffee_data.drop(['Currency'], axis=1)
coffee_data.dropna()
coffee_data['Average'] = coffee_data['High'] - coffee_data['Low']

# Save modified file
wr.s3.to_parquet(df=coffee_data, path=f's3://{utils.bucket_name.replace("raw", "processed")}/coffee_data.parquet')

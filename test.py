import influxdb_client, os, time
from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS

token = 'Z4wFFxS8oZZ_lOOsd1WnHeT5l1C1j44QoJurdWW7zViIBYEYRxSineixh1JzeDH6AulkGUFTQwLkaBJ_uwRO5A=='
org = "CENS"
url = "http://grafmon.local:8086"

write_client = influxdb_client.InfluxDBClient(url=url, token=token, org=org)
bucket="test"

write_api = write_client.write_api(write_options=SYNCHRONOUS)
   
for value in range(5):
  point = (
    Point("measurement1")
    .tag("tagname1", "tagvalue1")
    .field("field1", value)
  )
  write_api.write(bucket=bucket, org="CENS", record=point)
  time.sleep(1) # separate points by 1 second
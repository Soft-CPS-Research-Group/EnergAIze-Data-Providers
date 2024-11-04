import unittest
import json
import pika
from unittest.mock import patch, MagicMock
from ICTranslator import ICTranslator  # Assuming ICTranslator is in ICTranslator.py

class TestICTranslator(unittest.TestCase):
    
    def setUp(self):
        self.house_name = "Casa1"
        
        self.mock_configurations = {
            "internalAMQPServer": {
                "host": "localhost",
                "port": 5672
            },
            'maxReconnectAttempts': 3,
            "QueueSuffixes":{
                "MessageAggregator": "_prod",
                "AlgorithmReceiver": "_alg"
            },
            "messageIC":{
                "meter.values":"Non Shiftable Load [kWh]",
                "pv.production":"Solar Generation [kWh]",
                "battery.soc":"Battery Charging Energy [kWh]"
            },
            "ChargersSessionFormat": {
                "Charger Id": "",
                "EOT": 0,
                "EsocD": 0,
                "EAT": 0,
                "EsocA": 0,
                "soc": 0,
                "power": 0
            },
            "Users":{
                "path": "house_files/without_type/test4/others/Users.json"
            },
        }
        
        self.mock_users = {
            "Casa1": {
                "manuel.neuer@mail.com": {
                    "cards": [],
                    "EAT": "06:00:00",
                    "EOT": "15:00:00",
                    "vehicle.model": "",
                    "energy.min": 0,
                    "energy.total": 0,
                    "prioritary": False,
                    "optimization": True,
                    "EsocD": 90
                },
                "jan.oblak@mail.com": {
                    "cards": [],
                    "EAT": "06:30:00",
                    "EOT": "15:30:00",
                    "vehicle.model": "",
                    "energy.min": 0,
                    "energy.total": 0,
                    "prioritary": False,
                    "optimization": True,
                    "EsocD": 90
                },
                "alisson.becker@mail.com": {
                    "cards": [],
                    "EAT": "07:00:00",
                    "EOT": "16:00:00",
                    "vehicle.model": "",
                    "energy.min": 0,
                    "energy.total": 0,
                    "prioritary": False,
                    "optimization": True,
                    "EsocD": 90
                }
            }
        }
        
        self.devices = [
            {
                "label":"Non Shiftable Load [kWh]",
                "id":"meter2",
                "name":"Imported Active Energy",
                "measurementunit": "Kilowatt Hour" 
            },
            {
                "label": "Solar Generation [kWh]",
                "id":"solar2",
                "name":"Total Generated Active Energy",
                "measurementunit": "Kilowatt Hour" 
            },
            {
                "label": "ChargersSession",
                "id":"rft_p3",
                "serialNumber": "rft",
                "plug": "p3"
            },
            {
                "label": "ChargersSession",
                "id":"rft_p1",
                "serialNumber": "rft",
                "plug": "p1"
            }, 
            {
                "label": "ChargersSession",
                "id":"dee_p2",
                "serialNumber": "dee",
                "plug": "p2"
            }
        ]
        
        self.message = {
            "time": "2012-04-23T18:15:00.00Z",
            "battery.soc": 70,
            "pv.production": 85,
            "charging.session": [
                {
                    "id": 1,
                    "serialnumber": "rft",
                    "user.id": "manuel.neuer@mail.com",
                    "card.id": "xxxx",
                    "plug": "p3",
                    "soc": 45,
                    "power": 30
                },
                {
                    "id": 2,
                    "serialnumber": "rft",
                    "user.id": "jan.oblak@mail.com",
                    "card.id": "xxxx",
                    "plug": "p1",
                    "soc": 20,
                    "power": 50
                },
                {
                    "id": 3,
                    "serialnumber": "dee",
                    "user.id": "alisson.becker@mail.com",
                    "card.id": "xxxx",
                    "plug": "p2",
                    "soc": 65,
                    "power": 80
                }
            ]
        }
        
        # Patch DataSet.get_schema to return mock configurations and users
        self.patch_get_schema = patch('ICTranslator.DataSet.get_schema')
        self.mock_get_schema = self.patch_get_schema.start()
        self.mock_get_schema.side_effect = lambda path: self.mock_configurations if path.endswith('runtimeConfigurations.json') else self.mock_users
        
        # Patch pika.BlockingConnection
        self.MockBlockingConnection = patch('ICTranslator.pika.BlockingConnection')
        self.mock_blocking_connection = self.MockBlockingConnection.start()
        
        # Mock pika Connection and Channel
        self.mock_channel = MagicMock()
        self.mock_blocking_connection.return_value.channel.return_value = self.mock_channel
        
    def tearDown(self):
        # Stop patches
        self.patch_get_schema.stop()
        self.MockBlockingConnection.stop()
    
    def test_translate(self):
        # Expected messages
        expected_messages = [
            {
                "id": "solar2",
                "value": 85,
                "timestamp": 0
            },
            {
                "id": "rft_p3",
                "value": {
                    "Charger Id": "rft_p3",
                    "EOT": "15:00:00",
                    "EsocD": 90,
                    "EAT": "06:00:00",
                    "EsocA": -1,
                    "soc": 45,
                    "power": 30
                },
                "timestamp": 0
            },
            {
                "id": "rft_p1",
                "value": {
                    "Charger Id": "rft_p1",
                    "EOT": "15:30:00",
                    "EsocD": 90,
                    "EAT": "06:30:00",
                    "EsocA": -1,
                    "soc": 20,
                    "power": 50
                },
                "timestamp": 0
            },
            {
                "id": "dee_p2",
                "value": {
                    "Charger Id": "dee_p2",
                    "EOT": "16:00:00",
                    "EsocD": 90,
                    "EAT": "07:00:00",
                    "EsocA": -1,
                    "soc": 65,
                    "power": 80
                },
                "timestamp": 0
            }
        ]
        
        # Convert message to JSON bytes
        json_str = json.dumps(self.message)
        bytes_message = json_str.encode('utf-8')
        
        # Run the translate method
        ICTranslator.translate(self.house_name, self.devices, bytes_message)
        
        # Assert pika methods were called
        self.mock_blocking_connection.assert_called_once_with(pika.ConnectionParameters(host='localhost', port=5672))
        self.mock_channel.queue_declare.assert_called_once_with(queue='Casa1_prod', durable=True)
        
        # Assert messages were published to the queue
        self.assertEqual(self.mock_channel.basic_publish.call_count, len(expected_messages))
        
        # Assert each message published is as expected
        calls = self.mock_channel.basic_publish.call_args_list
        for idx, call_args in enumerate(calls):
            args, kwargs = call_args
            published_message = json.loads(kwargs['body'])
            
            # Print information for the test case
            print(f"Test Case {idx + 1}:")
            print(f"Expected Message: {expected_messages[idx]}")
            print(f"Actual Message  : {published_message}")
            
            # Check ID and value
            self.assertEqual(published_message['id'], expected_messages[idx]['id'])
            self.assertEqual(published_message['value'], expected_messages[idx]['value'])
            
            # Optionally, assert timestamp (if relevant to your test case)
            # self.assertEqual(published_message['timestamp'], expected_messages[idx]['timestamp'])
            
            print("Assertion passed: Message correctly serialized and sent.\n")

if __name__ == '__main__':
    unittest.main()

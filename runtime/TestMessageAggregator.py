import unittest
import json
import pika
from unittest.mock import patch, MagicMock
from datetime import datetime
from MessageAggregator import MessageAggregator

class TestMessageAggregator(unittest.TestCase):
    def setUp(self):
        # Setup
        self.house_name = "Casa1"
        self.devices = [
            {"label": "Battery Charging Energy [kWh]", "id": "bat2"},
            {"label": "Non Shiftable Load [kWh]", "id": "meter2"},
            {"label": "Solar Generation [kWh]", "id": "solar2"},
            {"label": "ChargersSession", "id": "rft_p3"},
            {"label": "ChargersSession", "id": "rft_p1"},
            {"label": "ChargersSession", "id": "dee_p2"}
        ]

        self.messages = [
            {"id": "bat2", "value": 3, "timestamp": 0},
            {"id": "meter2", "value": 90, "timestamp": 0},
            {"id": "solar2", "value": 85, "timestamp": 0},
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

        self.mock_configurations = {
            "internalAMQPServer": {
                "host": "localhost",
                "port": 5672
            },
            "frequency": {
                "value": 2,
                "unit": "minutes"
            },
            "AlgorithmAtributes": {
                "Month": "",
                "Hour": "",
                "Minute": "",
                "Day Type": "",
                "Non Shiftable Load [kWh]": "",
                "Solar Generation [kWh]": "",
                "Energy Price": "",
                "ChargersSession": [],
                "Generated": 0
            },
            "ChargersSessionFormat": {
                "Charger Id": "",
                "EOT": 0,
                "EsocD": 0,
                "EAT": 0,
                "EsocA": 0,
                "soc": 0,
                "power": 0
            }
        }

        self.patch_get_schema = patch('MessageAggregator.DataSet.get_schema')
        self.mock_get_schema = self.patch_get_schema.start()
        self.mock_get_schema.side_effect = lambda path: self.mock_configurations if path.endswith('runtimeConfigurations.json') else None
        self.mock_energy_price = patch('MessageAggregator.EnergyPrice')
        self.mock_energy_price_instance = self.mock_energy_price.start()
        self.mock_energy_price_instance.getEnergyPrice.return_value = 3

        # Patch pika.BlockingConnection
        self.MockBlockingConnection = patch('MessageAggregator.pika.BlockingConnection')
        self.mock_blocking_connection = self.MockBlockingConnection.start()
        
        # Mock pika Connection and Channel
        self.mock_channel = MagicMock()
        self.mock_blocking_connection.return_value.channel.return_value = self.mock_channel

    def tearDown(self):
        # Stop patches
        self.patch_get_schema.stop()
        self.MockBlockingConnection.stop()
        self.mock_energy_price.stop()

    def test_new_message(self):
        print("Starting test_new_message: Processing messages and verifying aggregated message generation.")
        expected_output = {
            "Month": 0,
            "Hour": 0,
            "Minute": 0,
            "Day Type": 0,
            "Non Shiftable Load [kWh]": 87,
            "Solar Generation [kWh]": 85,
            "Energy Price": 3,
            "ChargersSession": [
                {
                    "Charger Id": "rft_p3",
                    "EOT": "15:00:00",
                    "EsocD": 90,
                    "EAT": "06:00:00",
                    "EsocA": -1,
                    "soc": 45,
                    "power": 30
                },
                {
                    "Charger Id": "rft_p1",
                    "EOT": "15:30:00",
                    "EsocD": 90,
                    "EAT": "06:30:00",
                    "EsocA": -1,
                    "soc": 20,
                    "power": 50
                },
                {
                    "Charger Id": "dee_p2",
                    "EOT": "16:00:00",
                    "EsocD": 90,
                    "EAT": "07:00:00",
                    "EsocA": -1,
                    "soc": 65,
                    "power": 80
                }
            ],
            "Generated": 0
        }

        ma = MessageAggregator(self.devices, self.house_name)

        # Mock the timer to not start
        ma.start_timer = MagicMock()

        # Process the messages
        for msg in self.messages:
            ma.newMessage(None, None, None, json.dumps(msg).encode('utf-8'))

        # Manually call the send method
        ma.send()

        # Assert pika methods were called
        self.mock_blocking_connection.assert_called_once_with(pika.ConnectionParameters(host='localhost', port=5672))
        self.mock_channel.queue_declare.assert_called_once_with(queue='Casa1_alg', durable=True)

        # Assert basic_publish was called
        self.assertEqual(self.mock_channel.basic_publish.call_count, 1)

        calls = self.mock_channel.basic_publish.call_args_list
        for idx, call_args in enumerate(calls):
            args, kwargs = call_args
            published_message = json.loads(kwargs['body'])
            # Check main fields in published_message
            self.assertEqual(published_message["Non Shiftable Load [kWh]"], expected_output["Non Shiftable Load [kWh]"])
            self.assertEqual(published_message["Solar Generation [kWh]"], expected_output["Solar Generation [kWh]"])
            self.assertEqual(published_message["Energy Price"], expected_output["Energy Price"])
            self.assertEqual(published_message["Generated"], expected_output["Generated"])

            # Check ChargersSession (unordered comparison)
            self.assertEqual(len(published_message["ChargersSession"]), len(expected_output["ChargersSession"]))

            published_chargers_sessions = {
                tuple(session.items()) for session in published_message["ChargersSession"]
            }
            expected_chargers_sessions = {
                tuple(session.items()) for session in expected_output["ChargersSession"]
            }

            self.assertEqual(published_chargers_sessions, expected_chargers_sessions)
        print("Test passed successfully. All data was processed correctly.")
        ma.stop()

    def test_missing_solar_message(self):
        print("Starting test_missing_solar_message: Processing messages with missing solar panel and verifying substitution with zero.")
        # Messages except the message with id "solar2"
        messages_without_solar2 = [
            {"id": "bat2", "value": 3, "timestamp": 0},
            {"id": "meter2", "value": 90, "timestamp": 0},
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
                    "power":                     80
                },
                "timestamp": 0
            }
        ]

        expected_output = {
            "Month": 0,
            "Hour": 0,
            "Minute": 0,
            "Day Type": 0,
            "Non Shiftable Load [kWh]": 87,
            "Solar Generation [kWh]": 0,  # Expected value replaced with 0
            "Energy Price": 3,
            "ChargersSession": [
                {
                    "Charger Id": "rft_p3",
                    "EOT": "15:00:00",
                    "EsocD": 90,
                    "EAT": "06:00:00",
                    "EsocA": -1,
                    "soc": 45,
                    "power": 30
                },
                {
                    "Charger Id": "rft_p1",
                    "EOT": "15:30:00",
                    "EsocD": 90,
                    "EAT": "06:30:00",
                    "EsocA": -1,
                    "soc": 20,
                    "power": 50
                },
                {
                    "Charger Id": "dee_p2",
                    "EOT": "16:00:00",
                    "EsocD": 90,
                    "EAT": "07:00:00",
                    "EsocA": -1,
                    "soc": 65,
                    "power": 80
                }
            ],
            "Generated": 1
        }

        ma = MessageAggregator(self.devices, self.house_name)

        # Mock the timer to not start
        ma.start_timer = MagicMock()

        # Process the messages
        for msg in messages_without_solar2:
            ma.newMessage(None, None, None, json.dumps(msg).encode('utf-8'))

        # Manually call the send method
        ma.send()

        # Assert pika methods were called
        self.mock_blocking_connection.assert_called_once_with(pika.ConnectionParameters(host='localhost', port=5672))
        self.mock_channel.queue_declare.assert_called_once_with(queue='Casa1_alg', durable=True)

        # Assert basic_publish was called
        self.assertEqual(self.mock_channel.basic_publish.call_count, 1)

        calls = self.mock_channel.basic_publish.call_args_list
        for idx, call_args in enumerate(calls):
            args, kwargs = call_args
            published_message = json.loads(kwargs['body'])
            # Check main fields in published_message
            self.assertEqual(published_message["Non Shiftable Load [kWh]"], expected_output["Non Shiftable Load [kWh]"])
            self.assertEqual(published_message["Solar Generation [kWh]"], expected_output["Solar Generation [kWh]"])
            self.assertEqual(published_message["Energy Price"], expected_output["Energy Price"])
            self.assertEqual(published_message["Generated"], expected_output["Generated"])

            # Check ChargersSession (unordered comparison)
            self.assertEqual(len(published_message["ChargersSession"]), len(expected_output["ChargersSession"]))

            published_chargers_sessions = {
                tuple(session.items()) for session in published_message["ChargersSession"]
            }
            expected_chargers_sessions = {
                tuple(session.items()) for session in expected_output["ChargersSession"]
            }

            self.assertEqual(published_chargers_sessions, expected_chargers_sessions)
        print("Test passed successfully. Missing solar panel data was replaced with zero because there were no values in the substitute_dict to replace it.")
        ma.stop()

    def test_missing_solar_message_with_substitute(self):
        print("Starting test_missing_solar_message_with_substitute: Processing messages with missing solar panel data and verifying substitution by substitute_dict.")
        # Initialize substitute_dict with a value for 'solar2'
        ma = MessageAggregator(self.devices, self.house_name)
        ma._substitute_dict['solar2'] = {'timestamp': 0, 'data': 33, 'generated': 1}

        messages_without_solar2 = [
            {"id": "bat2", "value": 3, "timestamp": 0},
            {"id": "meter2", "value": 90, "timestamp": 0},
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

        expected_output = {
            "Month": 0,
            "Hour": 0,
            "Minute": 0,
            "Day Type": 0,
            "Non Shiftable Load [kWh]": 87,
            "Solar Generation [kWh]": 33,  # Should be replaced by the value from substitute_dict
            "Energy Price": 3,
            "ChargersSession": [
                {
                    "Charger Id": "rft_p3",
                    "EOT": "15:00:00",
                    "EsocD": 90,
                    "EAT": "06:00:00",
                    "EsocA": -1,
                    "soc": 45,
                    "power": 30
                },
                {
                    "Charger Id": "rft_p1",
                    "EOT": "15:30:00",
                    "EsocD": 90,
                    "EAT": "06:30:00",
                    "EsocA": -1,
                    "soc": 20,
                    "power": 50
                },
                {
                    "Charger Id": "dee_p2",
                    "EOT": "16:00:00",
                    "EsocD": 90,
                    "EAT": "07:00:00",
                    "EsocA": -1,
                    "soc": 65,
                    "power": 80
                }
            ],
            "Generated": 1
        }

        # Mock the timer to not start
        ma.start_timer = MagicMock()

        # Process the messages
        for msg in messages_without_solar2:
            ma.newMessage(None, None, None, json.dumps(msg).encode('utf-8'))

        # Manually call the send method
        ma.send()

        # Assert pika methods were called
        self.mock_blocking_connection.assert_called_once_with(pika.ConnectionParameters(host='localhost', port=5672))
        self.mock_channel.queue_declare.assert_called_once_with(queue='Casa1_alg', durable=True)

        # Assert basic_publish was called
        self.assertEqual(self.mock_channel.basic_publish.call_count, 1)

        calls = self.mock_channel.basic_publish.call_args_list
        for idx, call_args in enumerate(calls):
            args, kwargs = call_args
            published_message = json.loads(kwargs['body'])
            # Check main fields in published_message
            self.assertEqual(published_message["Non Shiftable Load [kWh]"], expected_output["Non Shiftable Load [kWh]"])
            self.assertEqual(published_message["Solar Generation [kWh]"], expected_output["Solar Generation [kWh]"])
            self.assertEqual(published_message["Energy Price"], expected_output["Energy Price"])
            self.assertEqual(published_message["Generated"], expected_output["Generated"])

            # Check ChargersSession (unordered comparison)
            self.assertEqual(len(published_message["ChargersSession"]), len(expected_output["ChargersSession"]))

            published_chargers_sessions = {
                tuple(session.items()) for session in published_message["ChargersSession"]
            }
            expected_chargers_sessions = {
                tuple(session.items()) for session in expected_output["ChargersSession"]
            }

            self.assertEqual(published_chargers_sessions, expected_chargers_sessions)
        print("Test passed successfully. Missing solar panel data was replaced by the value from substitute_dict.")
        ma.stop()

if __name__ == '__main__':
    unittest.main()


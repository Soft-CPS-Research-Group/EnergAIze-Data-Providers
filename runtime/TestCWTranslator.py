import unittest
from unittest.mock import Mock, patch
from datetime import datetime
import json

# Import the class or method you want to test
from runtime.Cleanwatts.CWTranslator import CWTranslator  # Replace 'your_module' with the actual module name

class TestCWTranslator(unittest.TestCase):
    
    def setUp(self):
        # Mock configurations
        self.configurations = {
            "internalAMQPServer": {
                "host": "localhost",
                "port": 5672
            },
            'maxReconnectAttempts': 3,
            "QueueSuffixes":{
                "MessageAggregator": "_prod",
                "AlgorithmReceiver": "_alg"
            }
        }
        
        self.house_name = "House1"
        
        # Mock datetime.now() to return a fixed timestamp
        self.fixed_timestamp = datetime(2024, 6, 14, 12, 0, 0)
        self.mock_datetime_now = Mock()
        self.mock_datetime_now.return_value = self.fixed_timestamp
        
        # Patch datetime.datetime.now to return our fixed timestamp
        self.patcher = patch('datetime.datetime')
        self.mock_datetime = self.patcher.start()
        self.mock_datetime.now.return_value = self.fixed_timestamp
        
    def tearDown(self):
        self.patcher.stop()
    
    def test_translate_multiple_messages(self):
        # Define input-output pairs
        test_cases = [
            {
                "input": {
                    "UnitId": 1017,
                    "Granularity": "Instant",
                    "TagId": 33683,
                    "Date": "2024-05-06T15:45:00",
                    "Read": 1.39825,
                    "ReadCurrency": 0,
                    "ReadCarbon": 0.4893875,
                    "Trees": 2.7965,
                    "Cars": 4.19475,
                    "Consumption": 0,
                    "CurrencySymbol": "€",
                    "ValueType": 0
                },
                "expected_output": {
                    "id": 33683,
                    "value": 1.39825,
                    "timestamp": self.fixed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
            },
            {
                "input": {
                    "UnitId": 1018,
                    "Granularity": "Hourly",
                    "TagId": 33684,
                    "Date": "2024-05-06T16:00:00",
                    "Read": 2.5,
                    "ReadCurrency": 0,
                    "ReadCarbon": 0.7,
                    "Trees": 5.0,
                    "Cars": 6.0,
                    "Consumption": 0,
                    "CurrencySymbol": "€",
                    "ValueType": 0
                },
                "expected_output": {
                    "id": 33684,
                    "value": 2.5,
                    "timestamp": self.fixed_timestamp.strftime("%Y-%m-%d %H:%M:%S")
                }
            },
            # Add more test cases as needed
        ]
        
        # Mock the connection and channel
        mock_channel = Mock()
        with patch('pika.BlockingConnection') as mock_blocking_connection:
            mock_blocking_connection.return_value.channel.return_value = mock_channel
            
            # Create an instance of CWTranslator
            translator = CWTranslator()
            
            # Iterate over test cases
            for idx, test_case in enumerate(test_cases):
                with self.subTest(test_case=test_case):
                    print(f"Running test case {idx + 1}: {test_case['input']} -> {test_case['expected_output']}")
                    
                    # Call the translate method with current test_case
                    translator.translate(self.house_name, [test_case["input"]])
                    
                    # Check if the message was correctly serialized and sent
                    message_bytes = json.dumps(test_case["expected_output"]).encode('utf-8')
                    mock_channel.basic_publish.assert_called_with(
                        exchange='', routing_key=f'{self.house_name}_prod', body=message_bytes)
                    
                    print("Assertion passed: Message correctly serialized and sent.")
                    
if __name__ == '__main__':
    unittest.main()

from utils.logging import Logging
from utils.data import DataSet

def load_configurations(config_file, name):
    configurations = DataSet.get_schema(config_file)
    logger = Logging(name,configurations)
    return configurations, logger

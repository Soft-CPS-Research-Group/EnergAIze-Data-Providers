from runtime.IDecisionForwarder import IDecisionForwarder
from utils.config_loader import load_configurations

configurations, logger = load_configurations('./configs/runtimeConfigurations.json',"icharging")

class ICDecisionForwarder(IDecisionForwarder):
    @staticmethod
    def toForward(result):
        #print(result)
        pass
    
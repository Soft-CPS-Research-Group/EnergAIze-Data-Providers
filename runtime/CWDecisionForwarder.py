from IDecisionForwarder import IDecisionForwarder

class CWDecisionForwarder(IDecisionForwarder):
    @staticmethod
    def toForward(result):
        print(result)
    
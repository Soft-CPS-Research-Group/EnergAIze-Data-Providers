from IDecisionForwarder import IDecisionForwarder

class ICDecisionForwarder(IDecisionForwarder):
    @staticmethod
    def toForward(result):
        print(result)
    
class IManager:
    def newMessage(self, ch, method, properties, body):
        raise NotImplementedError()

    def stop(self):
        raise NotImplementedError()

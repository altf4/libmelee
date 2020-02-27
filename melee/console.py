from abc import ABC, abstractmethod

class Console(ABC):
    def __init__(self, ai_port, opponent_port, opponent_type, logger=None):
        pass

    @abstractmethod
    def run():
        pass

    @abstractmethod
    def stop():
        pass

    @abstractmethod
    def step():
        pass

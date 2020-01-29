from abc import ABCMeta, abstractmethod

# Crawler interface
class Crawler(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, id, pw):
        pass

    @abstractmethod
    def crawl(self, query, start_date, end_date):
        pass

    @property
    @abstractmethod
    def data(self):
        pass

from abc import ABCMeta, abstractmethod

# Crawler interface
class Crawler(metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, *args, **kwargs):
        pass

    @abstractmethod
    def crawl(self, query, start_date, end_date, *args, **kwargs):
        """crawl method should scrap data related to `query` with range [`start_date`, `end_date]"""
        pass

    @abstractmethod
    def run(self, *args, **kwargs):
        """run method should be an entry point of Crawler behavior"""
        pass

    @property
    @abstractmethod
    def data(self):
        """data method should return scraped data after calling crawl method"""
        pass

    @abstractmethod
    def analyse(self, data=None):
        """analyse method should return analysed result from scraped data"""
        pass

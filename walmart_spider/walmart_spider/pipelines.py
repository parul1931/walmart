from scrapy import signals
from scrapy.exporters import CsvItemExporter

class CSVExportPipeline(object):
    counter = 0
    file_count = 1

    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        if spider.name != 'categories':
            file = open('%s_products_%s.csv' % (spider.name, self.file_count),
                        'w+b')
            self.files[spider] = file
            tag = spider.name + "_price"
            self.export_fields = ['title', 'upc', 'rank', 'category', tag, 'amazon_price1', 'amazon_price2', 'amazon_price3', 'weight', 'wt_cost', 'Tax_Cost', 'Fees', 'Tot_Cost', 'Profit', 'ROI']
            self.exporter = CsvItemExporter(file, fields_to_export=self.export_fields)
            self.exporter.start_exporting()

    def spider_closed(self, spider):
        if spider.name != 'categories':
            self.exporter.finish_exporting()
            file = self.files.pop(spider)
            file.close()

    def process_item(self, item, spider):
        if spider.name != 'categories':
            tag = spider.name + "_price"
            price = item.get(tag, None)
            upc = item.get('upc', None)
            if price and upc:
                self.counter += 1
                if self.counter == 10000:
                    self.exporter.finish_exporting()
                    file = self.files.pop(spider)
                    file.close()

                    self.file_count += 1

                    file = open('%s_products_%s.csv' % (spider.name,
                                                        self.file_count),
                                'w+b')
                    self.files[spider] = file
                    self.export_fields = ['title', 'upc', 'rank', 'category', tag, 'amazon_price1', 'amazon_price2', 'amazon_price3', 'weight', 'wt_cost', 'Tax_Cost', 'Fees', 'Tot_Cost', 'Profit', 'ROI']
                    self.exporter = CsvItemExporter(file, fields_to_export=self.export_fields)
                    self.exporter.start_exporting()

                    self.counter = 0
                print self.counter, '*'*50
                self.exporter.export_item(item)
        return item

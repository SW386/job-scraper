# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
from itemadapter import ItemAdapter
from sqlalchemy import create_engine
from sqlalchemy import Table, MetaData, Column, Integer, String

class CareersPipeline:

    def __init__(self, uri):
        self.database_uri = uri
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            uri=crawler.settings.get('DATABASE_URI'),
        )

    def open_spider(self, spider):
        
        metadata = MetaData()
        self.table = Table(
            'careers',
            metadata,
            Column('company', String),
            Column('job', String),
            Column('application', String),
            Column('category', String),
            Column('location', String)
        )
        self.engine = create_engine(self.database_uri)
        metadata.create_all(self.engine)
            

    def process_item(self, item, spider):

        try:
            adapter = ItemAdapter(item)
            with self.engine.begin() as conn:
                conn.execute(self.table.insert(), item)

        except Exception as e:
            print(e)
            raise DropItem(f"Error saving {item} in database")



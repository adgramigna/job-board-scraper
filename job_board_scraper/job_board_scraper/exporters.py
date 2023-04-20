from scrapy.exporters import BaseItemExporter
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
import logging


class ParquetItemExporter(BaseItemExporter):
    def __init__(self, pq_file, **kwargs):
        """
        Initialize exporter
        """
        super().__init__(dont_fail=True, **kwargs)
        self.file = pq_file  # file
        self.itemcount = 0  # initial item count
        self.columns = []  # initial columns to export
        self.pq_convertstr = False
        self.pq_items_rowgroup = 10000
        self.logger = logging.getLogger()

    def export_item(self, item):
        """
        Export a specific item to the file
        """
        # Initialize writer
        if len(self.columns) == 0:
            self._init_table(item)
        # Create a new row group to write
        if self.itemcount > self.pq_items_rowgroup:
            self._flush_table()
        # Add the item to data frame
        row = self._get_df_from_item(item)
        row_df = pd.DataFrame.from_dict(row, orient="index").T
        self.df = pd.concat(
            [self.df, row_df],
            ignore_index=True,
        )
        self.itemcount += 1
        return item

    def start_exporting(self):
        """
        Triggered when Scrapy starts exporting. Useful to configure headers etc.
        """
        self.firstBlock = True  # first block of parquet file

    def finish_exporting(self):
        """
        Triggered when Scrapy ends exporting. Useful to shutdown threads, close files etc.
        """
        self._flush_table()

    def _get_columns(self, item):
        """
        Determines the columns of an item
        """
        if isinstance(item, dict):
            # for dicts try using fields of the first item
            self.columns = list(item.keys())
        else:
            # use fields declared in Item
            self.columns = list(item.fields.keys())

    def _init_table(self, item):
        """
        Initializes table for parquet file
        """
        # initialize columns
        self._get_columns(item)
        self._reset_rowgroup()

    def _get_df_from_item(self, item):
        """
        Get the dataframe from item
        """
        row = {}
        fields = dict(self._get_serialized_fields(item, default_value=""))
        for column in self.columns:
            if self.pq_convertstr == True:
                row[column] = str(fields.get(column, None))
            else:
                value = fields.get(column, None)
                row[column] = value
        if self.pq_convertstr == True:
            return pd.DataFrame(row, index=[0]).astype(str)
        return row

    def _reset_rowgroup(self):
        """
        Reset dataframe for writing
        """
        if self.pq_convertstr == False:  # auto determine schema
            # initialize df
            self.df = pd.DataFrame(columns=self.columns)
        else:
            # initialize df with zero strings to derive correct schema
            self.df = pd.DataFrame(columns=self.columns).astype(str)

    def _flush_table(self):
        """
        Writes the current row group to parquet file
        """
        if len(self.df.index) > 0:
            # reset written entries
            self.itemcount = 0
            # write existing dataframe as rowgroup to parquet file
            papp = True
            if self.firstBlock == True:
                self.firstBlock = False
                papp = False

            # df = some pandas.DataFrame
            table = pa.Table.from_pandas(self.df)
            # buf = pa.BufferOutputStream()
            # self.logger.info(self.file, "FILE")
            pq.write_table(table, self.file)
            # fp_write(
            #     self.file,
            #     self.df,
            #     append=papp,
            #     compression="SNAPPY",
            #     # has_nulls=True,
            #     write_index=False,
            #     # file_scheme="simple",
            #     # object_encoding="utf8",
            #     # times="int64",
            #     # row_group_offsets=50000000,
            # )

            # initialize new data frame for new row group
            self._reset_rowgroup()

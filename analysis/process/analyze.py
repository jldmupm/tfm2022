import numpy as np
import pandas as pd
import dask.bag as db
import dask.dataframe as ddf

import analysis.process.merging as merge

def get_metadata():
    meta = pd.DataFrame([], columns=merge.MergeVoteWithMeasuresAvailableFields)
    meta.type = meta.type.astype(str)
    meta.subjectId = meta.subjectId.astype(str)
    meta.date = meta.date.astype(np.datetime64)
    meta.duration = meta.duration.astype(np.unsignedinteger)
    meta.room = meta.room.astype(str)
    meta.reasonString = meta.reasonString.astype(str)
    meta.category = meta.category.astype(str)
    meta.score = meta.score.astype(np.number)
    meta.reasonsList = meta.reasonsList.astype(object)
    meta.timestamp = meta.timestamp.astype(np.number)
    meta.sensor = meta.sensor.astype(object)
    meta.sensor_type = meta.sensor.astype(str)
    meta.sensor_id = meta.sensor_id.astype(str)
    meta.sensor_avg = meta.sensor_avg.astype(np.number)
    meta.sensor_count = meta.sensor_count.astype(np.unsignedinteger)
    meta.sensor_min = meta.sensor_min.astype(np.number)
    meta.sensor_max = meta.sensor_max.astype(np.number)

    return meta

def get_merged_dask_dataframe(bag: db.Bag) -> ddf.DataFrame:
    d_df: ddf.DataFrame = bag.to_dataframe(meta=get_metadata())
    return d_df
    
if __name__ == '__main__':
    import src.dask.setup_client
    src.dask.setup_client.setup()
    snd = merge.merge_from_file('./db/all_feedback_data.csv')
    d_df = get_merged_dask_dataframe(snd)
    
    sub_df: pd.DataFrame = d_df.compute()
    print(sub_df)
    print(sub_df.size) # rows x cols

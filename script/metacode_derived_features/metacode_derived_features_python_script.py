import dolphindb as ddb
import numpy as np
import pandas as pd
from joblib import delayed, Parallel
import datetime
from contextlib import contextmanager
import time

stockList = ['601318', '600519', '600036', '600276', '601166', '600030', '600887', '600016', '601328', '601288', '600000', '600585', '601398', '600031', '601668', '600048']
startDate = '2021.01.04'
endDate = '2021.01.05'
n_jobs = 8  # paralellism

s = ddb.session()
s.connect("192.168.1.1", 8848)
s.login("admin", "123456")

colNames = []
for i in range(10):
    colNames.append(f'BidPrice{i}')
    colNames.append(f'BidOrderQty{i}')
    colNames.append(f'OfferPrice{i}')
    colNames.append(f'OfferOrderQty{i}')
snapshot = s.run(f"""
    stockList={'`' + '`'.join(stockList)};
    dbName = "dfs://SH_TSDB_snapshot_MultiColumn";
    tableName = "snapshot";
    snapshot = loadTable(dbName, tableName);
    select DateTime, SecurityID, {', '.join(colNames)} from snapshot where date(DateTime) between {startDate} : {endDate}, SecurityID in stockList, (time(DateTime) between 09:30:00.000 : 11:29:59.999) or (time(DateTime) between 13:00:00.000 : 14:56:59.999)
""")
print('load done')
@contextmanager
def timer(name: str):
    s = time.time()
    yield
    elapsed = time.time() - s
    print(f'[{name}] {elapsed: .3f}sec')


def realizedVolatility(series):
    return np.sqrt(np.sum(series ** 2))


def log_return(series: np.ndarray):
    return np.log(series).diff().replace(np.NINF, np.nan).replace(np.inf, np.nan)


def calc_wap(bidPrice, offerPrice, bidOrderQty, offerOrderQty) -> pd.Series:
    return (bidPrice * offerOrderQty + offerPrice * bidOrderQty) / (bidOrderQty + offerOrderQty)


def timeResample(df):
    for i in range(10):
        df[f'LogReturn{i}'] = log_return(df[f'Wap{i}'])
        df[f'LogReturnOffer{i}'] = log_return(df[f'OfferPrice{i}'])
        df[f'LogReturnBid{i}'] = log_return(df[f'BidPrice{i}'])
    df['TimeGroup'] = df.name
    return df


def flattenMultIndex(multIndex, postfix=None):
    flattenNames = []
    for i in multIndex:
        if i[0] in ['SecurityID', 'TimeGroup']:
            flattenNames.append(i[0])
        else:
            if postfix is None:
                flattenNames.append('_'.join(list(i)))
            else:
                flattenNames.append('_'.join(list(i) + [postfix]))
    return flattenNames

features = {
    'SecurityID' : ['first'],
    'DateTime' : ['count'],
    'WapBalance' : [np.sum, np.mean, np.std],
    'PriceSpread' : [np.sum, np.mean, np.std],
    'BidSpread' : [np.sum, np.mean, np.std],
    'OfferSpread' : [np.sum, np.mean, np.std],
    'TotalVolume' : [np.sum, np.mean, np.std],
    'VolumeImbalance' : [np.sum, np.mean, np.std]
}

for i in range(10):
    features[f'Wap{i}'] = [np.sum, np.mean, np.std]
    features[f'LogReturn{i}'] = [np.sum, realizedVolatility, np.mean, np.std]
    features[f'LogReturnOffer{i}'] = [np.sum, realizedVolatility, np.mean, np.std]
    features[f'LogReturnBid{i}'] = [np.sum, realizedVolatility, np.mean, np.std]

def makeFeaturesParallel(data):
    pass
    data = data.resample('10min', on='DateTime').apply(timeResample)
    agg = data.groupby('TimeGroup').agg(features).reset_index(drop=False)
    agg.columns = flattenMultIndex(agg.columns)
    for time in [450, 300, 150]:
        d = data[data['DateTime'] >= data['TimeGroup'] + datetime.timedelta(seconds=time)].groupby('TimeGroup').agg(
            features).reset_index(drop=False)
        d.columns = flattenMultIndex(d.columns, str(time))
        agg = pd.merge(agg, d, on=['TimeGroup', 'SecurityID'], how='left')
    return agg

with timer(f"execution time of derived features: (n_jobs:{n_jobs}, stocks: {len(stockList)}, period: {startDate}-{endDate})"):
    for i in range(10):
        snapshot[f'Wap{i}'] = calc_wap(snapshot[f'BidPrice{i}'], snapshot[f'OfferPrice{i}'], snapshot[f'BidOrderQty{i}'],
                                   snapshot[f'OfferOrderQty{i}'])
    snapshot['WapBalance'] = abs(snapshot['Wap0'] - snapshot['Wap1'])
    snapshot['PriceSpread'] = (snapshot['OfferPrice0'] - snapshot['BidPrice0']) / ((snapshot['OfferPrice0'] + snapshot['BidPrice0']) / 2)
    snapshot['BidSpread'] = snapshot['BidPrice0'] - snapshot['BidPrice1']
    snapshot['OfferSpread'] = snapshot['OfferPrice0'] - snapshot['OfferPrice1']
    snapshot['TotalVolume'] = snapshot[[f'OfferOrderQty{i}' for i in range(10)] + [f'BidOrderQty{i}' for i in range(10)]].sum(axis=1)
    snapshot['VolumeImbalance'] = abs(snapshot[[f'OfferOrderQty{i}' for i in range(10)]].sum(axis=1) - snapshot[[f'BidOrderQty{i}' for i in range(10)]].sum(axis=1))
    snapshotFeatures = Parallel(n_jobs=n_jobs)(
        delayed(makeFeaturesParallel)(snapshot[snapshot['SecurityID'] == i]) for i in snapshot.SecurityID.unique())
    snapshotFeature = pd.concat(snapshotFeatures, ignore_index=True)
    snapshotFeature.rename(columns={'TimeGroup': 'DateTime'}, inplace=True)

# Remove records with NULL values
col_names = np.array(snapshotFeature.columns)
for i in col_names:
    snapshotFeature = snapshotFeature[~snapshotFeature[i].isnull()]

print(snapshotFeature)
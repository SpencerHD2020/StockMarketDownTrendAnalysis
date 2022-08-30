import requests, json, os, sys
import datetime as dt

url = "https://alpha-vantage.p.rapidapi.com/query"

headers = None
KEY_FILE_NAME = "keys.json"


if os.path.isfile(KEY_FILE_NAME):
    with open(KEY_FILE_NAME, "r") as f:
        headers = json.load(f)
else:
    print("ERROR: keys.json does not exist in this directory! Please add it with following params: X-RapidAPI-Key, X-RapidAPI-Host")
    sys.exit(1)
        
        
DEBUG = True

PRICE_ENUM = {
    "open": "1. open",
    "high": "2. high",
    "low": "3. low",
    "close": "4. close"
}
TICKR_SYM = "AAPL"
if len(sys.argv) > 1:
    TICKR_SYM = sys.argv[1]


def getStockData(symbol):
    """
    Fetches data about stock prices by day
    Args:
        symbol (String): Ticker Symbol you wish to search for
    Returns:
        {dateString: {"1. open": "265.8500",
            "2. high": "267.4000",
            "3. low": "263.8500",
            "4. close": "265.2300",
            "5. volume": "20319470"}}
    """
    querystring = {"function":"TIME_SERIES_DAILY","symbol":symbol,"outputsize":"compact","datatype":"json"}

    response = requests.request("GET", url, headers=headers, params=querystring)
    return response.json()["Time Series (Daily)"]


def getDateRange(data):
    """ Time based analytics about your stock data.

    Args:
        data (Object): Object full of other objects with string keys describing dates (IE: {"2022-08-29" : {...}})

    Returns:
        Object: {numDays: int, dateObjList: [dt.date], span: String}
    """
    dates = list()
    for date in dict.keys(data):
        dateParts = date.split("-")
        tempDate = dt.date(int(dateParts[0]), int(dateParts[1]), int(dateParts[2]))
        dates.append(tempDate)
    numDays = len(dates)
    dates.sort()
    if (DEBUG):
        lastDate = dates[(numDays - 1)]
        print(f"Collected Data over {numDays} days spanning from: {dates[0]} - {lastDate}")
    return {
        "numDays": numDays,
        "dateObjList": dates,
        "span": f"{dates[0]} - {lastDate}"
    }
    
def getTodaysPrices(data, timeData):
    """ Returns latest price data from passed data

    Args:
        data (Object): Object of price Objects indexed by date strings
        timeData (Object): {numDays: int, dateObjList: [dt.date], span: String}

    Returns:
        Object: Each Value (excluding volume) is a string representation of a float. Keys are "1. open" - "4. close"
    """
    latestDate = str(timeData["dateObjList"][(timeData["numDays"] - 1)])
    return data[latestDate]

def predictTomorrowsPrice(symbol):
    data = getStockData(symbol)
    timeAnalytics = getDateRange(data)
    print(getTodaysPrices(data, timeAnalytics))
    
    
# Volume on first day should be analyzed as it is the beginning of the trend
class DownWardTrend:
    def __init__(self, sampleDate, lastDate, volumeArray, prices):
        self.sampleDate = sampleDate
        self.lastDate = lastDate
        self.volumeArray = volumeArray
        self.prices = prices
        self.trendLength = self.findTrendLength()
        self.overallPriceDrop = self.prices[0] - self.prices[(len(self.prices) - 1)]
        self.volDownWithPriceDrop = 0
        self.volUpWithPriceDrop = 0
        self.mapVolumeVarianceToPriceDrops()
        
    def findTrendLength(self):
        return self.lastDate - self.sampleDate
    
    def mapVolumeVarianceToPriceDrops(self):
        for i in range((len(self.volumeArray) - 1)):
            curVol = self.volumeArray[i]
            nextVol = self.volumeArray[(i + 1)]
            if curVol > nextVol:
                self.volDownWithPriceDrop += 1
            else:
                self.volUpWithPriceDrop += 1
    
    
def averagePrices(priceObject):
    priceSum = 0.0
    for key in dict.keys(PRICE_ENUM):
        priceSum += float(priceObject[PRICE_ENUM[key]])
    return priceSum / (len(dict.keys(PRICE_ENUM)))
    
def analyzeVolumeOnDownTrends(symbol):
    data = getStockData(symbol)
    timeAnalytics = getDateRange(data)
    downTrends = []
    tempDownTrend = None
    trackingDT = False
    for i in range(timeAnalytics["numDays"]):
        # Make sure this is not the lest element
        if i == (timeAnalytics["numDays"] - 1):
            if trackingDT:
                # Finalize the current trend
                downTrends.append(tempDownTrend)
                tempDownTrend = None
                trackingDT = False
            break
        else:
            currentDate = timeAnalytics["dateObjList"][i]
            nextDate = timeAnalytics["dateObjList"][(i + 1)]
            currentPrices = data[str(currentDate)]
            nextPrices = data[str(nextDate)]
            currentAVG = averagePrices(currentPrices)
            nextAVG = averagePrices(nextPrices)
            if nextAVG < currentAVG:
                if trackingDT:
                    tempDownTrend.lastDate = nextDate
                    tempDownTrend.volumeArray.append(nextPrices["5. volume"])
                    tempDownTrend.prices.append(nextAVG)
                else:
                    tempDownTrend = DownWardTrend(currentDate, nextDate, 
                        [currentPrices["5. volume"], nextPrices["5. volume"]], [currentAVG, nextAVG]
                    )
                    trackingDT = True
            elif trackingDT:
                # Finalize the current trend
                downTrends.append(tempDownTrend)
                tempDownTrend = None
                trackingDT = False
    return downTrends


appleDownTrends = analyzeVolumeOnDownTrends(TICKR_SYM)
for trend in appleDownTrends:
    print("*" * 55)
    print(f"This trend lasted {trend.trendLength} days")
    print(f"Over this trend the price dropped ${round(trend.overallPriceDrop, 2)}")
    print(f"The volume decreased as price dropped {trend.volDownWithPriceDrop} times and increased {trend.volUpWithPriceDrop} times")
    print("*" * 55)
print(f"In this time span there were {len(appleDownTrends)} seperate downward trends.")
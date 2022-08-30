### Setup
- For this script to run properly you will need to create a free API Key from [this](https://rapidapi.com/alphavantage/api/alpha-vantage/) link.
- Then create a file in the same directory as main.py called keys.json.
- Add the following schema to the file:
- ```{"X-RapidAPI-Key": "{yourAPIKey}", "X-RapidAPI-Host": "{apiHost}"}```

### Usage
```python3 main.py {tickerSymbol}```

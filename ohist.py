# import sys
# import json
import dateutil.parser as dp
from datetime import datetime

import json
import requests
import logging

import calendar

import re
import time

import six
from abc import ABCMeta, abstractmethod

import charttools as chtl, charttools
import cfg

# import data.acct as acct
from importlib.machinery import SourceFileLoader

logger = logging.getLogger(__name__)

responses = {
    "_v3_instruments_instrument_orderbook": {
        "url": "/v3/instruments/{instrument}/orderBook",
        "instrument": "EUR_USD",
        "params": {},
        "response": {
             "orderBook": {
                "buckets": [
                  {
                    "price": "1.12850",
                    "shortCountPercent": "0.2352",
                    "longCountPercent": "0.2666"
                  },
                  {
                    "price": "1.12900",
                    "shortCountPercent": "0.2195",
                    "longCountPercent": "0.3293"
                  },
                  {
                    "price": "1.12950",
                    "shortCountPercent": "0.3136",
                    "longCountPercent": "0.2901"
                  },
                  {
                    "price": "1.13000",
                    "shortCountPercent": "0.3842",
                    "longCountPercent": "0.4156"
                  },
                  {
                    "price": "1.13050",
                    "shortCountPercent": "0.1960",
                    "longCountPercent": "0.3685"
                  },
                  {
                    "price": "1.13100",
                    "shortCountPercent": "0.2431",
                    "longCountPercent": "0.2901"
                  },
                  {
                    "price": "1.13150",
                    "shortCountPercent": "0.2509",
                    "longCountPercent": "0.3136"
                  },
                  {
                    "price": "1.13200",
                    "shortCountPercent": "0.2587",
                    "longCountPercent": "0.3450"
                  },
                  {
                    "price": "1.13250",
                    "shortCountPercent": "0.3842",
                    "longCountPercent": "0.2666"
                  },
                  {
                    "price": "1.13300",
                    "shortCountPercent": "0.3371",
                    "longCountPercent": "0.3371"
                  },
                  {
                    "price": "1.13350",
                    "shortCountPercent": "0.3528",
                    "longCountPercent": "0.2744"
                  },
                  {
                    "price": "1.13400",
                    "shortCountPercent": "0.3842",
                    "longCountPercent": "0.3136"
                  },
                  {
                    "price": "1.13450",
                    "shortCountPercent": "0.2039",
                    "longCountPercent": "0.2744"
                  },
                  {
                    "price": "1.13500",
                    "shortCountPercent": "0.1882",
                    "longCountPercent": "0.3371"
                  },
                  {
                    "price": "1.13550",
                    "shortCountPercent": "0.0235",
                    "longCountPercent": "0.0392"
                  },
                  {
                    "price": "1.13600",
                    "shortCountPercent": "0.0549",
                    "longCountPercent": "0.0314"
                  },
                  {
                    "price": "1.13650",
                    "shortCountPercent": "0.1333",
                    "longCountPercent": "0.0314"
                  },
                  {
                    "price": "1.13700",
                    "shortCountPercent": "0.1176",
                    "longCountPercent": "0.1019"
                  },
                  {
                    "price": "1.13750",
                    "shortCountPercent": "0.1568",
                    "longCountPercent": "0.0784"
                  },
                  {
                    "price": "1.13800",
                    "shortCountPercent": "0.1176",
                    "longCountPercent": "0.0862"
                  },
                  {
                    "price": "1.13850",
                    "shortCountPercent": "0.2117",
                    "longCountPercent": "0.1960"
                  },
                  {
                    "price": "1.13900",
                    "shortCountPercent": "0.4548",
                    "longCountPercent": "0.2587"
                  },
                  {
                    "price": "1.13950",
                    "shortCountPercent": "0.2979",
                    "longCountPercent": "0.3215"
                  },
                  {
                    "price": "1.14000",
                    "shortCountPercent": "0.7449",
                    "longCountPercent": "0.2901"
                  },
                  {
                    "price": "1.14050",
                    "shortCountPercent": "0.2117",
                    "longCountPercent": "0.1176"
                  },
                  {
                    "price": "1.14100",
                    "shortCountPercent": "0.1960",
                    "longCountPercent": "0.1333"
                  },
                  {
                    "price": "1.14150",
                    "shortCountPercent": "0.1882",
                    "longCountPercent": "0.1176"
                  },
                ],
                "instrument": "EUR_USD",
                "price": "1.13609",
                "bucketWidth": "0.00050",
                "time": "2017-06-28T10:00:00Z"
              }
        }
    },
    "_v3_instruments_instrument_positionbook": {
        "url": "/v3/instruments/{instrument}/positionBook",
        "instrument": "EUR_USD",
        "params": {},
        "response": {
              "positionBook": {
                "buckets": [
                  {
                    "price": "1.12800",
                    "shortCountPercent": "0.2670",
                    "longCountPercent": "0.2627"
                  },
                  {
                    "price": "1.12850",
                    "shortCountPercent": "0.2034",
                    "longCountPercent": "0.2712"
                  },
                  {
                    "price": "1.12900",
                    "shortCountPercent": "0.2034",
                    "longCountPercent": "0.2161"
                  },
                  {
                    "price": "1.12950",
                    "shortCountPercent": "0.2670",
                    "longCountPercent": "0.2839"
                  },
                  {
                    "price": "1.13000",
                    "shortCountPercent": "0.2755",
                    "longCountPercent": "0.3221"
                  },
                  {
                    "price": "1.13050",
                    "shortCountPercent": "0.1949",
                    "longCountPercent": "0.2839"
                  },
                  {
                    "price": "1.13100",
                    "shortCountPercent": "0.2288",
                    "longCountPercent": "0.2712"
                  },
                  {
                    "price": "1.13150",
                    "shortCountPercent": "0.2416",
                    "longCountPercent": "0.2712"
                  },
                  {
                    "price": "1.13200",
                    "shortCountPercent": "0.2204",
                    "longCountPercent": "0.3178"
                  },
                  {
                    "price": "1.13250",
                    "shortCountPercent": "0.2543",
                    "longCountPercent": "0.2458"
                  },
                  {
                    "price": "1.13300",
                    "shortCountPercent": "0.2839",
                    "longCountPercent": "0.2585"
                  },
                  {
                    "price": "1.13350",
                    "shortCountPercent": "0.3602",
                    "longCountPercent": "0.3094"
                  },
                  {
                    "price": "1.13400",
                    "shortCountPercent": "0.2882",
                    "longCountPercent": "0.3560"
                  },
                  {
                    "price": "1.13450",
                    "shortCountPercent": "0.2500",
                    "longCountPercent": "0.3009"
                  },
                  {
                    "price": "1.13500",
                    "shortCountPercent": "0.1738",
                    "longCountPercent": "0.3475"
                  },
                  {
                    "price": "1.13550",
                    "shortCountPercent": "0.2119",
                    "longCountPercent": "0.2797"
                  },
                  {
                    "price": "1.13600",
                    "shortCountPercent": "0.1483",
                    "longCountPercent": "0.3094"
                  },
                  {
                    "price": "1.13650",
                    "shortCountPercent": "0.1483",
                    "longCountPercent": "0.1314"
                  },
                  {
                    "price": "1.13700",
                    "shortCountPercent": "0.1568",
                    "longCountPercent": "0.2034"
                  },
                  {
                    "price": "1.13750",
                    "shortCountPercent": "0.1398",
                    "longCountPercent": "0.1271"
                  },
                  {
                    "price": "1.13800",
                    "shortCountPercent": "0.1314",
                    "longCountPercent": "0.2034"
                  },
                  {
                    "price": "1.13850",
                    "shortCountPercent": "0.1483",
                    "longCountPercent": "0.1695"
                  },
                  {
                    "price": "1.13900",
                    "shortCountPercent": "0.2924",
                    "longCountPercent": "0.1653"
                  },
                  {
                    "price": "1.13950",
                    "shortCountPercent": "0.1526",
                    "longCountPercent": "0.1865"
                  },
                  {
                    "price": "1.14000",
                    "shortCountPercent": "0.4365",
                    "longCountPercent": "0.2034"
                  },
                  {
                    "price": "1.14050",
                    "shortCountPercent": "0.1398",
                    "longCountPercent": "0.1144"
                  }
                ],
                "instrument": "EUR_USD",
                "price": "1.13609",
                "bucketWidth": "0.00050",
                "time": "2017-06-28T10:00:00Z"
              }
        }
    },
    "_v3_instruments_instrument_candles": {
        "url": "/v3/instruments/{instrument}/candles",
        "instrument": "DE30_EUR",
        "params": {
            "count": 5,
            "granularity": "M5"
        },
        "response": {
            "candles": [
                {
                  "volume": 132,
                  "time": "2016-10-17T19:35:00.000000000Z",
                  "complete": True,
                  "mid": {
                    "h": "10508.0",
                    "c": "10506.0",
                    "l": "10503.8",
                    "o": "10503.8"
                  }
                },
                {
                  "volume": 162,
                  "time": "2016-10-17T19:40:00.000000000Z",
                  "complete": True,
                  "mid": {
                    "h": "10507.0",
                    "c": "10504.9",
                    "l": "10502.0",
                    "o": "10506.0"
                  }
                },
                {
                  "volume": 196,
                  "time": "2016-10-17T19:45:00.000000000Z",
                  "complete": True,
                  "mid": {
                    "h": "10509.8",
                    "c": "10505.0",
                    "l": "10502.6",
                    "o": "10504.9"
                  }
                },
                {
                  "volume": 153,
                  "time": "2016-10-17T19:50:00.000000000Z",
                  "complete": True,
                  "mid": {
                    "h": "10510.1",
                    "c": "10509.0",
                    "l": "10504.2",
                    "o": "10505.0"
                  }
                },
                {
                  "volume": 172,
                  "time": "2016-10-17T19:55:00.000000000Z",
                  "complete": True,
                  "mid": {
                    "h": "10509.8",
                    "c": "10507.8",
                    "l": "10503.2",
                    "o": "10509.0"
                  }
                }
            ],
            "instrument": "DE30/EUR",
            "granularity": "M5"
        }
    }
}

def dyndoc_insert(src):
    """docstring_insert - a decorator to insert API-docparts dynamically."""
    # manipulating docstrings this way is tricky due to indentation
    # the JSON needs leading whitespace to be interpreted correctly
    import json
    import re

    def mkblock(d, flag=0):
        # response, pretty formatted
        v = json.dumps(d, indent=2)
        if flag == 1:
            # strip the '[' and ']' in case of a list holding items
            # that stand on their own (example: tick records from a stream)
            nw = re.findall('.*?\[(.*)\]', v, flags=re.S)
            v = nw[0]
        # add leading whitespace for each line and start with a newline
        return "\n{}".format("".join(["{0:>16}{1}\n".format("", L)
                             for L in v.split('\n')]))

    def dec(obj):
        allSlots = re.findall("\{(_v3.*?)\}", obj.__doc__)
        docsub = {}
        sub = {}
        for k in allSlots:
            p = re.findall("^(_v3.*)_(.*)", k)
            p = list(*p)
            sub.update({p[1]: p[0]})

        for v in sub.values():
            for k in sub.keys():
                docsub["{}_url".format(v)] = "{}".format(src[v]["url"])
                if "resp" == k:
                    docsub.update({"{}_resp".format(v):
                                   mkblock(src[v]["response"])})
                if "body" == k:
                    docsub.update({"{}_body".format(v):
                                   mkblock(src[v]["body"])})

                if "params" == k:
                    docsub.update({"{}_params".format(v):
                                   mkblock(src[v]["params"])})
                if "ciresp" == k:
                    docsub.update({"{}_ciresp".format(v):
                                   mkblock(src[v]["response"], 1)})

        obj.__doc__ = obj.__doc__.format(**docsub)

        return obj

    return dec

def endpoint(url, method="GET", expected_status=200):
    """endpoint - decorator to manipulate the REST-service endpoint.

    The endpoint decorator sets the endpoint and the method for the class
    to access the REST-service.
    """
    def dec(obj):
        obj.ENDPOINT = url
        obj.METHOD = method
        obj.EXPECTED_STATUS = expected_status
        return obj

    return dec

@six.add_metaclass(ABCMeta)
class APIRequest(object):
    """Base Class for API-request classes."""

    @abstractmethod
    def __init__(self, endpoint, method="GET", expected_status=200):
        """Instantiate an API request.

        Parameters
        ----------
        endpoint : string
            the URL format string

        method : string
            the method for the request. Default: GET.
        """
        self._expected_status = expected_status
        self._status_code = None
        self._response = None

        self._endpoint = endpoint
        self.method = method

    @property
    def expected_status(self):
        return self._expected_status

    @property
    def status_code(self):
        return self._status_code

    @status_code.setter
    def status_code(self, value):
        if value != self._expected_status:
            raise ValueError("{} {} {:d}".format(self, self.method, value))
        self._status_code = value

    @property
    def response(self):
        """response - get the response of the request."""
        return self._response

    @response.setter
    def response(self, value):
        """response - set the response of the request."""
        self._response = value

    def __str__(self):
        """return the endpoint."""
        return self._endpoint

class Instruments(APIRequest):
    """Instruments - abstract class to handle instruments endpoint."""

    ENDPOINT = ""
    METHOD = "GET"

    @abstractmethod
    @dyndoc_insert(responses)
    def __init__(self, instrument):
        """Instantiate a Instrument APIRequest instance.

        Parameters
        ----------
        instrument : string (required)
            the instrument to operate on

        params : dict with query parameters
        """
        endpoint = self.ENDPOINT.format(instrument=instrument)
        super(Instruments, self).__init__(endpoint, method=self.METHOD)


@endpoint("v3/instruments/{instrument}/candles")
class InstrumentsCandles(Instruments):
    """Get candle data for a specified Instrument."""

    @dyndoc_insert(responses)
    def __init__(self, instrument, params=None):
        """Instantiate an InstrumentsCandles request.

        Parameters
        ----------
        instrument : string (required)
            the instrument to fetch candle data for

        params : dict
            optional request query parameters, check developer.oanda.com
            for details


        Params example::

            {_v3_instruments_instrument_candles_params}


        Candle data example::

        >>> import oandapyV20
        >>> import oandapyV20.endpoints.instruments as instruments
        >>> client = oandapyV20.API(access_token=...)
        >>> params = ...
        >>> r = instruments.InstrumentsCandles(instrument="DE30_EUR",
        >>>                                    params=params)
        >>> client.request(r)
        >>> print r.response


        Output::

            {_v3_instruments_instrument_candles_resp}

        """
        super(InstrumentsCandles, self).__init__(instrument)
        self.params = params


@endpoint("v3/instruments/{instrument}/orderBook")
class InstrumentsOrderBook(Instruments):
    """Get orderbook data for a specified Instrument."""

    @dyndoc_insert(responses)
    def __init__(self, instrument, params=None):
        """Instantiate an InstrumentsOrderBook request.

        Parameters
        ----------
        instrument : string (required)
            the instrument to fetch candle data for

        params : dict
            optional request query parameters, check developer.oanda.com
            for details


        Params example::

            {_v3_instruments_instrument_orderbook_params}


        OrderBook data example::

        >>> import oandapyV20
        >>> import oandapyV20.endpoints.instruments as instruments
        >>> client = oandapyV20.API(access_token=...)
        >>> params = ...
        >>> r = instruments.InstrumentsOrderBook(instrument="EUR_USD",
        >>>                                      params=params)
        >>> client.request(r)
        >>> print r.response


        Output::

            {_v3_instruments_instrument_orderbook_resp}

        """
        super(InstrumentsOrderBook, self).__init__(instrument)
        self.params = params


@endpoint("v3/instruments/{instrument}/positionBook")
class InstrumentsPositionBook(Instruments):
    """Get positionbook data for a specified Instrument."""

    @dyndoc_insert(responses)
    def __init__(self, instrument, params=None):
        """Instantiate an InstrumentsPositionBook request.

        Parameters
        ----------
        instrument : string (required)
            the instrument to fetch candle data for

        params : dict
            optional request query parameters, check developer.oanda.com
            for details


        Params example::

            {_v3_instruments_instrument_positionbook_params}


        PositionBook data example::

        >>> import oandapyV20
        >>> import oandapyV20.endpoints.instruments as instruments
        >>> client = oandapyV20.API(access_token=...)
        >>> params = ...
        >>> r = instruments.InstrumentsPositionBook(instrument="EUR_USD",
        >>>                                         params=params)
        >>> client.request(r)
        >>> print r.response


        Output::

            {_v3_instruments_instrument_positionbook_resp}

        """
        super(InstrumentsPositionBook, self).__init__(instrument)
        self.params = params

def secs2time(e):
    """secs2time - convert epoch to datetime.

    >>> d = secs2time(1497499200)
    >>> d
    datetime.datetime(2017, 6, 15, 4, 0)
    >>> d.strftime("%Y%m%d-%H:%M:%S")
    '20170615-04:00:00'
    """
    w = time.gmtime(e)
    return datetime(*list(w)[0:6])


def granularity_to_time(s):
    """convert a named granularity into seconds.

    get value in seconds for named granularities: M1, M5 ... H1 etc.

    >>> print(granularity_to_time("M5"))
    300
    """
    mfact = {
        'S': 1,
        'M': 60,
        'H': 3600,
        'D': 86400,
        'W': 604800,
    }
    try:
        f, n = re.match("(?P<f>[SMHDW])(?:(?P<n>\d+)|)", s).groups()
        n = n if n else 1
        return mfact[f] * int(n)

    except Exception as e:
        raise ValueError(e)

MAX_BATCH = 5000
DEFAULT_BATCH = 500
ACTIVE_BATCH=DEFAULT_BATCH

def InstrumentsCandlesFactory(instrument, params=None):
    """InstrumentsCandlesFactory - generate InstrumentCandles requests.

    InstrumentsCandlesFactory is used to retrieve historical data by
    automatically generating consecutive requests when the OANDA limit
    of *count* records is exceeded.

    This is known by calculating the number of candles between *from* and
    *to*. If *to* is not specified *to* will be equal to *now*.

    The *count* parameter is only used to control the number of records to
    retrieve in a single request.

    The *includeFirst* parameter is forced to make sure that results do
    no have a 1-record gap between consecutive requests.

    Parameters
    ----------

    instrument : string (required)
        the instrument to create the order for

    params: params (optional)
        the parameters to specify the historical range,
        see the REST-V20 docs regarding 'instrument' at developer.oanda.com
        If no params are specified, just a single InstrumentsCandles request
        will be generated acting the same as if you had just created it
        directly.

    Example
    -------

    The *oandapyV20.API* client processes requests as objects. So,
    downloading large historical batches simply comes down to:

    >>> import json
    >>> from oandapyV20 import API
    >>> from oandapyV20.contrib.factories import InstrumentsCandlesFactory
    >>>
    >>> client = API(access_token=...)
    >>> instrument, granularity = "EUR_USD", "M15"
    >>> _from = "2017-01-01T00:00:00Z"
    >>> params = {
    ...    "from": _from,
    ...    "granularity": granularity,
    ...    "count": 2500,
    ... }
    >>> with open("/tmp/{}.{}".format(instrument, granularity), "w") as OUT:
    >>>     # The factory returns a generator generating consecutive
    >>>     # requests to retrieve full history from date 'from' till 'to'
    >>>     for r in InstrumentsCandlesFactory(instrument=instrument,
    ...                                        params=params)
    >>>         client.request(r)
    >>>         OUT.write(json.dumps(r.response.get('candles'), indent=2))

    .. note:: Normally you can't combine *from*, *to* and *count*.
              When *count* specified, it is used to calculate the gap between
              *to* and *from*. The *params* passed to the generated request
              itself does contain the *count* parameter.

    """
    RFC3339 = "%Y-%m-%dT%H:%M:%SZ"

    # if not specified use the default of 'S5' as OANDA does
    gs = granularity_to_time(params.get('granularity', 'S5'))

    _from = None
    _epoch_from = None
    if 'from' in params:
        _from = datetime.strptime(params.get('from'), RFC3339)
        _epoch_from = int(calendar.timegm(_from.timetuple()))

    _to = datetime.utcnow()
    if 'to' in params:
        _tmp = datetime.strptime(params.get('to'), RFC3339)
        # if specified datetime > now, we use 'now' instead
        if _tmp > _to:
            logger.info("datetime %s is in the future, will be set to 'now'",
                        params.get('to'))
        else:
            _to = _tmp

    _epoch_to = int(calendar.timegm(_to.timetuple()))

    _count = params.get('count', ACTIVE_BATCH)
    # OANDA will respond with a V20Error if count > MAX_BATCH

    if 'to' in params and 'from' not in params:
        raise ValueError("'to' specified without 'from'")

    if not params or 'from' not in params:
        yield InstrumentsCandles(instrument=instrument,
                                             params=params)

    else:
        delta = _epoch_to - _epoch_from
        nbars = delta / gs

        cpparams = params.copy()
        for k in ['count', 'from', 'to']:
            if k in cpparams:
                del cpparams[k]
        # force includeFirst
        cpparams.update({"includeFirst": True})

        # generate InstrumentsCandles requests for all 'bars', each request
        # requesting max. count records
        for _ in range(_count, int(((nbars//_count)+1))*_count+1, _count):
            to = _epoch_from + _count * gs
            if to > _epoch_to:
                to = _epoch_to
            yparams = cpparams.copy()
            yparams.update({"from": secs2time(_epoch_from).strftime(RFC3339)})
            yparams.update({"to": secs2time(to).strftime(RFC3339)})
            yield InstrumentsCandles(instrument=instrument,
                                                 params=yparams)
            _epoch_from = to


class V20Error(Exception):
    """Generic error class.

    In case of HTTP response codes >= 400 this class can be used
    to raise an exception representing that error.
    """

    def __init__(self, code, msg):
        """Instantiate a V20Error.

        Parameters
        ----------
        code : int
            the HTTP-code of the response

        msg : str
            the message returned with the response
        """
        self.code = code
        self.msg = msg

        super(V20Error, self).__init__(msg)

ITER_LINES_CHUNKSIZE = 60

TRADING_ENVIRONMENTS = {
    "practice": {
        "stream": 'https://stream-fxpractice.oanda.com',
        "api": 'https://api-fxpractice.oanda.com'
    },
    "live": {
        "stream": 'https://stream-fxtrade.oanda.com',
        "api": 'https://api-fxtrade.oanda.com'
    }
}

DEFAULT_HEADERS = {
    "Accept-Encoding": "gzip, deflate"
}

class API(object):
    r"""API - class to handle APIRequests objects to access API endpoints.

    Examples
    --------

    ::

        # get a list of trades
        from oandapyV20 import API
        import oandapyV20.endpoints.trades as trades

        api = API(access_token="xxx")
        accountID = "101-305-3091856-001"

        r = trades.TradesList(accountID)
        # show the endpoint as it is constructed for this call
        print("REQUEST:{}".format(r))
        rv = api.request(r)
        print("RESPONSE:\n{}".format(json.dumps(rv, indent=2)))


    Output::

        REQUEST:v3/accounts/101-305-3091856-001/trades
        RESPONSE:
        "trades": [
            {
              "financing": "0.0000",
              "openTime": "2016-07-21T15:47:05.170212014Z",
              "price": "10133.9",
              "unrealizedPL": "8.0000",
              "realizedPL": "0.0000",
              "instrument": "DE30_EUR",
              "state": "OPEN",
              "initialUnits": "-10",
              "currentUnits": "-10",
              "id": "1032"
            },
            {
              "financing": "0.0000",
              "openTime": "2016-07-21T15:47:04.963590941Z",
              "price": "10134.4",
              "unrealizedPL": "13.0000",
              "realizedPL": "0.0000",
              "instrument": "DE30_EUR",
              "state": "OPEN",
              "initialUnits": "-10",
              "currentUnits": "-10",
              "id": "1030"
            }
          ],
          "lastTransactionID": "1040"
        }

    ::

        # reduce a trade by it's id
        from oandapyV20 import API
        import oandapyV20.endpoints.trades as trades

        api = API(access_token="...")

        accountID = "101-305-3091856-001"
        tradeID = "1030"
        cfg = {"units": 5}
        r = trades.TradeClose(accountID, tradeID=tradeID, data=cfg)
        # show the endpoint as it is constructed for this call
        print("REQUEST:{}".format(r))
        rv = api.request(r)
        print("RESPONSE\n{}".format(json.dumps(rv, indent=2)))

    or by using it in a *with context*:

    ::

        with API(access_token="...") as api:

            accountID = "101-305-3091856-001"
            tradeID = "1030"
            cfg = {"units": 5}
            r = trades.TradeClose(accountID, tradeID=tradeID, data=cfg)
            # show the endpoint as it is constructed for this call
            print("REQUEST:{}".format(r))
            rv = api.request(r)
            print("RESPONSE\n{}".format(json.dumps(rv, indent=2)))

    in this case the API-client instance *api* will close connections
    explicitely.

    Output::

        REQUEST:v3/accounts/101-305-3091856-001/trades/1030/close
        RESPONSE: {
          "orderFillTransaction": {
            "orderID": "1041",
            "financing": "-0.1519",
            "instrument": "DE30_EUR",
            "userID": 1435156,
            "price": "10131.6",
            "tradeReduced": {
              "units": "5",
              "financing": "-0.1519",
              "realizedPL": "14.0000",
              "tradeID": "1030"
            },
            "batchID": "1041",
            "accountBalance": "44876.2548",
            "reason": "MARKET_ORDER_TRADE_CLOSE",
            "time": "2016-07-21T17:32:51.361464739Z",
            "units": "5",
            "type": "ORDER_FILL",
            "id": "1042",
            "pl": "14.0000",
            "accountID": "101-305-3091856-001"
          },
          "orderCreateTransaction": {
            "timeInForce": "FOK",
            "positionFill": "REDUCE_ONLY",
            "userID": 1435156,
            "batchID": "1041",
            "instrument": "DE30_EUR",
            "reason": "TRADE_CLOSE",
            "tradeClose": {
              "units": "5",
              "tradeID": "1030"
            },
            "time": "2016-07-21T17:32:51.361464739Z",
            "units": "5",
            "type": "MARKET_ORDER",
            "id": "1041",
            "accountID": "101-305-3091856-001"
          },
          "relatedTransactionIDs": [
            "1041",
            "1042"
          ],
          "lastTransactionID": "1042"
        }
    """

    def __init__(self, access_token, environment="practice",
                 headers=None, request_params=None):
        """Instantiate an instance of OandaPy's API wrapper.

        Parameters
        ----------
        access_token : string
            Provide a valid access token.

        environment : string
            Provide the environment for OANDA's REST api. Valid values:
            'practice' or 'live'. Default: 'practice'.

        headers : dict (optional)
            Provide request headers to be set for a request.


        .. note::

            There is no need to set the 'Content-Type: application/json'
            for the endpoints that require this header. The API-request
            classes covering those endpoints will take care of the header.

        request_params : (optional)
            parameters to be passed to the request. This can be used to apply
            for instance a timeout value:

               request_params={"timeout": 0.1}

            See specs of the requests module for full details of possible
            parameters.

        .. warning::
            parameters belonging to a request need to be set on the
            requestinstance and are NOT passed via the client.

        """
        logger.info("setting up API-client for environment %s", environment)
        try:
            TRADING_ENVIRONMENTS[environment]

        except KeyError as err:  # noqa F841
            logger.error("unkown environment %s", environment)
            raise KeyError("Unknown environment: {}".format(environment))

        else:
            self.environment = environment

        self.access_token = access_token
        self.client = requests.Session()
        self.client.stream = False
        self._request_params = request_params if request_params else {}

        # personal token authentication
        if self.access_token:
            self.client.headers['Authorization'] = 'Bearer '+self.access_token

        self.client.headers.update(DEFAULT_HEADERS)
        if headers:
            self.client.headers.update(headers)
            logger.info("applying headers %s", ",".join(headers.keys()))

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """close.

        explicit close of the session.
        """
        self.client.close()

    @property
    def request_params(self):
        """request_params property."""
        return self._request_params

    def __request(self, method, url, request_args, headers=None, stream=False):
        """__request.

        make the actual request. This method is called by the
        request method in case of 'regular' API-calls. Or indirectly by
        the__stream_request method if it concerns a 'streaming' call.
        """
        func = getattr(self.client, method)
        headers = headers if headers else {}
        response = None
        try:
            logger.info("performing request %s", url)
            response = func(url, stream=stream, headers=headers,
                            **request_args)
        except requests.RequestException as err:
            logger.error("request %s failed [%s]", url, err)
            raise err

        # Handle error responses
        if response.status_code >= 400:
            logger.error("request %s failed [%d,%s]",
                         url,
                         response.status_code,
                         response.content.decode('utf-8'))
            raise V20Error(response.status_code,
                           response.content.decode('utf-8'))
        return response

    def __stream_request(self, method, url, request_args, headers=None):
        """__stream_request.

        make a 'stream' request. This method is called by
        the 'request' method after it has determined which
        call applies: regular or streaming.
        """
        headers = headers if headers else {}
        response = self.__request(method, url, request_args,
                                  headers=headers, stream=True)
        lines = response.iter_lines(ITER_LINES_CHUNKSIZE)
        for line in lines:
            if line:
                data = json.loads(line.decode("utf-8"))
                yield data

    def request(self, endpoint):
        """Perform a request for the APIRequest instance 'endpoint'.

        Parameters
        ----------
        endpoint : APIRequest
            The endpoint parameter contains an instance of an APIRequest
            containing the endpoint, method and optionally other parameters
            or body data.

        Raises
        ------
            V20Error in case of HTTP response code >= 400
        """
        method = endpoint.method
        method = method.lower()
        params = None
        try:
            params = getattr(endpoint, "params")
        except AttributeError:
            # request does not have params
            params = {}

        headers = {}
        if hasattr(endpoint, "HEADERS"):
            headers = getattr(endpoint, "HEADERS")

        request_args = {}
        if method == 'get':
            request_args['params'] = params
        elif hasattr(endpoint, "data") and endpoint.data:
            request_args['json'] = endpoint.data

        # if any parameter for request then merge them
        request_args.update(self._request_params)

        # which API to access ?
        if not (hasattr(endpoint, "STREAM") and
                getattr(endpoint, "STREAM") is True):
            url = "{}/{}".format(
                TRADING_ENVIRONMENTS[self.environment]["api"],
                endpoint)

            response = self.__request(method, url,
                                      request_args, headers=headers)
            content = response.content.decode('utf-8')
            content = json.loads(content)

            # update endpoint
            endpoint.response = content
            endpoint.status_code = response.status_code

            return content

        else:
            url = "{}/{}".format(
                TRADING_ENVIRONMENTS[self.environment]["stream"],
                endpoint)
            endpoint.response = self.__stream_request(method,
                                                      url,
                                                      request_args,
                                                      headers=headers)
            return endpoint.response

#re-format function
def output(_from,_to,gran, instr):
    acct=SourceFileLoader(cfg.ACCT_FILE,cfg.DATA_DIR+cfg.ACCT_FILE).load_module()
    access_token = acct.API_KEY
    client = API(access_token=access_token)
    from fetcher import oa_dict
    params = {
        "granularity": gran,
        "from": _from,
        "to": _to
    }

    def cnv(r, h):
        for candle in r.get('candles'):
            ctime = candle.get('time')[0:19]
            try:
                nowt=datetime.now().timestamp()
                offset=(datetime.fromtimestamp(nowt) - datetime.utcfromtimestamp(nowt)).total_seconds()
                rec = "{time},{o},{h},{l},{c}".format(
                    time=int(dp.parse(ctime).timestamp()+offset),
                    o=candle['mid']['o'],
                    h=candle['mid']['h'],
                    l=candle['mid']['l'],
                    c=candle['mid']['c'],
                )
            except Exception as e:
                pass
                #print(e, r)
            else:
                h.write(rec+"\n")
    
    filename=None
    try:
        #Dummy request to check whether the connection is operational. 
        #If it fails than the main request is not processed either
        for r in InstrumentsCandlesFactory(instrument=instr,params=dict(granularity=gran, count=3)):
            sts=client.request(r)
        #main request:
        symb=instr.replace('_','')
        tf=oa_dict[gran]['tf']
        filename=chtl.symbol_to_filename(symb,tf,True)
        # "{}{}_{}.csv".format(cfg.DATA_SYMBOLS_DIR,symb, tf)
        with open(filename, "w") as f:  
            for r in InstrumentsCandlesFactory(instrument=instr, params=params):
                # print("REQUEST: {} {} {}".format(r, r.__class__.__name__, r.params))
                rv = client.request(r)
                cnv(r.response, f) #note that rv==r.response and is interchangeable
    except Exception: pass
    
    return filename

if __name__=='__main__':
    output('2017-01-01T00:00:00Z', '2017-06-30T00:00:00Z', 'H4', 'EUR_USD')
<p align="center"><img src="https://raw.githubusercontent.com/Belikhun/dhs-frontend/master/assets/img/icon%40128x128.png" width="96" height="96" alt="Deal Hunter Suite logo"></p>

# dhs-proxy

The proxy server of **Deal Hunter Suite**. It runs on Android phones under Termux and sends the extension's requests out through each phone's own connection.

## What is here

- `proxy.py`: a small threaded HTTP server on port 25685. `/heartbeat` reports the phone's CPU,
  memory and address, `/request` performs a request with pycurl and returns the answer, and
  `/cookie` reads a cookie from one of its cookie jars.
- `init`: sets a fresh Termux install up (packages and Python requirements).
- `update.py`: pulls the newest build from
  [dhs-proxy-build](https://github.com/Belikhun/dhs-proxy-build).
- `build/`: compiles the server and pushes the build.

The extension scans the local network for phones answering on that port and spreads a script's
requests across them.

## Running it

In Termux, with Python 3.9:

```
./init
python proxy.py
```

## The suite

| Repository | What it is |
| --- | --- |
| [dhs-frontend](https://github.com/Belikhun/dhs-frontend) | the Chrome extension |
| [dhs-backend](https://github.com/Belikhun/dhs-backend) | the licence and script server, with its web console |
| [dhs-proxy](https://github.com/Belikhun/dhs-proxy) | the proxy server that runs on Android phones |
| [dhs-proxy-build](https://github.com/Belikhun/dhs-proxy-build) | compiled builds of the proxy, which phones update from |
| [dhs-archive](https://github.com/Belikhun/dhs-archive) | every packaged release of the extension from 3.0 |

## Status

Deal Hunter Suite was a commercial product from 2019 to early 2022 and is no longer in service.
Its servers are offline, so nothing here runs out of the box, and the marketplace scripts were
written against sites that have changed since. The code is published as it was, for reference.
It is not affiliated with any of the marketplaces it worked on.

More of my work is on [belikhun.dev](https://belikhun.dev).

## Licence

MIT. See [LICENSE](LICENSE).

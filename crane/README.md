<!-- markdownlint-disable MD033 -->

[![Build Status](https://travis-ci.com/snuspl/crane.svg?token=q2afY56xJcDx5qxq3otD&branch=master)](https://travis-ci.com/snuspl/crane)

# Crane: GPU Cluster Manager with Batteries Included

<p align="center">
  <img src="../docs/pages/assets/image/title-light.svg" alt="Crane Logo">
</p>

Crane is an open-source GPU cluster manager with Batteries included.

# Installation

> Crane requires python 3.9 and above.

See [installation](docs/INSTALL.md)

For installing for development, see [hacking](docs/HACKING.md)

# Testing

To run lint,

```Bash
make lint
```

To test code,

```Bash
make alltest  # runs every test (slow)
make e2etest  # runs only end to end test
make inttest  # runs integration test
make comptest  # runs component test
make unittest  # runs unit tests
```

Note that for `alltest`, `e2etest`, `inttest`, you must have docker enabled, and nothing is running.
Please consider using `script/clean.sh` before test. (WARNING: this script resets docker.)

### Mac OS M1

see `./script/setup_browser_driver.sh` for downloading mac m1 chrome
also, set `export CHROME_PATH="....../Chromium.app/Contents/MacOS/Chromium"`

also see `./script/build_m1_image.sh`

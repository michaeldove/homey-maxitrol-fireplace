# Maxitrol Fireplace for Homey

A community-developed Homey app for Maxitrol G6R H4T 433.92 MHz fireplace
controls. It runs locally on Homey using the Python Homey Apps SDK and has been
physically verified with a `G6R-H4T5-Z19` handset, `G6R-R4AU` receiver, and
Homey Self-Hosted Server with a Homey Bridge.

The app learns the unique 18-bit identity of the existing handset during
pairing, then uses that identity for every transmission. It provides:

- Fireplace on and off control
- Flame-up and flame-down device buttons
- Flame-up and flame-down Flow actions with optional duration
- Automatic handset-ID learning from the original remote

## Compatibility

Maxitrol supplies the G6R/GV60 control system to multiple fireplace
manufacturers. Compatibility therefore depends on the handset and receiver
model labels rather than the brand shown on the fireplace.

| Component | Supported or verified configuration |
|---|---|
| Handset | `G6R-H4T5-Z19` |
| Receiver | `G6R-R4AU` |
| Radio | 433.92 MHz |
| Homey | Homey Self-Hosted Server 13.0.0+ with Homey Bridge (verified), or Homey Pro 13.0.0+ with 433 MHz radio hardware |

Other G6R H4T variants may share the protocol but are not yet claimed as
verified. B6R/Symax/myfire systems, Wi-Fi controllers, 315 MHz and 868 MHz
handsets, and unrelated 433 MHz remotes are not supported.

Communication is transmit-only. Homey cannot observe changes made with the
original handset and displays the last command sent through Homey.

## Repository layout

| Path | Contents |
|---|---|
| [`com.maxitrol.fireplace/`](com.maxitrol.fireplace/) | Homey app source, tests, Store assets, and development documentation |
| [`MAXITROL_G6R_H4T_433_PROTOCOL.md`](MAXITROL_G6R_H4T_433_PROTOCOL.md) | Reverse-engineered RF protocol specification and compatibility boundaries |

See the [app development guide](com.maxitrol.fireplace/README.md) for pairing,
RF implementation details, and the complete local development workflow.

## Development

The app requires Node.js 24 or newer, Homey CLI 4.4.1 or newer, Python 3.14,
and Docker for running the Python app through Homey CLI.

```shell
cd com.maxitrol.fireplace
homey app validate --level=publish
python3 -m unittest discover -s tests -v
```

To run the branch-coverage suite:

```shell
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m coverage run --branch -m unittest discover -s tests
.venv/bin/python -m coverage report -m
```

To install a development build on a selected Homey:

```shell
homey login
homey select
homey app run
```

## Safety

This app only emulates transmissions from the original handset. The Maxitrol
receiver, valve, ignition proving, flame supervision, and shutdown controls
must remain installed and operational.

Do not automate ignition while the fireplace is unattended. Confirm
compatibility and correct operation on the actual appliance before relying on
Homey control.

This is an independent community integration and is not an official Maxitrol
product.

## License

This project is available under the [MIT License](LICENSE).

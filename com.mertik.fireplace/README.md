# Mertik Fireplace for Homey

Python Homey App SDK v3 support for the Mertik Maxitrol
`G6R-H4T5-Z19` 433.92 MHz fireplace handset protocol.

The app learns the 18-bit handset address during pairing and provides:

- Fireplace ON and OFF through Homey's standard `onoff` capability.
- Flame-up and flame-down device buttons.
- Flame-up and flame-down Flow actions with optional duration.
- Automatic handset-ID learning from a valid remote transmission.

## Supported hardware

| Component | Model |
|---|---|
| Handset | `G6R-H4T5-Z19` |
| Receiver | `G6R-R4AU` |
| Homey | Homey Pro with software 13.0.0 or newer |

The full reverse-engineered protocol specification is in
[`../MERTIK_G6R_H4T5_PROTOCOL.md`](../MERTIK_G6R_H4T5_PROTOCOL.md).

## Runtime and SDK

This is a native Python Homey app:

- Homey Apps SDK v3
- Python 3.14
- Local/Homey Pro platform
- `homey:wireless:433` permission

Python is now an officially supported Homey app runtime. The higher-level
`homey-rfdriver` package remains Node.js-only, so this app uses the native
Python `ManagerRF.get_signal_433()` and `Signal.tx()` APIs.

## RF signal definition

The Homey signal is defined in:

```text
.homeycompose/signals/433/mertik_g6r_h4t5.json
```

It currently uses:

```text
logical 0: 308 µs carrier-on, 624 µs carrier-off
logical 1: 609 µs carrier-on, 323 µs carrier-off
end of frame: 609 µs carrier-on, then 21,860 µs carrier-off
start-to-start repeat cadence: approximately 43 ms
default repetitions: 10
```

The bit-to-pulse polarity was confirmed on the target Brighton Homey. With the
two words reversed, Brighton repeatedly decoded the exact bitwise inverse of
the captured Flame Down frame. A same-receiver RTL-SDR comparison then
confirmed the timings and terminal pulse above: Homey and the original handset
both decode as `{23}a8ff04` for Flame Down.

## Development setup

Current Python Homey app development requires:

- Node.js 24 or newer for the latest Homey CLI.
- Homey CLI 4.4.1 or newer.
- Python 3.14.
- Docker for running Python apps through the Homey CLI.

Install or update the CLI:

```shell
npm install --global homey
```

Then authenticate, select a Homey, validate, and run:

```shell
homey login
homey select
homey app validate
homey app run
```

The project currently passes:

```shell
homey app validate --level=debug
```

Store-publish validation additionally requires Homey marketing PNGs for the app
and driver. Those assets are intentionally not included yet because this build
still needs RF bench testing.

Run the protocol unit tests independently of Homey:

```shell
python3 -m unittest discover -s tests -v
```

Install the test extra and run the branch-coverage gate:

```shell
python3 -m pip install -r requirements-dev.txt
python3 -m coverage run -m unittest discover -s tests
python3 -m coverage report
```

The coverage gate requires at least 90% coverage across the production Python
modules. The suite also checks that the source RF signal definition and the
generated `app.json` signal remain identical.

## Pairing

The pairing screen listens temporarily on 433 MHz:

1. Place the original handset near Homey.
2. Select **Start learning**.
3. Press and hold **Flame Down** on the handset for two seconds.
4. Homey validates repeated 22-bit frames and requires three matching handset
   IDs before storing the learned 18-bit ID with the new device.

Only frames containing one of the four known G6R command masks are accepted.
Repeated-frame agreement prevents a single noisy RF frame from becoming the
stored handset ID.
The receiver is enabled only during the 30-second learning window and is
disabled immediately after success, timeout, or cancellation.

The learned ID is included in the device's immutable `data` and is used to
build every transmitted ON, OFF, flame-up, and flame-down frame. The original
captured address `0x15C03` remains only in the protocol tests and documentation.

Learning a handset does not place the fireplace receiver into pairing mode or
change its existing pairing.

The manifest contains a placeholder contributor name under `author`. Replace it
with the publisher's name (and optionally email/website) before publication.

## First RF test

Prefer capturing Homey's transmission with an SDR or logic-analyser receiver
before testing against the fireplace:

1. Run the app with `homey app run`.
2. Pair the single `G6R Fireplace` device.
3. Capture one Homey command and verify a 22-bit frame, approximately 21.14 ms
   frame duration, and approximately 43 ms start-to-start repeat cadence.
4. Confirm the Homey `ON` payload decodes as
   `0101011100000000111001`.
5. If every bit decodes inverted, swap the two arrays under `words` in
   `.homeycompose/signals/433/mertik_g6r_h4t5.json`, then rerun the app.

Only after that comparison should ON/OFF and flame adjustment be tested against
the actual receiver.

## Safety

The app only emulates handset button transmissions. The original Maxitrol
receiver, valve, ignition proving, flame supervision, and shutdown controls
must remain installed and operational.

Do not automate ignition while the fireplace is unattended until RF timing and
repeat behaviour have been verified on the actual appliance.

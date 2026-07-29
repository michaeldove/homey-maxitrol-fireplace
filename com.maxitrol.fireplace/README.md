# Maxitrol for Homey

Python Homey App SDK v3 support for the Maxitrol G6R H4T 433.92 MHz
fireplace handset protocol family. The implementation has been physically
verified with a `G6R-H4T5-Z19` handset and `G6R-R4AU` receiver.

The app learns the 18-bit handset address during pairing and provides:

- Fireplace ON and OFF through Homey's standard `onoff` capability.
- Flame-up and flame-down device buttons.
- Flame-up and flame-down Flow actions with optional duration.
- Automatic handset-ID learning from a valid remote transmission.

Maxitrol supplies the G6R/GV60 control system as an OEM component, so a
compatible controller may be installed in a fireplace sold under another
brand. Compatibility is determined by the handset and receiver labels, not
only by the fireplace brand.

## Compatibility

### Physically verified

| Component | Supported or verified configuration |
|---|---|
| Handset | `G6R-H4T5-Z19` |
| Receiver | `G6R-R4AU` |
| Homey | Homey Self-Hosted Server 13.0.0+ with Homey Bridge (verified), or Homey Pro 13.0.0+ with 433 MHz radio hardware |

### Protocol-family candidates

[RFXCOM groups](https://www.rfxcom.com/WebRoot/StoreNL2/Shops/78165469/MediaGallery/Downloads/RFXtrx_User_Guide.pdf)
the `G6R-H4T5`, `G6R-H4TB`, `G6R-H4T`, and `G6R-H4T21-Z22` variants in the
same Maxitrol/Mertik RF family. These are strong compatibility candidates but
have not been capture-tested with this Homey app.

`G6R-H4T1`, `G6R-H4TD`, `G6R-H4T16`, `G6R-H3T1`, and `G6R-H4S` are related
G6R variants. They are not currently claimed as supported because available
integrations distinguish multiple protocol subtypes.

B6R/Symax/myfire bidirectional systems, 315 MHz and 868 MHz handsets, and
unrelated 433 MHz fireplace remotes are outside this driver's scope.

The full reverse-engineered protocol specification is in
[`../MAXITROL_G6R_H4T_433_PROTOCOL.md`](../MAXITROL_G6R_H4T_433_PROTOCOL.md).

## Runtime and SDK

This is a native Python Homey app:

- Homey Apps SDK v3
- Python 3.14
- Local platform (Homey Pro, or Homey Self-Hosted Server with Homey Bridge)
- `homey:wireless:433` permission

## RF signal definition

The Homey signal is defined in:

```text
.homeycompose/signals/433/maxitrol_g6r_h4t_433.json
```

It currently uses:

```text
logical 0: 308 µs carrier-on, 624 µs carrier-off
logical 1: 609 µs carrier-on, 323 µs carrier-off
end of frame: 609 µs carrier-on
inter-frame interval: 21,860 µs carrier-off
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
and driver. Those Store assets are not included yet.

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
build every transmitted ON, OFF, flame-up, and flame-down frame.

Learning a handset does not place the fireplace receiver into pairing mode or
change its existing pairing.

## First RF test

Prefer capturing Homey's transmission with an SDR or logic-analyser receiver
before testing against the fireplace:

1. Run the app with `homey app run`.
2. Pair the single `G6R 433 MHz Fireplace` device.
3. Capture one Homey command and verify a 22-bit frame, approximately 21.14 ms
   frame duration, and approximately 43 ms start-to-start repeat cadence.
4. Confirm the Homey `ON` payload decodes as
   `0101011100000000111001`.
5. If every bit decodes inverted, swap the two arrays under `words` in
   `.homeycompose/signals/433/maxitrol_g6r_h4t_433.json`, then rerun the app.

Only after that comparison should ON/OFF and flame adjustment be tested against
the actual receiver.

## Safety

The app only emulates handset button transmissions. The original Maxitrol
receiver, valve, ignition proving, flame supervision, and shutdown controls
must remain installed and operational.

Do not automate ignition while the fireplace is unattended until RF timing and
repeat behaviour have been verified on the actual appliance.

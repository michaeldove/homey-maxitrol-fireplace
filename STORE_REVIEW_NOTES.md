# Homey App Store review notes

## Integration summary

Maxitrol is an independent community integration for the G6R H4T 433.92 MHz
fireplace handset protocol. It directly transmits the same four commands as the
original handset:

- ON
- OFF
- Flame Up
- Flame Down

The app requests only the `homey:wireless:433` permission. It does not use an
external service, collect user data, or make network requests.

## Verified hardware

The implementation has been physically tested with:

- Maxitrol `G6R-H4T5-Z19` handset
- Maxitrol `G6R-R4AU` receiver
- Homey Self-Hosted Server 13.0.0 or newer with a Homey Bridge
- An RTL-SDR receiver used to compare Homey transmissions with the original
  handset

Homey Pro installations require Homey hardware that provides a 433 MHz radio.

## Pairing and handset identity

During pairing, the user starts learning and holds Flame Down on the original
handset. The app requires three matching valid frames before accepting the
handset's 18-bit address. That learned address is stored with the device and is
used for every subsequent command. No handset address is hard-coded.

The user then completes Homey's standard device name and zone steps. The app
does not add a competing custom name field.

## Reviewer test procedure

1. Add the **G6R 433 MHz Fireplace** device.
2. Start learning when prompted.
3. Hold Flame Down on a compatible original handset until learning succeeds.
4. Complete Homey's standard name and zone steps.
5. Test ON, OFF, Flame Up, and Flame Down from the device controls.
6. Test the Flame Up and Flame Down Flow action cards, including their optional
   duration argument.

## Compatibility boundaries

Maxitrol supplies G6R/GV60 components to multiple fireplace manufacturers, so
compatibility is determined by the handset and receiver model labels rather
than the consumer fireplace brand.

Other G6R H4T variants may share this protocol, but they are not yet claimed as
verified. B6R/Symax/myfire systems, Wi-Fi controllers, 315 MHz and 868 MHz
systems, and unrelated 433 MHz remotes are not supported.

Existing community Maxitrol projects known to the author target Wi-Fi or
868 MHz/B6R systems. This app is an original direct-RF implementation based on
captured G6R H4T 433.92 MHz transmissions.

## State and safety

Communication is transmit-only. Homey cannot observe changes made with the
original handset and therefore displays the last command sent through Homey.

The app emulates the original handset only. The receiver, valve, ignition
proving, flame supervision, and shutdown controls remain responsible for
appliance safety. The Store copy tells users not to automate ignition while
the fireplace is unattended.

## Project links

- Source and documentation:
  https://github.com/michaeldove/homey-maxitrol-fireplace
- Support and issue reports:
  https://github.com/michaeldove/homey-maxitrol-fireplace/issues

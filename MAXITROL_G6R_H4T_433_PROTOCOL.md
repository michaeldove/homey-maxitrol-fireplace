# Maxitrol G6R H4T 433.92 MHz RF Protocol

## Status

This document describes a 433.92 MHz over-the-air profile in the Maxitrol G6R
H4T fireplace handset protocol family. The timings and frame contents were
observed from a `G6R-H4T5-Z19` handset paired with a `G6R-R4AU` receiver.

Older handsets, manuals, and community integrations may use the former
**Mertik Maxitrol** name. [Maxitrol consolidated the brand worldwide in
2020](https://www.maxitrol.com/2020/12/maxitrol-one-name-worldwide/).

The frame contents and command values below are based on 45 clean captured
bursts. Field meanings marked **inferred** are strongly supported by the
captured button combinations and by existing G6R integrations, but have not
been confirmed by a manufacturer protocol specification. Compatibility beyond
the verified handset and receiver is therefore stated in tiers.

## Scope

| Item | Value |
|---|---|
| Verified handset | `G6R-H4T5-Z19` |
| Verified receiver | `G6R-R4AU` |
| Captured profile | G6R H4T5 |
| Protocol family | Maxitrol G6R H4T 433 MHz |
| Region/frequency | 433.92 MHz |
| Direction covered | Handset to receiver |
| Address observed | `0x15C03` |

The `Z19` suffix appears to identify an OEM or application configuration. No
public definition for the suffix has been found, and the captured RF format
matches the established G6R H4T family.

## Compatibility Boundaries

Maxitrol supplies the G6R/GV60 control system as an OEM component. A fireplace
may therefore use this protocol even when the appliance carries another
manufacturer's brand. Compatibility should be determined from the handset and
receiver model labels rather than the fireplace badge.

| Tier | Models or systems | Status |
|---|---|---|
| Verified | `G6R-H4T5-Z19` with `G6R-R4AU` | Captured and tested with Homey and RTL-SDR |
| Strong candidates | `G6R-H4T5-*`, `G6R-H4TB`, `G6R-H4T`, `G6R-H4T21-Z22` | Grouped in the same RF family by existing integrations; not tested here |
| Related variants | `G6R-H4T1`, `G6R-H4TD`, `G6R-H4T16`, `G6R-H3T1`, `G6R-H4S` | May use another G6R protocol subtype; unsupported until captured |
| Excluded | B6R/Symax/myfire bidirectional systems; 315 MHz or 868 MHz handsets | Different generation, directionality, or carrier frequency |

Use of 433.92 MHz OOK/PWM alone does not establish compatibility. A candidate
must also match this profile's 22-bit frame, 18-bit handset address, command
nibble, pulse timings, and repeat cadence.

## RF and Timing

| Parameter | Observed value |
|---|---|
| Carrier frequency | Approximately 433.92 MHz |
| Modulation | OOK/ASK envelope, PWM encoded |
| Carrier-on short duration | Approximately 308 µs |
| Carrier-on long duration | Approximately 609 µs |
| Carrier-off long duration | Approximately 624 µs |
| Carrier-off short duration | Approximately 323 µs |
| Nominal symbol duration | Approximately 0.933 ms |
| Symbols per frame | 22 |
| Frame duration | Approximately 21.14 ms |
| Start-to-start repeat cadence | Approximately 43 ms |
| Approximate inter-frame idle time | 21.86 ms |
| Clean candidate bursts captured | 45 |

Each bit is represented by one short and one long interval:

```text
Symbol A: short, long
Symbol B: long, short
```

Testing with a Brighton Homey Pro confirmed the logical-to-physical mapping:

```text
Logical 0: carrier on for about 308 µs, then off for about 624 µs
Logical 1: carrier on for about 609 µs, then off for about 323 µs
```

When these two words were initially reversed, Homey repeatedly decoded the
exact bitwise inverse of the expected Flame Down frame. Swapping the words
produced the expected logical mapping.

A same-receiver RTL-SDR comparison identified a terminal carrier-on pulse of
approximately 609 µs after the 22 data symbols. The transmitter then remains
off for approximately 21.86 ms before the next frame. The terminal pulse is
not part of the 22-bit payload.

The Homey implementation therefore uses `0 = [308, 624]`,
`1 = [609, 323]`, followed by the end-of-frame pulse `[609]`. The
approximately 21.86 ms carrier-off gap is configured separately with
`interval = 21860`. Together, the payload, terminal pulse, and interval
produce the approximately 43,000 µs start-to-start cadence.

## Frame Format

The transmitted frame contains 22 bits, sent left to right:

```text
Bit index:  0                 17 18       21
            +------------------+-----------+
Frame:      |  Handset ID      | Command   |
            |  18 bits         | 4 bits    |
            +------------------+-----------+
```

In compact form:

```text
AAAAAAAAAAAAAAAAAA CCCC
```

| Field | Width | Description |
|---|---:|---|
| `A` | 18 bits | Fixed handset address/signature |
| `C` | 4 bits | Active-low button state, inferred |

No counter, rolling-code field, or checksum is visible in the captured frames.
The handset address remains fixed and only the final four bits change between
the captured commands.

## Handset Address

The address captured from this handset is:

```text
Binary:  010101110000000011
Hex:     0x15C03
Decimal: 89091
```

The 18-bit width agrees with the G6R H4T5/H4TB profile reported by existing
integrations. Another handset will normally have a different address.

## Command Field

### Captured frames

| Action | Complete 22-bit frame | Command |
|---|---|---|
| Ignition / ON | `0101011100000000111001` | `1001` |
| OFF | `0101011100000000111011` | `1011` |
| Flame up | `0101011100000000111101` | `1101` |
| Flame down | `0101011100000000111110` | `1110` |

### Active-low button interpretation

The command nibble behaves as an active-low button bitmap:

```text
Command bit:   C3   C2    C1    C0
Meaning:       ?    OFF   UP    DOWN
Pressed state:      0
Released state:     1
```

| Command | Inferred button state |
|---|---|
| `1111` | No relevant button pressed |
| `1110` | DOWN pressed |
| `1101` | UP pressed |
| `1011` | OFF pressed |
| `1001` | OFF and UP pressed simultaneously |

The ignition frame provides strong evidence for this interpretation. Normal
G6R ignition is initiated by pressing OFF and the large-flame/UP button
together; its `1001` command clears exactly the OFF and UP bits.

`C3` remained `1` in all supplied captures. It may be reserved or may represent
an auxiliary function not exercised during capture. Its purpose is unknown.

## Repetition and Button Behaviour

A held button produces repeated copies of its frame at an approximately 43 ms
start-to-start cadence.

Recommended emulation:

- For a momentary command, start with 10 identical repetitions. This occupies
  approximately 430 ms and agrees with an older working G6R Homey integration.
- For flame adjustment, continue sending the flame-up or flame-down frame at
  the captured cadence while the virtual button remains held.
- For ignition, repeat the ON frame as a held OFF+UP action until the receiver
  acknowledges that its startup sequence has begun. The application should
  impose a bounded maximum hold time.
- Stop transmission cleanly between commands; do not concatenate frames
  without the captured inter-frame idle period.

The fireplace receiver and valve must remain responsible for ignition proving,
flame supervision, and shutdown safety. A radio implementation must not bypass
those controls.

## Pairing

The receiver is already paired with address `0x15C03`, so replaying frames with
that address should not require pairing.

Manufacturer instructions for this G6R generation pair a handset by placing the
receiver in learn mode and then holding the small-flame/DOWN button within the
learning window. For this handset, the corresponding captured frame is:

```text
0101011100000000111110
```

Pairing with a custom transmitter has not yet been capture-verified. Preserve
the existing learned address unless deliberately replacing the handset
identity.

## Decoder Outline

1. Tune the receiver to approximately 433.92 MHz and demodulate the OOK/ASK
   envelope.
2. Classify carrier-on interval lengths into short (about 308 µs) and long
   (about 609 µs), with corresponding carrier-off intervals of about 624 µs
   and 323 µs.
3. Convert each short/long pair into one logical bit using the polarity observed
   in the original capture.
4. Accept frames containing 22 decoded bits.
5. Split the frame into an 18-bit address and 4-bit command.
6. Require address `0x15C03` when decoding this particular handset.
7. Map the command using the captured command table.
8. Collapse identical frames arriving at approximately 43 ms intervals into
   one held-button event.

## Encoder Outline

1. Select the 18-bit address. Use `0x15C03` for the currently paired handset.
2. Append the four-bit command.
3. Encode each bit with the measured short/long pulse pair and correct carrier
   polarity.
4. Emit one 22-bit frame.
5. Emit the approximately 609 µs terminal carrier pulse.
6. Remain idle for approximately 21.86 ms, producing an approximately 43 ms
   start-to-start cadence.
7. Repeat for the desired button-hold duration.

## Open Questions

- Meaning of command bit `C3`.
- Whether additional thermostat, timer, auxiliary burner, or pairing frames
  exist for the `Z19` configuration.
- Which G6R H4T variants use this exact 22-bit profile without timing or
  command differences.
- Minimum reliable repetition count for each receiver operation.
- Receiver tolerance for pulse duration and repeat-cadence variation.

## References

- [Maxitrol: One Name Worldwide](https://www.maxitrol.com/2020/12/maxitrol-one-name-worldwide/)
- [Maxitrol GV60 installation and operating manual](https://fcc.report/FCC-ID/RTDG6RH/2534187.pdf)
- [RFXCOM RFXtrx user guide and G6R compatibility list](https://www.rfxcom.com/WebRoot/StoreNL2/Shops/78165469/MediaGallery/Downloads/RFXtrx_User_Guide.pdf)
- [Legacy Mertik Maxitrol Homey G6R signal definition](https://github.com/nlrb/com.mertik.maxitrol/blob/master/app.json)
- [Legacy Mertik Maxitrol Homey G6R command implementation](https://github.com/nlrb/com.mertik.maxitrol/blob/master/drivers/fireplace/driver.js)

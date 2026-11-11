# Raspberry Pi I2C Current Loop Receiver Using the IS4420 Module

<p align="center">
  <a href="https://inacks.com/product/4-20ma-receiver-is4420-m1/">
    <img src="https://inacks.com/wp-content/uploads/IS4420-M1-I2C-UART-Current-Loop-Receiver-1.jpg" alt="IS4420-M1 I2C/UART 4-20 mA current loop receiver module" width="250">
  </a>
</p>

This example is powered by the **IS4420-M1**, an I2C/UART 4-20 mA current loop receiver module that lets a Raspberry Pi read a current loop with a single I2C read.

No analog circuitry to design. No level shifter: the Raspberry Pi and the IS4420-M1 both work at 3.3 V. No calibration needed: INACKS calibrates every module at 4 mA and 20 mA.  
The IS4420-M1 contains the complete measurement side of the receiver: the loop current flows into its CIN pad, and your code reads the current in mA, the percentage of the 4-20 mA span and the module temperature from its registers.

Perfect for reading pressure, temperature, flow, level and weight transmitters from a Raspberry Pi, for adding 4-20 mA inputs to your own data loggers and gateways, and for reading up to five current loops on the same I2C-serial interface.

### 🛒 [Buy the IS4420-M1 and learn more](https://inacks.com/product/4-20ma-receiver-is4420-m1/)

---

## What this example does

- Reads the current, the percentage of the 4-20 mA span and the module temperature twice a second.
- Prints them in the terminal.
- Prints `Over-range` when the current is above 21.50 mA, and `No measurement yet` when the module has no valid measurement.
- Prints `No answer from the module` if the IS4420-M1 does not acknowledge the I2C transfer, and `Unexpected MODULE_ID` if another device answers at its address.

To read the module through its UART output instead, see [ISXMPL4420ex1](https://github.com/inacks/ISXMPL4420ex1).

---

## What you need

- An [IS4420-M1 module](https://inacks.com/product/4-20ma-receiver-is4420-m1/)
- A Raspberry Pi with the 40-pin header, such as a Raspberry Pi 4, a Raspberry Pi 5 or a Raspberry Pi Zero 2 W, running Raspberry Pi OS
- A 4-20 mA transmitter (2-wire or 3-wire) and its loop power supply, or a 4-20 mA current source
- Python 3 and smbus2 (`sudo apt install python3-smbus2`)

---

## Wiring

| IS4420-M1 pad | Connect to |
|---|---|
| 3V3 | Raspberry Pi pin 1 (3.3 V) |
| GND | Raspberry Pi pin 9 (GND) and the loop power supply 0 V |
| SDA | Raspberry Pi pin 3 (GPIO2, SDA) |
| SCL | Raspberry Pi pin 5 (GPIO3, SCL) |
| ADR | GND: I2C address 26 |
| SPD | GND: 100 kHz |
| CIN | Current loop input: the loop current flows into CIN and returns through GND |
| TX | Leave it floating, with nothing connected. Never connect it to GND: the module doesn't start while TX is held low. |

- The IS4420-M1 takes its 3.3 V supply from the Raspberry Pi.
- The Raspberry Pi already has 1.8 kΩ pull-ups to 3.3 V on pins 3 and 5. They are the pull-ups the I2C-serial interface needs, so SDA and SCL need no extra resistors.
- With a 2-wire transmitter: loop power supply + to the transmitter +, the transmitter - to CIN, and the loop power supply 0 V to GND.
- With a 3-wire transmitter: the transmitter output to CIN, and the transmitter 0 V and the loop power supply 0 V to GND.
- The current loop input isn't isolated: the loop power supply 0 V, the IS4420-M1 GND and the Raspberry Pi GND are connected together.

---

## Setting up the Raspberry Pi

1. Run `sudo raspi-config` and go to **Interface Options** → **I2C** → **Yes**. Reboot.
2. **Raspberry Pi 4 and earlier only:** the IS4420-M1 holds SCL low for a moment while it prepares the data (clock stretching), and the I2C hardware of these models doesn't handle clock stretching reliably. Use the Linux software I2C on the same pins instead. In `/boot/firmware/config.txt` (`/boot/config.txt` on older Raspberry Pi OS versions), change `dtparam=i2c_arm=on` to `dtparam=i2c_arm=off` and add this line:
   ```
   dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=2,i2c_gpio_scl=3,i2c_gpio_delay_us=2
   ```
   Reboot, and set `I2C_PORT = 3` at the top of the script. The wiring stays the same.
3. Install smbus2:
   ```
   sudo apt install python3-smbus2
   ```

---

## Running the example

1. Wire the circuit.
2. Copy `ISXMPL4420ex2.py` to the Raspberry Pi.
3. Run it:
   ```
   python3 ISXMPL4420ex2.py
   ```
4. Press Ctrl+C to stop it.

You should see a new line twice a second. With 12 mA in the loop:

```
12.00 mA   +50.0 %  +26 degC
12.00 mA   +50.0 %  +26 degC
12.00 mA   +50.0 %  +26 degC
...
```

The percentage is the position of the current in the 4-20 mA span:

| Loop current | Percentage |
|:---:|:---:|
| Below 4 mA | Negative |
| 4 mA | 0.0 % |
| 12 mA | 50.0 % |
| 20 mA | 100.0 % |
| 21.50 mA | 109.4 % |
| Above 21.50 mA | `Over-range` |

---

## How it works

The Raspberry Pi (I2C master) reads the measurement with a single I2C transfer. It writes the 2-byte register address 0x0000 and, after a repeated START, reads 7 registers:

```
START | 26+W | 0x00 | 0x00 | RESTART | 26+R | 7 data bytes | STOP
```

| Address | Register | Content |
|:---:|---|---|
| 0x0000 | MA_INT | Current, whole mA |
| 0x0001 | MA_FRAC | Current, hundredths of mA |
| 0x0002 | PERCENT_INT | Percentage, whole %. Bit 7 is the sign: set below 4 mA. |
| 0x0003 | PERCENT_FRAC | Percentage, tenths of % |
| 0x0004 | MODULE_ID | Module identifier: 149 for the IS4420-M1 |
| 0x0005 | MODULE_REV | Module revision (not used here) |
| 0x0006 | MODULE_TEMP | Module temperature, whole °C. Bit 7 is the sign: set below 0 °C. 254 (0xFE) means no measurement. |

Some examples of the first four registers:

| Bytes read | Meaning |
|:---:|---|
| 12, 34, 52, 1 | 12.34 mA, 52.1 % |
| 2, 0, 140, 5 | 2.00 mA, -12.5 % (bit 7 of 140 is set, and 140 - 128 = 12) |
| 255, 0, 255, 0 (0xFF 00 FF 00) | Over-range: the current is above 21.50 mA |
| 254, 0, 254, 0 (0xFE 00 FE 00) | No measurement |

In the script, the read and the conversion are just this:

```python
write = i2c_msg.write(26, [0x00, 0x00])        # register address 0x0000
read = i2c_msg.read(26, 7)                     # registers 0x0000 to 0x0006
i2c.i2c_rdwr(write, read)                      # one transfer, repeated START
r = list(read)

mA = r[0] + r[1] / 100                         # 12 and 34 -> 12.34 mA
pct = (r[2] & 0x7F) + r[3] / 10                # 52 and 1  -> 52.1 %
if r[2] & 0x80:                                # bit 7 set: below 4 mA
    pct = -pct
```

`i2c_rdwr()` sends the write and the read in one transfer, with a repeated START between them, which is what the IS4420-M1 needs. The usual SMBus calls, such as `read_i2c_block_data()`, send a 1-byte register address, so they don't work with the IS4420-M1.

---

## Notes

- **Register address first:** every read starts by writing the 2-byte register address. Reads without it are not supported.
- **Consistent readings:** each read returns a copy of the registers taken when the read starts, so the current, the percentage and the temperature always come from the same measurement.
- **Update rate:** the IS4420-M1 updates its registers once per measurement, about every 100 ms. The script reads them twice a second.
- **Clock stretching:** the IS4420-M1 holds SCL low for a few milliseconds while it prepares the data. On a Raspberry Pi 5 the hardware I2C handles it. On a Raspberry Pi 4 and earlier, use the software I2C (setup step 2).
- **Several modules:** ADR selects the I2C address, so up to five IS4420-M1 modules can share the same I2C-serial interface. SPD selects the speed. The module reads both pads at power-up, so only change them with the module off. Then update `ADDRESS` in the script.

  | ADR | I2C address |
  |:---:|:---:|
  | GND | 26 |
  | 1/4 of 3V3 | 27 |
  | 1/2 of 3V3 | 28 |
  | 3/4 of 3V3 | 29 |
  | 3V3 | 30 |

  | SPD | Speed |
  |:---:|:---:|
  | GND | 100 kHz |
  | 1/2 of 3V3 | 400 kHz |
  | 3V3 | 1 MHz |

  For the intermediate levels, use a resistor divider between 3V3 and GND: two 10 kΩ resistors for 1/2 of 3V3, or 30 kΩ and 10 kΩ for 1/4 and 3/4 of 3V3 (the 10 kΩ resistor goes to GND for 1/4 and to 3V3 for 3/4). This example keeps SPD at GND, the speed the Raspberry Pi uses by default.
- **Temperature:** it's the temperature inside the module, which can be above the ambient temperature.
- **Protection:** CIN has no protection. Never connect the loop power supply straight to CIN, and never reverse the loop: both destroy the module.

---

## Troubleshooting

If the terminal shows `No answer from the module`, the IS4420-M1 did not acknowledge the I2C transfer. One such line right after power-up is normal: the module answers about 0.5 s after power-up. If it keeps showing, check:

- SDA on pin 3 and SCL on pin 5.
- The 3V3 and GND connections.
- ADR and SPD, both connected to GND in this example. The module reads them at power-up, so power-cycle it after changing them.
- On a Raspberry Pi 4 and earlier, the software I2C (setup step 2) and `I2C_PORT = 3` in the script.

| The terminal shows | What to check |
|---|---|
| An error opening `/dev/i2c-1` | I2C is not enabled (setup step 1). With the software I2C, the script must use `I2C_PORT = 3`. |
| `Unexpected MODULE_ID` | Another device answers at address 26. Check that ADR is connected to GND. |
| About `0.00 mA   -25.0 %` | There's no loop current. Check the CIN connection, the transmitter and its loop power supply, and that the loop power supply 0 V goes to GND. |
| `Over-range` | The loop current is above 21.50 mA. Check the transmitter. |
| `No measurement yet` | Normal for a moment right after power-up, before the first measurement. If it keeps showing, check the 3V3 supply (3.3 V). |

---

## Get the IS4420-M1

- 🛒 **[Buy the IS4420-M1](https://inacks.com/product/4-20ma-receiver-is4420-m1/)**: I2C/UART 4-20 mA Current Loop Receiver Module

ℹ️ For more information: [www.inacks.com](https://www.inacks.com)

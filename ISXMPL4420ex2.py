# ISXMPL4420ex2 - Raspberry Pi I2C Current Loop Receiver Using the IS4420 Module
# https://inacks.com/is4420
# Datasheet: https://inacks.com/wp-content/uploads/IS4420-M1-Datasheet-I2C-4-20mA-Current-Loop-Receiver-ISDOC146.pdf
#
# Reads registers 0x0000 to 0x0006 of the IS4420-M1 twice a second and prints
# the loop current, the percentage of the 4-20 mA span and the temperature
# inside the module.
#
# Wiring (IS4420-M1 pad -> Raspberry Pi header pin):
#     3V3 -> pin 1 (3.3 V)
#     GND -> pin 9 (GND)
#     SDA -> pin 3 (GPIO2, SDA)
#     SCL -> pin 5 (GPIO3, SCL)
#     ADR -> GND: I2C address 26
#     SPD -> GND: 100 kHz
#     TX  -> leave it floating, with nothing connected. Never connect it to
#            GND: the module does not start while TX is held low.
#     No extra pull-ups: the Raspberry Pi has 1.8 kOhm pull-ups to 3.3 V on
#     pins 3 and 5.
#     CIN -> current loop: the loop current flows into CIN and returns through
#            GND. Never connect the loop supply straight to CIN.
#
# Raspberry Pi set-up (once):
#     sudo raspi-config -> Interface Options -> I2C -> Yes. Reboot.
#     Raspberry Pi 4 and earlier: the IS4420-M1 stretches the I2C clock, and
#     the hardware I2C of these models does not handle clock stretching
#     reliably. Use the software I2C on the same pins instead: in
#     /boot/firmware/config.txt change "dtparam=i2c_arm=on" to
#     "dtparam=i2c_arm=off", add this line, reboot and set I2C_PORT = 3 below:
# dtoverlay=i2c-gpio,bus=3,i2c_gpio_sda=2,i2c_gpio_scl=3,i2c_gpio_delay_us=2
#     sudo apt install python3-smbus2
#
# Run: python3 ISXMPL4420ex2.py      (Ctrl+C to stop)

import time
from smbus2 import SMBus, i2c_msg

I2C_PORT = 1     # /dev/i2c-1 (Raspberry Pi 4 and earlier: 3, see set-up)
ADDRESS = 26     # ADR tied to GND


def sign(register):              # Bit 7 is the sign: 1 = negative
    return -1 if register & 0x80 else 1


with SMBus(I2C_PORT) as i2c:
    while True:
        time.sleep(0.5)          # The values change about every 103 ms

        # Every read starts with the 2-byte register address (0x0000), then a
        # repeated START and the read. The 7 bytes all come from the same
        # measurement:
        #   r[0] MA_INT     r[1] MA_FRAC    r[2] PERCENT_INT  r[3] PERCENT_FRAC
        #   r[4] MODULE_ID  r[5] MODULE_REV r[6] MODULE_TEMP
        write = i2c_msg.write(ADDRESS, [0x00, 0x00])
        read = i2c_msg.read(ADDRESS, 7)
        try:
            i2c.i2c_rdwr(write, read)
        except OSError:
            print("No answer from the module")
            continue
        r = list(read)

        if r[4] != 149:                  # MODULE_ID of the IS4420-M1 is 149
            print("Unexpected MODULE_ID:", r[4])
            continue

        if r[0] == 0xFE:                 # No measurement (yet)
            print("No measurement yet")
            continue

        temp = sign(r[6]) * (r[6] & 0x7F)                # Whole degC

        if r[0] == 0xFF:                 # Current above the range
            print(f"Over-range            {temp:+d} degC")
        else:
            mA = r[0] + r[1] / 100                       # MA_INT + hundredths
            pct = sign(r[2]) * ((r[2] & 0x7F) + r[3] / 10)  # < 0 below 4 mA
            print(f"{mA:5.2f} mA  {pct:+6.1f} %  {temp:+d} degC")

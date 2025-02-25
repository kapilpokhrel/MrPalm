from fingerbent import FingerBent, FINGERS
import time
import serial

webcam = FingerBent()
webcam.startThreaded()

fourfingers = [FINGERS.INDEX, FINGERS.MIDDLE, FINGERS.RING, FINGERS.PINKY]
thumb = [FINGERS.THUMB_TOP]

s1 = None
s2 = None
try:
    s1 = serial.Serial('/dev/ttyACM0', baudrate=250000)
except Exception as e:
    pass

try:
    s2 = serial.Serial('/dev/ttyUSB0', baudrate=250000)
except Exception as e:
    pass

while True:

    percentage_value = webcam.val
    if percentage_value:
        fourfinger_cmd = 'w'
        thumb_cmd = 'w'

        for finger in fourfingers:
            p = percentage_value[finger]
            fourfinger_cmd += f'{int(p):03d}'
        for finger in thumb:
            p = percentage_value[finger]
            thumb_cmd += f'{int(p):03d}'

        fourfinger_cmd += '\n'
        thumb_cmd += '\n'
        if s1:
            s1.write(bytes(fourfinger_cmd, 'ascii'))
        if s2:
            s2.write(bytes(thumb_cmd, 'ascii'))

    time.sleep(50/1000)

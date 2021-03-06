import os
import sys
import time
import argparse
import operator
import collections


from neopixel import *
from emotion_API import Emotion_API

# From https://github.com/jgarff/rpi_ws281x/blob/master/python/examples/strandtest.py
# LED strip configuration:
LED_COUNT = 60      # Number of LED pixels.
LED_PIN = 18      # GPIO pin connected to the pixels (18 uses PWM!).
# LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 50     # Set to 0 for darkest and 255 for brightest
# True to invert the signal (when using NPN transistor level shift)
LED_INVERT = False
LED_CHANNEL = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP = ws.WS2812_STRIP   # Strip type and colour ordering


def display_color(strip, color):
    """Display `color`."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()
    time.sleep(10)


def color_wipe(strip, color, wait_ms=50):
    # From https://github.com/jgarff/rpi_ws281x/blob/master/python/examples/strandtest.py
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms / 1000.0)


def get_emotion_scores(emo, filename='image.jpg'):
    # Detect emotions
    results, _ = emo.get_emotions(filename)

    # Take first face detected
    try:
        scores = results[0]['scores']
    except IndexError:
        print("No faces found.")
        return None, None
    except TypeError:
        print("Make sure your API key is correct.")
        sys.exit()

    # Get most likely emotion
    top_emotion = max(scores, key=lambda key: scores[key])
    print("Top emotion: {}".format(top_emotion))
    return scores, top_emotion


def get_colors(scores, top_emotion):
    """Map colors to emotion `scores`"""
    red = green = blue = 0
    # For warm and cold emotions, return solid color
    if top_emotion == 'anger':
        color = (255, 0, 0)  # red
        return color
    elif top_emotion == 'fear':
        color = (255, 255, 0)  # yellow
        return color
    elif top_emotion in ['sadness', 'contempt']:
        color = (0, 0, 255)  # blue
        return color
    for e in scores.keys():
        if e in ['anger', 'fear', 'happiness']:
            red += scores[e]
        if e in ['disgust', 'surprise', 'contempt', 'happiness']:
            green += scores[e]
        if e in ['neutral', 'sadness']:
            blue += scores[e]
    color = [int(c * 255) for c in [red, green, blue]]
    print("Red: {}, Green: {}, Blue: {}".format(*color))
    return color


def main(single=False, delay=10):
    # Initialize emotion API
    emo = Emotion_API()
    if single:
        photo = None
        while photo is None:
            os.system('sudo fswebcam --no-banner image.jpg')
            while not os.path.exists('image.jpg'):
                os.system('sudo fswebcam --no-banner image.jpg')
                time.sleep(3)
            scores, top_emotion = get_emotion_scores(emo)
            if scores == None:  # No emotions detected
                continue
            _color = get_colors(scores, top_emotion)
            color = Color(*_color)
            print("Displaying {}".format(_color))
            display_color(strip, color)
            photo = True
            input("Press Enter to exit...")
    else:  # looping
        while True:
            os.system('sudo fswebcam --no-banner image.jpg')
            while not os.path.exists('image.jpg'):
                os.system('sudo fswebcam --no-banner image.jpg')
                time.sleep(3)
            # Initialize emotion API
            emo = Emotion_API()
            scores, top_emotion = get_emotion_scores(emo)
            if scores == None:
                continue
            _color = get_colors(scores, top_emotion)
            color = Color(*_color)
            display_color(strip, color)
            time.sleep(delay)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--color", type=str,
                        help="display single RGB or hex color (eg, 255x255x255 or #FFFFFF)")
    parser.add_argument("-s", "--single",
                        help="update lights with a single photo", action="store_true")
    parser.add_argument("-d", "--delay", type=int,
                        help="time delay between emotion sensing (in seconds)")
    args = parser.parse_args()

    # Create NeoPixel object with appropriate configuration
    strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ,
                              LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)

    # Initialize the library
    strip.begin()

    if args.color:  # Display single color
        if '#' in args.color:
            # Convert hex to Color
            color = args.color.lstrip('#')
            color = Color(tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)))
        else:
            # Extract RGB int values from string
            _color = args.color.split('x')
            _color = [int(x) for x in _color]
            print("Displaying {}".format(_color))
            color = Color(*tuple(_color))
        while True:
            display_color(strip, color)
    if args.delay:
        main(single=args.single, delay=args.delay)
    else:
        main(single=args.single)

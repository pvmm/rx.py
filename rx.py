#!/usr/bin/env python3
#
# Copyright (C) 2023 by Pedro de Medeiros <pedro.medeiros@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import os
from argparse import ArgumentParser
from PIL import Image

#import cv2
import numpy as np


__version__ = '1.0'
num_colours = 16
contains_palette = False
pixelmap = {}
indexmap = {}


def process_palette(image, max_colours):
    w, h = image.size
    palette = image.getpalette()
    print(f'palette size: {len(palette) // 3}')
    index = 1
    max_pixel = 0
    for y in range(0, h):
        for x in range(0, w):
            pixel = image.getpixel((x, y))
            rgb = palette[pixel * 3:pixel * 3 + 3]
            max_pixel = max(pixel, max_pixel)
            # detect black and reserve space for it
            if rgb == [0, 0, 0] and not pixel in indexmap:
                print("index 0 registered to color %i (%i, %i, %i)" % (pixel, *rgb))
                indexmap[pixel] = 0
                pixelmap[0] = pixel
            elif not pixel in indexmap:
                print("index %i registered to color %i (%i, %i, %i)" % (index, pixel, *rgb))
                indexmap[pixel] = index
                pixelmap[index] = pixel
                index += 1
    if index < max_colours - 1:
        for tmp in range(index, max_colours):
            max_pixel += 1
            rgb = palette[max_pixel * 3:max_pixel * 3 + 3]
            print("index %i registered to color %i" % (tmp, max_pixel))
            #indexmap[-tmp] = index
            pixelmap[tmp] = max_pixel

"""
def create_mono(image, colour):
    mask = cv2.inRange(img, np.array(colour), np.array(colour))
    result = cv2.bitwise_and(image, image, mask=mask)
    return result
"""

def create_mono(image, colour):
    # Create new image with the specified colour only
    new_img = Image.new('P', image.size, colour)

    # Mask the new image using the original image
    mask = image.point(lambda pixel: pixel == colour)
    new_img.paste(image, mask=mask)

    return new_img


def process_image(image):
    w, h = image.size
    colours = []
    overwrite_pixels = []
    edges = {}

    print('image palette: %s' % ('true' if contains_palette else 'false'))
    for y in range(1 if contains_palette else 0, h):
        for x in range(0, w):
            pixel = image.getpixel((x, y))
            if not pixel in colours:
                colours.append(pixel)
            if x > 0:
                prev_pixel = image.getpixel((x - 1, y))
            else:
                prev_pixel = None

            if not prev_pixel is None:
                # convert to indexes
                prev_index = indexmap[prev_pixel]
                try:
                    index = indexmap[pixel]
                except KeyError as e:
                    print('colour at (%i, %i) not found' % (x, y))
                    raise e
                new_index = prev_index ^ index
                #print("new index = %i ^ %i = %i" % (prev_index, index, new_index))
                # back to colour
                new_pixel = pixelmap[new_index]
                overwrite_pixels.append(((x, y), new_pixel))
        # change line after it is finished
        for coordinates, pixel in overwrite_pixels:
            x, y = coordinates
            image.putpixel((x, y), pixel)
        overwrite_pixels = []

    if len(colours) > num_colours:
        raise ValueError('number of colours exceeded')

    # Set path and filename
    path, tmp = os.path.split(image.filename)
    new_path = os.path.join(path, 'p_' + os.path.splitext(tmp)[0] + '.png')
    image.save(new_path, colors=num_colours)
    return new_path


def main():
    global contains_palette

    parser = ArgumentParser(
        description='PNG to RX (Running XOR) encoder',
        epilog='Copyright (C) 2023 Pedro de Medeiros <pedro.medeiros@gmail.com>',
    )

    parser.add_argument(
        '--version', action='version', version='%(prog)s ' + __version__
    )
    parser.add_argument(
        '--num-colours',
        dest='num_colours',
        default=16,
        type=int,
        help='define the number of colours in the image',
    )
    parser.add_argument(
        '-r',
        '--rgb',
        dest='rgb',
        action='store_true',
        help='convert to RGB image (default: indexed)',
    )
    parser.add_argument(
        '-c',
        '--contains-palette',
        dest='contains_palette',
        action='store_true',
        help='image contains embedded palette in the first line (height + 1)',
    )
    parser.add_argument(
        '-d',
        '--detect-line',
        dest='detect_line',
        action='store_true',
        help='detect lines using OpenCV',
    )

    parser.add_argument('image', nargs='+', help='image or images to convert')
    args = parser.parse_args()
    num_colours = args.num_colours
    contains_palette = args.contains_palette

    for image_name in args.image:
        try:
            image = Image.open(image_name)
            #image = cv2.imread(image_name)
        except IOError:
            raise IOError('failed to open the image "%s"' % image_name)
        if image.mode != 'P':
            raise TypeError('not indexed image')
        try:
            process_palette(image, num_colours)
            new_name = process_image(image)
            print('new image in "%s"' % new_name)
        except IOError as e:
            print('image "%s" not saved: %s' % (image_name, str(e)))


if __name__ == '__main__':
    main()

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


__version__ = '1.0'
num_colours = 16


def fix_palette(image, max_colours):
    palette = image.getpalette()
    print(f'palette size: {len(palette) / 3}')
    if len(palette) // 3 < max_colours:
        palette = palette + [0, 0, 0] * (max_colours - len(palette) // 3)
        print(f'new palette size: {len(palette) / 3}')
        image.putpalette(palette)


def recreate_original(image):
    new_img = image.copy()
    w, h = image.size

    for y in range(0, h):
        for x in range(1, w):
            prev_pixel = new_img.getpixel((x - 1, y))
            pixel = new_img.getpixel((x, y))
            new_img.putpixel((x, y), prev_pixel ^ pixel)

    new_img.show()


def process_image(image):
    w, h = image.size
    colours = []
    overwrite_pixels = []

    for y in range(0, h):
        for x in range(0, w):
            pixel = image.getpixel((x, y))
            if not pixel in colours:
                colours.append(pixel)
            if x > 0:
                prev_pixel = image.getpixel((x - 1, y))
            else:
                prev_pixel = None

            if not prev_pixel is None:
                new_pixel = prev_pixel ^ pixel
                overwrite_pixels.append(((x, y), new_pixel))
        # change line after it is finished
        for coordinates, pixel in overwrite_pixels:
            x, y = coordinates
            image.putpixel((x, y), pixel)
        overwrite_pixels = []

    if len(colours) > num_colours:
        raise ValueError('number of colours exceeded')

    return image


def main():
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
        '-d',
        '--detect-line',
        dest='detect_line',
        action='store_true',
        help='detect lines using OpenCV',
    )

    parser.add_argument('image', nargs='+', help='image or images to convert')
    args = parser.parse_args()
    num_colours = args.num_colours

    for image_name in args.image:
        try:
            image = Image.open(image_name)
            fix_palette(image, num_colours)
        except IOError:
            raise IOError('failed to open the image "%s"' % image_name)
        if image.mode != 'P':
            raise TypeError('not indexed image')
        try:
            new_image = process_image(image)
            recreate_original(new_image)
            path, tmp = os.path.split(image.filename)
            new_path = os.path.join(path, 'p_' + os.path.splitext(tmp)[0] + '.png')
            new_image.save(new_path, colors=num_colours)
            print('new image in "%s"' % new_path)
        except IOError as e:
            print('image "%s" not saved: %s' % (image_name, str(e)))


if __name__ == '__main__':
    main()

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


class FakeImage:
    def __init__(self):
        self.filename = 'fake_image.png'
        self.data = [1, 1, 1, 1, 2, 1, 4, 4, 1, 3, 1, 1, 1]
        self.size = len(self.data), 1
        self.old_data = list(self.data)

    def getpixel(self, coordinates):
        x, y = coordinates
        return self.data[x + y * self.size[0]]

    def putpixel(self, coordinates, value):
        x, y = coordinates 
        self.data[x + y * self.size[0]] = value

    def getdata(self):
        return self.data

    def get_name(self):
        return 'fake_image.png'

    def save(self, name):
        print('old data:', self.old_data)
        print('new data:', self.data)


def process_image(image, max_colours):
    (w, h) = image.size
    data = image.getdata()
    colours = []
    overwrite_pixels = []
    edges = {}

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
                overwrite_pixels.append(((x, y), prev_pixel ^ pixel))
        # change line after it is finished
        for coordinates, pixel in overwrite_pixels:
            image.putpixel(coordinates, pixel)
        overwrite_pixels = []

    if len(colours) > max_colours:
        raise ValueError('max colours exceeded')

    path, filename = os.path.split(image.filename)
    image.save(os.path.join(path, 'p_' + filename))


def inc(edges, pixels):
    sorted_args = tuple(sorted(pixels))
    if sorted_args in edges:
        print("updated edge", sorted_args)
        edges[sorted_args] += 1
        #raise "a"
    else:
        print("created edge", sorted_args)
        edges[sorted_args] = 1


def main():
    parser = ArgumentParser(
        description='PNG to RLX (Run-length XOR) encoder',
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
        '-t',
        '--test',
        dest='test',
        action='store_true',
        help='run fake test image',
    )


    parser.add_argument('image', nargs='+', help='image or images to convert')
    args = parser.parse_args()

    if args.test:
        process_image(FakeImage(), args.num_colours)
    else:
        for image_name in args.image:
            try:
                image = Image.open(image_name)
            except IOError:
                raise IOError('failed to open the image "%s"' % image_name)
            if image.mode != 'P':
                raise TypeError('not indexed image')
            try:
                process_image(image, args.num_colours)
            except Exception as e:
                print('image "%s" not saved: %s' % image_name, e.message)


if __name__ == '__main__':
    main()

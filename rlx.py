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
        self.size = 10, 1
        self.data = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]

    def getdata(self):
        return self.data

    def get_name(self):
        return 'fake_image.png'

    def save(self, name):
        print(self.getdata())


def process_image(image, max_colors):
    (w, h) = image.size
    data = image.getdata()
    colors = {}
    erased_pixels = []
    edges = {}

    for y in range(0, h):
        for x in range(0, w):
            pos = x + y * w
            pixel = data[pos]
            if not pixel in colors:
                colors[pixel] = True
            if x > 0:
                prev_pixel = data[pos - 1]
            else:
                prev_pixel = None
            if x < w - 1:
                next_pixel = data[pos + 1]
            else:
                next_pixel = None

            # detect horizontal line
            # aA
            if prev_pixel == pixel:
                # aAa
                if next_pixel == pixel:
                    # erase middle pixels
                    erased_pixels.append(pos)
                edge = (pixel == next_pixel)
            # aB.
            elif prev_pixel and next_pixel:
                # .aBc
                if not edge:
                    if pixel != next_pixel:
                        # [^a]aBc
                        inc(edges, (pixel, next_pixel))
                edge = False
        for pos in erased_pixels:
            data[pos] = 0
        erased_pixels = []

    if len(colors) > max_colors:
        raise ValueError('max colors exceeded')

    image.save('p_' + image.get_name())


def inc(edges, pixels):
    sorted_args = tuple(sorted(pixels))
    if sorted_args in edges:
        edges[sorted_args] += 1
    else:
        edges[sorted_args] = 0


def main():
    parser = ArgumentParser(
        description='PNG to RLX (Run-length XOR) encoder',
        epilog='Copyright (C) 2023 Pedro de Medeiros <pedro.medeiros@gmail.com>',
    )

    parser.add_argument(
        '--version', action='version', version='%(prog)s ' + __version__
    )
    parser.add_argument(
        '--num-colors',
        dest='num_colors',
        default=16,
        type=int,
        help='define the number of colors in the image',
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
        process_image(FakeImage(), args.num_colors)
    else:
        for image_name in args.image:
            try:
                image = Image.open(image_name)
            except IOError:
                raise IOError('failed to open the image "%s"' % image_name)
            if image.mode != 'RGB':
                raise TypeError('not RGB image')
            try:
                process_image(image, args.num_colors)
            except Exception as e:
                print('image "%s" not saved: %s' % image_name, e.message)


if __name__ == '__main__':
    main()

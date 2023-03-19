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

import sys
import math
import os
import struct
from argparse import ArgumentParser
from PIL import Image


__version__ = '1.0'
num_colours = 16


def fix_palette_size(palette, max_colours):
    print(f'real palette size: {len(palette) // 3}')
    if len(palette) // 3 < max_colours:
        palette = palette + [0, 0, 0] * (max_colours - len(palette) // 3)
        print(f'new palette size: {len(palette) // 3} (padded)')
    return palette


def create_pal_image(image, max_colours):
    new_img = image.convert('P', palette=Image.Palette.ADAPTIVE, colors=max_colours)
    p = new_img.getpalette()
    tmp_palette = []

    # fix palette ordering
    for p1, p2, p3 in zip(p[0::3], p[1::3], p[2::3]):
        if not (p1, p2, p3) in tmp_palette:
            tmp_palette.append((p1, p2, p3))
        #if not (p1, p2, p3) in tmp_palette:
        #    tmp_palette.insert(0, (p1, p2, p3))
    new_palette = [item for rgb in tmp_palette for item in rgb]
    new_img.putpalette(new_palette)
    return new_img


def recreate_original(image):
    new_img = image.copy()
    w, h = image.size

    for y in range(0, h):
        for x in range(1, w):
            prev_pixel = new_img.getpixel((x - 1, y))
            pixel = new_img.getpixel((x, y))
            new_img.putpixel((x, y), prev_pixel ^ pixel)

    new_img.show()


def save_image(image, filename, max_colours):
    path, tmp = os.path.split(image.filename)
    new_path = os.path.join(path, filename % os.path.splitext(tmp)[0])
    image.save(new_path, colors=max_colours)
    print('new image in "%s"' % new_path)


def write_screen5(image, filename):
    w, h = image.size
    path, tmp = os.path.split(image.filename)
    new_path = os.path.join(path, filename % os.path.splitext(tmp)[0])
    print(f'writing raw MSX image file to "{new_path}"') 
    with open(new_path, 'wb') as file:
        file.write(struct.pack("<B", w & 0xff))
        file.write(struct.pack("<B", w >> 8))
        file.write(struct.pack("<B", h & 0xff))
        file.write(struct.pack("<B", h >> 8))
        for y in range(0, h):
            for x in range(0, w, 2):
                pixel = image.getpixel((x, y))
                next_pixel = image.getpixel((x + 1, y))
                file.write(struct.pack("<B", (pixel << 4) | next_pixel))


def process_image(image):
    w, h = image.size
    colours = []
    prev_pixel = pixel = 0

    for y in range(0, h):
        prev_pixel = image.getpixel((0, y))

        for x in range(1, w):
            pixel = image.getpixel((x, y))
            image.putpixel((x, y), prev_pixel ^ pixel)
            prev_pixel = pixel

    if len(colours) > num_colours:
        raise ValueError('number of colours exceeded')

    return image


def main():
    global num_colours

    parser = ArgumentParser(
        description='PNG to RX (Running XOR) encoder',
        epilog='Copyright (C) 2023 Pedro de Medeiros <pedro.medeiros@gmail.com>',
    )

    parser.add_argument(
        '--version', action='version', version='%(prog)s ' + __version__
    )
    parser.add_argument(
        '-5',
        '--screen5',
        dest='screen5',
        action='store_true',
        help='activate SCREEN 5 mode',
    )
    parser.add_argument(
        '-r',
        '--remap-black',
        dest='remap_black',
        default=0,
        type=int,
        help='remap black colour in the palette (default: 0)',
    )
    parser.add_argument(
        '-s',
        '--show-result',
        dest='show_result',
        action='store_true',
        help='show result at the end',
    )

    parser.add_argument('image', nargs='+', help='image or images to convert')
    args = parser.parse_args()

    # set number of colours
    if args.screen5:
        num_colours = 16
    if math.log2(num_colours) != int(math.log2(num_colours)):
        raise ValueError('number of colours should be a power of 2')
    print(f'number of colors: {num_colours}')

    for image_name in args.image:
        try:
            image = Image.open(image_name)
        except IOError:
            raise IOError('failed to open the image "%s"' % image_name)
        if image.mode in ['RGB', 'RGBA']:
            image = create_pal_image(image, num_colours)
            image.putpalette(fix_palette_size(image.getpalette(), num_colours))
        elif image.mode == 'P':
            image.putpalette(fix_palette_size(image.getpalette(), num_colours))
        else:
            raise ValueError('unknown image mode')
        try:
            image = process_image(image)
            if args.show_result:
                image.show()
                recreate_original(image)
            if args.screen5:
                write_screen5(image, '%s.sc5')
            else:
                save_image(image, 'p_%s.png', num_colours)
        except IOError as e:
            print('image "%s" not saved: %s' % (image_name, str(e)))


if __name__ == '__main__':
    main()

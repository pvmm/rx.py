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
    """palettes that don't declare the whole 4bit space (16 entries) will cause Gimp to crash"""
    print(f'real palette size: {len(palette) // 3}')
    if len(palette) // 3 < max_colours:
        palette = palette + [0, 0, 0] * (max_colours - len(palette) // 3)
        print(f'new palette size: {len(palette) // 3} (padded)')
    return palette


def create_pal_image(image, max_colours):
    """RGB to PAL conversion"""
    new_img = image.convert('P', palette=Image.Palette.ADAPTIVE, colors=max_colours)
    p = new_img.getpalette()
    tmp_palette = []

    # fix palette ordering
    for r, g, b in zip(p[0::3], p[1::3], p[2::3]):
        if not (r, g, b) in tmp_palette:
            tmp_palette.append((r, g, b))
    if len(tmp_palette) > max_colours:
        raise ValueError('generated palette is too big')
    # flatten list of tuples
    new_palette = [item for rgb in tmp_palette for item in rgb]
    new_img.putpalette(new_palette)
    return new_img


def debug_palette(image, max_colours):
    p = image.getpalette()[0 : max_colours * 3]
    for n, (r, g, b) in enumerate(zip(p[0::3], p[1::3], p[2::3])):
        print(f'colour {n} = ({r}, {g}, {b})')
    print('---------')


def fix_colour_bleed(image, max_colours):
    """replace palette position 0 which causes colour bleed"""
    p = image.getpalette()
    reallocated = None
    # check if zeroth index can be reallocated
    for n, (r, g, b) in enumerate(zip(p[0::3], p[1::3], p[2::3])):
        if not n:
            zeroth = r, g, b
        elif zeroth == (r, g, b):
            reallocated = n
    if reallocated == None:
        print('zeroth colour not found: reallocating')
        if len(p) / 3 == max_colours:
            raise ValueError('need to reallocate zeroth colour, but palette is full')
        # shift palette colours up to keep it updated
        dest_map = [0, 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
        image = image.remap_palette(dest_map)
    else:
        # reuse preallocated colour
        dest_map = [reallocated]
        image.remap_palette(dest_map)

    return image


def recreate_original(image):
    """popup window with results""" 
    new_img = image.copy()
    w, h = image.size

    for y in range(0, h):
        for x in range(1, w):
            prev_pixel = new_img.getpixel((x - 1, y))
            pixel = new_img.getpixel((x, y))
            new_img.putpixel((x, y), prev_pixel ^ pixel)

    new_img.show()


def create_filename(old_name, name_mask):
    path, tmp = os.path.split(old_name)
    return os.path.join(path, name_mask % os.path.splitext(tmp)[0])


def save_image(image, max_colours, old_name, name_mask='%s'):
    image.save(create_filename(old_name, name_mask), colors=max_colours)
    print('new image in "%s"' % new_path)


def write_screen5(image, max_colours, old_name, name_mask='%s'):
    w, h = image.size
    sc5_name = create_filename(old_name, name_mask + '.sc5')
    bas_name = create_filename(old_name, name_mask + '.bas')

    print(f'writing MSX-BASIC image loader to "{bas_name}"') 
    with open(bas_name, 'w') as file:
        p = image.getpalette()[3 : max_colours * 3]
        print('10 SCREEN 5', end='\r\n', file=file)
        print('20 COLOR 15,0,0', end='\r\n', file=file)
        for n, (r, g, b) in enumerate(zip(p[0 : : 3], p[1 : : 3], p[2 : : 3]), start=1):
            print(f'{10 * n + 20} COLOR=({n},{r * 7 // 0xff},{g * 7 // 0xff},{b * 7 // 0xff})', end='\r\n', file=file)
        n = n * 10 + 30
        print(f'{n} COPY "{os.path.split(sc5_name.upper())[1]}" TO (0,0),0', end='\r\n', file=file)
        n += 10
        print(f'{n} IF INKEY$="" GOTO {n}', end='\r\n', file=file)
        n += 10
        print(f'{n} COPY(0,0)-({w - 1},{h}),0 TO (1,0),0,XOR', end='\r\n', file=file)
        n += 10
        print(f'{n} IF INKEY$="" GOTO {n}', end='\r\n', file=file)

    print(f'writing raw MSX image file to "{sc5_name}"') 
    with open(sc5_name, 'wb') as file:
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
    #parser.add_argument(
    #    '-r',
    #    '--reorder-palette',
    #    dest='reorder_palette',
    #    action='store_true',
    #    help='put palette in ascending order',
    #)
    parser.add_argument(
        '-s',
        '--show-result',
        dest='show_result',
        action='store_true',
        help='show result at the end in a popup',
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
        if args.screen5 and (image.size[0] > 256 or image.size[1] > 256):
            raise ValueError('image is too big for SCREEN 5')
        if image.mode in ['RGB', 'RGBA']:
            image = create_pal_image(image, num_colours)
        elif image.mode != 'P':
            raise ValueError('unknown image mode')
        # move zeroth colour to new position
        image = fix_colour_bleed(image, num_colours)
        # fix short palette
        image.putpalette(fix_palette_size(image.getpalette(), num_colours))
        try:
            image = process_image(image)
            if args.show_result:
                image.show()
                recreate_original(image)
            if args.screen5:
                #debug_palette(image, num_colours)
                write_screen5(image, num_colours, image_name)
            else:
                save_image(image, num_colours, image_name, 'p_%s.png')
        except IOError as e:
            print('image "%s" not saved: %s' % (image_name, str(e)))


if __name__ == '__main__':
    main()

# Running XOR encoder (or: the hardware accelerated polygon fill method)

## What RX.py does?
RX.py is a Python script that prepares images for rendering them on the MSX2 blitter using [this](https://www.msx.org/forum/msx-talk/development/hardware-accelerated-polygon-fill-using-lmmm) method described by Laurens Holst (Grauw). It can be quite efficient compressing images rich in flat polygons, replacing the original image by a bunch of line segments (which are both easy to store and draw) and recreate the original image using the MSX2 hardware blitter (which is relatively fast). Imagine writing adventure games with lots of screens using this method.

For now RX.py generates SCREEN 5 compatible images, but a SCREEN 8 version is planned.

## Parameters
```
usage: rx.py [-h] [--version] [-v] [-b] [-5] [-s] image [image ...]

PNG to RX (Running XOR) encoder

positional arguments:
  image              image or images to convert

options:
  -h, --help         show this help message and exit
  --version          show program's version number and exit
  -v, --vertical     use vertical sweep only
  -b, --both         use both horizontal and vertical sweep (default: horizontal)
  -5, --screen5      activate SCREEN 5 mode
  -s, --show-result  show result at the end in a popup

Copyright (C) 2023 Pedro de Medeiros <pedro.medeiros@gmail.com>
```

## Everybody loves screenshots

RX.py converts this:<br/>
![Original image restored by the blitter on MSX2](/docs/canvas2.png "Original image restored by the blitter on MSX2")
<br/>into this:<br/>
![RX.py encoded sample image](/docs/canvas1.png "RX.py encoded sample image")
<br/>and going back to the original is as simple as calling a MSX-BASIC screen COPY operation (sample BASIC code included). Or two COPYs if you use both vertical and horizontal sweep operations.
![RX.py encoded sample image (horizontal and vertical sweep)](/docs/canvas3.png "RX.py encoded sample image (both horizontal and vertical sweep)")

## Reference
[this thread](https://www.msx.org/forum/msx-talk/development/hardware-accelerated-polygon-fill-using-lmmm)

## TODO list:
* [x] Horizontal and vertical sweep;
* [x] Output SC5 raw format directly;
* [ ] Output SC8 raw format directly;
* [x] Output screen as a MSX-BASIC program;
* [ ] Output V9990 formats;
* [ ] Add line detection;
* [ ] Implement Bresenham's modified line algorithm (Python and C);
* [ ] Write screen renderer in Python;
* [ ] Write screen renderer in C for the MSX;


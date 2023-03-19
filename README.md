# Running XOR encoder (or: the hardware accelerated polygon fill method)

## What RX.py does?
RX.py is a Python script that prepares images for rendering them on the MSX2 blitter using [this](https://www.msx.org/forum/msx-talk/development/hardware-accelerated-polygon-fill-using-lmmm) method described by Laurens Holst (Grauw). It can be quite efficient compressing images rich in flat polygons, replacing the original image by a bunch of line segments (which are both easy to store and draw) and recreate the original image using the MSX2 hardware blitter (which is relatively fast). Imagine writing adventure games with lots of screens using this method.

For now RX.py generates SCREEN 5 compatible images, but a SCREEN 8 version is planned.

## Everybody loves screenshots

![RX.py encoded sample image](/docs/canvas1.png "RX.py encoded sample image")
![Original image restored by the blitter](/docs/canvas2.png "Original image restored by the blitter")


## Reference
[this thread](https://www.msx.org/forum/msx-talk/development/hardware-accelerated-polygon-fill-using-lmmm)

## TODO list:
* Output SC5 raw format directly;
* Output SC8 raw format directly;
* Output screen as a MSX-BASIC program;
* Output V9990 formats;
* Add line detection;
* Implement Bresenham's modified line algorithm;
* Write screen renderer in Python;
* Write screen renderer in C for the MSX;

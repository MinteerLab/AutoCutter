# AutoCutter

WARNING:
Recent patches to the Silhouette Studio software have changed the tracing algorithm such that all cuts have increased in width and it is no longer able to cut precise electrodes.
The downloader for an old patch of the sofware for which this method was written, Silhouette studio version V4.4.554, is available below.

Windows (64-bit) - https://dl.silhcdn.com/39654d6728f2ad07
Windows (32-bit) - https://dl.silhcdn.com/f8274e86898d83a6
Mac - https://dl.silhcdn.com/d197c345dd44a22f 

Description:
AutoCutter is a tool for generating image files to serve as inputs into cutting machines (such as the Silhouette Cameo) to prepare precise carbon paper electrodes.
It takes a variety of input values such as electrode number, length, functional area, etc. and converts these values into pixel positions.
It generates a white canvas with a black perimeter as a numpy array, then makes separate copies of this canvas on which each row of electrodes is generated.
these arrays are then converted to images via PIL. The program generates each row and stores it in a cache, 
it then requests a location to save the input parameters as a txt, and creates a folder in the same location, transfering the images from the cache into the new directory.

How to Install:
The AutoCutter EXE was designed on Windows 10 64-bit and should function in win10 and above. Other operating systems have not been tested.
The Py file was written in python 3.8 and should function accordingly as long as appropriate libraries are installed.

How to Use:
The input guide image available in AutoCutter under [Help > Input Guide] and in this repository describes the meaning of each input parameter,
while default values and units are available as tooltips when hoovering over each input. All parameters are in cm except [px per cm] and [trodesPerRow].

Credits:
Written By Rokas Gerulskis in the research group of Shelley D. Minteer at the University of Utah in 2022.

License:
Licensed under GNU General Public License v3.0

# CasNum
CasNum (Compass and straightedge Number) is a library that implements
arbitrary precision arithmetic using 
[compass and straightedge](https://en.wikipedia.org/wiki/Straightedge_and_compass_construction) constructions.
Arbitrary precision arithmetic, now with 100% more Euclid. Featuring a functional
modified Game Boy emulator where every ALU opcode is implemented entirely through
geometric constructions.
![Demo](./screenshots/vid.gif)

# Table of Contents
1. [Introduction To Compass And Straightedge Constructions](#introduction-to-compass-and-straightedge-constructions)
2. [Possible Uses](#possible-uses)
   1. [Integration inside a Gameboy Emulator](#integration-inside-a-gameboy-emulator)
3. [Examples and how to run](#examples-and-how-to-run)
4. [Philosophy](#philosophy)
5. [Performance](#performance)
6. [Dependencies](#dependencies)
7. [F.A.Q](#faq)
8. [License and Third-Party Credits](#license-and-third-Party-credits)


## Introduction To Compass And Straightedge Constructions

This project began with a simple compass-and-straightedge 'engine', which can be found under the directory `cas/`.
In compass-and-straightedge constructions, one start with just two points:
The origin, and a unit. Exactly as God intended. The engine then allows us to do what the ancients did: 
-   Construct the line through two points
-   Construct the circle that contains one point and has a center at another point
-   Construct the point at the intersection of two (non-parallel) lines
-   Construct the one or two points in the intersection of a line and a circle (if they intersect)
-   Construct the one point or two points in the intersection of two circles (if they intersect) (Which, by the way turns out to be a nasty 4th degree equation. Check out the formula in `circle.py`, over 3600 characters, yikes. Good thing we have WolframAlpha).

These five constructions are considered the basic compass and straightedge constructions. Think of these as your ISA.

On top of the compass-and-straightedge engine, we have the `CasNum` class.
In `CasNum`, a number `x` is represented as the point `(x,0)` in the plane.
Now, the fun part: implementing all arithmetic and logical operations.
We can construct the addition of two points by finding the midpoint between them
and doubling it, which are both standard compass-and-straightedge constructions.
Then, we can build the product and quotient of numbers using triangle similarity.
The logical operations (AND, OR, XOR) are a little uglier, since they are not a "clean algebraic operation" in the relevant sense, but, hey, it works right?

What I thought was pretty neat is that implementing all this from scratch leaves a lot of room for optimization. For example, multiplication by 2 can be implemented much more efficiently than the generic algorithm for multiplication using triangle similarity. Then, implementing modulo by first removing the highest power of two times the modulus from the dividend yielded much better results than the naive implementation.

## Possible Uses
* Simple RSA program
* Integrate into the ALU of a Game Boy emulator, thus obtaining a Game Boy that arithmetically and logically runs solely on compass and straightedge constructions
* More? idk

The first two examples were actually implemented and can be found under the `examples/` directory.
So apparently one cannot [square the circle](https://en.wikipedia.org/wiki/Squaring_the_circle)
using a compass and a straightedge, but at least one can run Pokémon Red.
Man, I'm sure the ancient Greeks would have loved to see this.

### Integration inside a Game Boy Emulator
Thanks to the great code written by [PyBoy](https://github.com/Baekalfen/PyBoy),
integrating `CasNum` within it was pretty seamless.
The only file I needed to edit was `opcodes_gen.py`, and the edit was pretty
minimal. Though this is not strictly necessary, I also edited the `__main__.py`
to show the points, lines, and circles drawn during the course of the program.

## Examples and how to run

As always, please save any important work before running anything I ever write.

To clone the repo, and install requirements:
```sh
git clone --recursive git@github.com:0x0mer/CasNum.git
cd CasNum
pip install -r requirements.txt
```

You can run the rsa and basic examples from the repo's root directory like so:
```sh
python3 -m examples.basic
python3 -m examples.rsa
```

In order to run PyBoy, first you need a ROM. In order to avoid copyright
infringement, I included the ROM for [2048](https://github.com/Sanqui/2048-gb), 
free to distribute under the zlib license. But if, for example, the ROM you have
is 'Pokemon.gb', then you can place it in examples/Pyboy, cd into examples/PyBoy
and run:
```sh
PYTHONPATH=../.. python
```
Then, once in python, run:
```python
from pyboy import PyBoy
from casnum import viewer
viewer.start()
pyboy = PyBoy('2048.gb')
while pyboy.tick():
    pass

pyboy.stop()
```
the `viewer.start()` just displays the compass-and-straightedge constructions, it is not
strictly needed, but it is fun.

Notice however that the first run of the Game Boy emulator takes approximately 15
minutes to boot, so playing it may require somewhat increased patience. You see, Euclid wouldn't have optimized the Game Boy boot screen.
He would have spent those 15 minutes in silent appreciation, thinking, "Yeah.
That’s about how long that should take."

After running it once, most calculations should already be cached if you run it
from the same python interpreter instance, so on the second run you should be able
to get a decent 0.5~1 FPS, which is totally almost playable.

## Philosophy

Most modern developers are content with `a + b`. They don't want to work for it.
They don't want to see the midpoint being birthed from the intersection of two circles.
`CasNum` is for the developer who believes that if you didn't have to solve a
4th-degree polynomial just to increment a loop counter,
you didn't really increment it.

## Performance
Python's `lru_cache` is used to cache almost any calculation done in the library,
as everything is so expensive. Memory usage may blow up, run at your own risk.
* Time Complexity: Yes
* Space Complexity: Also yes

## Dependencies
* sympy
* pyglet (optional but highly recommended. Only needed if you want to display the
compass-and-straightedge constructions)
* Euclid Postulate V (optional)

## F.A.Q
1. Q: buT cAN iT rUn dOOm?
	
    A: It can't really "run" anything, its a number. 
2. Q: Is it fast?
	
    A: Define "fast". If you mean "faster than copying Euclid by hand", then yes, dramatically.
4. Q: Why did you make this?
	
    A: I wanted arbitrary precision arithmetic, but I also wanted to **feel something**.

## License and Third-Party Credits

The code in the root of this repository is licensed under the **MIT License**. 

### Third-Party Components

This project incorporates the following third-party materials:

* **PyBoy (Modified)**: Located in `./examples/PyBoy/`. Distributed under the **GNU Lesser General Public License (LGPL) v3.0**. 
    * **Notice of Modification**: This version of PyBoy has been modified from the original source code to use the CasNum library instead of Python's int. 
    * The original, unmodified source code for PyBoy can be found at: [https://github.com/Baekalfen/PyBoy](https://github.com/Baekalfen/PyBoy). 
    * The full LGPL license text is available in `./examples/PyBoy/License.md`.

* **2048.gb**: This Game Boy ROM binary is distributed under the **zlib License**. 
    * **Disclaimer**: This software is provided 'as-is', without any express or implied warranty. In no event will the authors be held liable for any damages arising from the use of this software.

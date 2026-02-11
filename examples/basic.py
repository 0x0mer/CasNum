from casnum import CasNum, one, two, viewer, enable_graphics

def cn(n):
    return CasNum.get_n(n)

if __name__ == "__main__":
    if enable_graphics: 
        viewer.start()
    five = two + two + one
    ten = five * two
    n211 = ten * ten * two + ten + one
    print(n211)
    print(n211.is_prime())
    # Now look at the pretty picture, you can kinda see a butterfly in the middle


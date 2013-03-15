from __future__ import division

def print_matching_images(image):
    from dxtbx.sweep_filenames import find_matching_images
    matching_images = find_matching_images(image)
    for mi in matching_images:
        print mi

if __name__ == '__main__':

    import sys
    print_matching_images(sys.argv[1])

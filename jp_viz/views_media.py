from django.shortcuts import render
from django.http import FileResponse, HttpResponse, HttpResponseNotFound
from datetime import timedelta
import os

from PIL import Image
import pillow_avif


# ---------------------------
# Return Avif image
# ---------------------------
def image(request, width, image_name):
    cached_filename = image_cached_filepath(width, image_name)

    # If the image doesn't exist in cache => generate image
    if not os.path.exists(cached_filename):
        raw_filename = image_raw_filepath(image_name)

        if width == 370:
            # Image carrée de côté 370 pixels
            with Image.open(raw_filename) as img:
                w = img.width
                h = img.height
                s = min(w, h)

                x0 = (w - s) // 2
                y0 = (h - s) // 2

                cropped = img.crop((x0, y0, x0 + s, y0 + s))
                new_img = cropped.resize((width, width), Image.LANCZOS)
                new_img.save(
                    cached_filename, "AVIF", quality=95
                )  # quality : 1-100 (optionnel)

        else:
            with Image.open(raw_filename) as img:
                w = img.width
                h = img.height
                ratio = width / float(w)
                new_h = int(float(h) * float(ratio))
                new_img = img.resize((width, new_h), Image.LANCZOS)
                new_img.save(
                    cached_filename, "AVIF", quality=95
                )  # quality : 1-100 (optionnel)

    # Http response with image
    try:
        img = open(cached_filename, "rb")
        response = FileResponse(img)
        response["Cache-Control"] = "public, max-age={}".format(
            int(timedelta(days=365).total_seconds())
        )
    except IOError:
        response = HttpResponseNotFound("<h1>File not exist</h1>")

    return response


def image_raw_filepath(image_name):
    """
    Return original jpg/webp/png/avif raw filepath
    /static/images/nom-image.jpg => /xxx/raw/image-name.ext
    /static/images/nom-image.webp=> /xxx/raw/image-name.ext
    """
    basename = os.path.basename(image_name)
    index_of_dot = basename.index(".")
    basename_without_extension = basename[:index_of_dot]

    # Find raw image filepath
    raw_filepath_png = f"{os.getenv('IMAGES_DIR')}/raw/{basename_without_extension}.png"
    raw_filepath_avif = (
        f"{os.getenv('IMAGES_DIR')}/raw/{basename_without_extension}.avif"
    )
    raw_filepath_webp = (
        f"{os.getenv('IMAGES_DIR')}/raw/{basename_without_extension}.webp"
    )
    raw_filepath_jpg = f"{os.getenv('IMAGES_DIR')}/raw/{basename_without_extension}.jpg"
    if os.path.exists(raw_filepath_jpg):
        return raw_filepath_jpg
    elif os.path.exists(raw_filepath_webp):
        return raw_filepath_webp
    elif os.path.exists(raw_filepath_avif):
        return raw_filepath_avif
    elif os.path.exists(raw_filepath_png):
        return raw_filepath_png
    else:
        return None


def image_cached_filepath(width, image_name):
    """Return avif cached filename"""
    basename = os.path.basename(image_name)
    index_of_dot = basename.index(".")
    basename_without_extension = basename[:index_of_dot]

    # Find image filepath
    return f"{os.getenv('IMAGES_DIR')}/{width}/{basename_without_extension}.avif"


# ---------------------------
# Return JPG image
# https://tb-dev.beautifuldata.fr/images/newsletter/transbeaute-soiree-travesti.jpg
# ---------------------------
def newsletter(request, image_name):
    width = 600

    basename = os.path.basename(image_name)
    index_of_dot = basename.index(".")
    basename_without_extension = basename[:index_of_dot]
    cached_filename = (
        f"{os.getenv('IMAGES_DIR')}/newsletter/{basename_without_extension}.jpg"
    )

    # If the image doesn't exist in cache => generate image
    if not os.path.exists(cached_filename):
        raw_filename = image_raw_filepath(image_name)

        with Image.open(raw_filename) as img:
            w = img.width
            h = img.height
            ratio = width / float(w)
            new_h = int(float(h) * float(ratio))
            new_img = img.resize((width, new_h), Image.LANCZOS)
            new_img.save(cached_filename, format="JPEG")

    # Http response with image
    try:
        img = open(cached_filename, "rb")
        response = FileResponse(img)
        response["Cache-Control"] = "public, max-age={}".format(
            int(timedelta(days=365).total_seconds())
        )
    except IOError:
        response = HttpResponseNotFound("<h1>File not exist</h1>")

    return response

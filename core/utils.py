import os
import hashlib
# from pixellib.tune_bg import alter_bg
from django.conf import settings
import requests
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage


from django.urls import reverse_lazy
from django.utils.http import urlencode

def build_url(viewname, kwargs=None, query_params=None):
    """
    Helper function to build a URL with optional path parameters and query parameters.

    :param viewname: Name of the view for reverse URL resolution.
    :param kwargs: Dictionary of path parameters.
    :param query_params: Dictionary of query parameters.
    :return: Constructed URL with query parameters.
    """
    url = reverse_lazy(viewname, kwargs=kwargs or {})
    if query_params:
        url = f"{url}?{urlencode(query_params)}"
    return url

# def get_image_hash(image_path):
#     with open(image_path, 'rb') as f:
#         return hashlib.md5(f.read()).hexdigest()

# def remove_bg_pixellib(input_path, subdir='processed_photos'):
#     """
#     Removes background using PixelLib and returns relative media path.
#     Skips processing if file already exists.
#     """
#     image_hash = get_image_hash(input_path)
#     output_dir = os.path.join(settings.MEDIA_ROOT, subdir)
#     os.makedirs(output_dir, exist_ok=True)

#     output_filename = f"{image_hash}.png"
#     output_path = os.path.join(output_dir, output_filename)

#     # Return cached image if it exists
#     if os.path.exists(output_path):
#         return os.path.join(subdir, output_filename)

#     # Load model and remove background
#     model_path = os.path.join(settings.BASE_DIR, "models", "deeplabv3_xception_tf_dim_ordering_tf_kernels.h5")
#     change_bg = alter_bg(model_type="pb")
#     change_bg.load_pascalvoc_model(model_path)
#     change_bg.color_bg(input_path, colors=(255, 255, 255), output_image_name=output_path)

#     return os.path.join(subdir, output_filename)
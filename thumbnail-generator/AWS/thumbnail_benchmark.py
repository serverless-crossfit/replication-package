from pathlib import Path
import base64
from io import BytesIO
from imageio import imread, imwrite
from skimage.util import random_noise

BENCHMARK_CONFIG = """
thumbnail_generator:
  description: Generates a thumbnail every time an image is uploaded to object storage.
  root: ..
  num_different_images: 1
  deployment_id: ""
  provider: aws
  region: us-east-1
"""

TAG = "terraform-azure-cli"

def prepare(spec):
    spec.build(TAG)
    spec.run('dotnet publish', image='mcr.microsoft.com/dotnet/sdk:3.1', check=True)
    tf_cmd = (
        "cd terraform; "
        "terraform init -upgrade; "
        f"terraform apply -var deployment_id={spec['deployment_id']} -var region={spec['region']} -auto-approve"
    )
    spec.run(tf_cmd, image=TAG)
    api_url = (
        "cd terraform; "
        "terraform output -raw invoke_url"
    )
    spec['api_url'] = spec.run(api_url, image=TAG).rstrip()


def invoke(spec):
    # Number of images can be passed through spec later
    test_images_path = Path('../test-images')
    img_array = imread(test_images_path.joinpath('test-1.png'))
    for i in range(spec['num_different_images']):
        # Add random noise to image. ALso remove alpha channel as JPEG doesn't support it
        noisy_img = random_noise(img_array)[:,:,:3]
        with BytesIO() as png_img:
            imwrite(png_img, noisy_img, format='jpg', quality=25)
            png_img.seek(0) # Reset position after writing
            # Prepare base64 encoded test image
            encoded_string = base64.b64encode(png_img.read())
            with open(test_images_path.joinpath(f"test-base64-{i}.jpg"), "wb") as target_image_file:
                target_image_file.write(encoded_string)

    envs = {
        'IMAGE_FILE_PREFIX': '../test-images/test-base64-',
        'NUM_IMAGES': spec['num_different_images'],
        'BASE_URL': spec['api_url']
    }
    spec.run_k6(envs)


def cleanup(spec):
    spec.build(TAG)
    tf_cmd = (
        "cd terraform; "
        "terraform init -upgrade; "
        "terraform destroy -auto-approve"
    )
    spec.run(tf_cmd, image=TAG)

import io
import json

from torchvision import models
import torchvision.transforms as transforms
from PIL import Image


# NOTE: the path to load should be an absolute path in the Docker image.
imagenet_class_index = json.load(open('/user/src/app/api/classify/imagenet_class_index.json'))
model = models.densenet121(pretrained=True)
model.eval()


def transform_image(image__url_repsonse):
    """
    Takes image data in bytes, applies the series of transforms and returns a tensor
    :param image_bytes: input image
    :return: tensor
    """
    my_transforms = transforms.Compose([transforms.Resize(255),
                                        transforms.CenterCrop(224),
                                        transforms.ToTensor(),
                                        transforms.Normalize(
                                            [0.485, 0.456, 0.406],
                                            [0.229, 0.224, 0.225])])

    image = Image.open(io.BytesIO(image__url_repsonse.content))

    return my_transforms(image).unsqueeze(0)


def get_prediction(image__url_repsonse):
    tensor = transform_image(image__url_repsonse=image__url_repsonse)
    outputs = model.forward(tensor)
    _, y_hat = outputs.max(1)
    predicted_idx = str(y_hat.item())
    return imagenet_class_index[predicted_idx]

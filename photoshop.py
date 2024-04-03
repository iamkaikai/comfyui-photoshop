from PIL import Image
import numpy as np
import torch
import time
import tempfile 
from photoshop import PhotoshopConnection


class PhotoshopToComfyUINode:

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "password": ("STRING", {"default": "12341234"}),
                "wait_for_photoshop_changes": ("BOOLEAN", {"default": False})
            }
        }
    
    RETURN_TYPES = ("IMAGE", "INT", "INT")
    RETURN_NAMES = ("IMAGE", "width", "height")
    FUNCTION = "load_to_comfy_ui"
    CATEGORY = "image"
    
    def photoshop_import(self, password):
        self.path = tempfile.gettempdir().replace("\\", "/") + '/temp_image.jpg'
        try:
            with PhotoshopConnection(password=password) as ps_conn:
                ps_conn.execute(f"""
                    var saveFile = new File("{self.path}");
                    var jpegOptions = new JPEGSaveOptions();
                    jpegOptions.quality = 10;
                    activeDocument.saveAs(saveFile, jpegOptions, true, );
                """)
        except Exception as e:
            print(f"Photoshop import error: {str(e)}")
            return False
        return True

    def wait_for_change(self, password):
        # Assuming Photoshop supports event-driven changes
        # Adjust based on Photoshop's actual capabilities
        with PhotoshopConnection(password=password) as conn:
            # conn.subscribe('imageChanged', lambda: self.photoshop_import(password), block=True)
            conn.subscribe('imageChanged', lambda _, __: self.photoshop_import(password), block=True)

    def load_to_comfy_ui(self, password, wait_for_photoshop_changes):
        if not self.photoshop_import(password):
            return None, None, None

        if wait_for_photoshop_changes:
            self.wait_for_change(password)

        try:
            image = Image.open(self.path)
            image.verify()
            image = Image.open(self.path).convert('RGB')
        except OSError as e:
            print(f"Image load failed: {str(e)}")
            return None, None, None

        np_image = np.array(image).astype(np.float32) / 255.0
        tensor_image = torch.from_numpy(np_image)[None, ]

        return tensor_image, image.width, image.height

    @classmethod
    def IS_CHANGED(cls, image_path):
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()


NODE_CLASS_MAPPINGS = {
    "PhotoshopToComfyUI": PhotoshopToComfyUINode
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "PhotoshopToComfyUI": "Photoshop to ComfyUI"
}

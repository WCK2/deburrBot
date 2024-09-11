import torch
from mobile_sam import sam_model_registry, SamPredictor, SamAutomaticMaskGenerator
import numpy as np
import cv2
import os


CHECKPOINT = os.getcwd() + '/assets/models/mobile_sam/mobile_sam.pt'
MODEL = 'vit_t'
DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'




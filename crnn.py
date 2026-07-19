import torch 
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision.transforms as transforms
from PIL import Image
import pandas as pd
import os

def preprocessing_img(image_path, target_height=32, max_width=250):
    img = Image.open(image_path).convert('L')
    w, h = img.size
    new_w = int(w * (target_height / h))
    if new_w > max_width:
        final_w = max_width
    else:
        final_w = new_w
    img = img.resize((final_w, target_height), Image.Resampling.LANCZOS)
    padded_img = Image.new('L', (max_width, target_height), color=255)
    padded_img.paste(img, (0, 0))

    return padded_img

class UmaDataset(Dataset):
    def __init__(self, csv_file, img_dir):
        self.df = pd.read_csv(csv_file)
        self.img_dir = img_dir
        self.transform = transforms.ToTensor()

    def __len__(self):
        return len(self.df)
    
    def __getitem__(self, idx):
        row = self.df.iloc[idx]
        img_name = row['filename']
        full_img_path = os.path.join(self.img_dir, img_name)
        padded_img = preprocessing_img(full_img_path)
        img_tensor = self.transform(padded_img)
        label = row['label']

        return img_tensor, label
    
def build_vocab(csv_file):
    df = pd.read_csv(csv_file)
    all_chars = set()

    for label in df['label']:
        all_chars.update(str(label))
    chars = sorted(list(all_chars))
    return chars

def build_char_maps(chars):
    char_to_idx = {char: idx + 1 for idx, char in enumerate(chars)}
    idx_to_char = {idx + 1: char for idx, char in enumerate(chars)}
    return char_to_idx, idx_to_char

class CrnnUma(nn.Module):
    def __init__(self, num_classes):
        super().__init__()

        self.cnn = nn.Sequential(
            nn.Conv2d(1, 32, kernel_size=3, padding=1),
            nn.BatchNorm2d(32),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(32, 64, kernel_size=3, padding=1),
            nn.BatchNorm2d(64),
            nn.ReLU(),
            nn.MaxPool2d(2, 2),

            nn.Conv2d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm2d(128),
            nn.ReLU(),
            nn.MaxPool2d((2, 1), (2, 1))
        )
    
    def forward(self, x):
        x = self.cnn(x)

        x = x.permute(0, 3, 1, 2)
        
        batch_size, seq_len, channels, height = x.size()
        x = x.view(batch_size, seq_len, channels * height)

        return x

if __name__ == "__main__":
    dataset = UmaDataset(csv_file="uma_data/labels_dl.csv", img_dir="uma_data")
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
    images_batch, labels_batch = next(iter(dataloader))

    model = CrnnUma(num_classes=50)
    output_cnn = model(images_batch)

    print("=== HASIL BATCH ===")
    print("Ukuran Tensor Output CNN:", output_cnn.shape)
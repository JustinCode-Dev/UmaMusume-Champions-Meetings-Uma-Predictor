import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader, random_split
import torchvision.transforms as transforms
from PIL import Image
import pandas as pd
import os

def preprocessing_img(image_path, target_height=48, max_width=460):
    img = Image.open(image_path).convert('L')
    w, h = img.size
    new_w = int(w * (target_height / h))
    if new_w > max_width - 5:
        final_w = max_width - 5
    else:
        final_w = new_w
    img = img.resize((final_w, target_height), Image.Resampling.LANCZOS)
    padded_img = Image.new('L', (max_width, target_height), color=255)
    padded_img.paste(img, (5, 0))

    return padded_img

train_transform = transforms.Compose([
    transforms.ColorJitter(brightness=0.2, contrast=0.2),
    transforms.RandomAffine(degrees=(-3, 3), fill = 255),
    transforms.RandomApply([
        transforms.GaussianBlur(kernel_size=(3, 3), sigma=(0.1, 1.0))
    ], p=0.3),
    transforms.RandomApply([
        transforms.RandomAdjustSharpness(sharpness_factor=2)
    ], p=0.2),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

val_transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.5], std=[0.5])
])

class UmaDataset(Dataset):
    def __init__(self, csv_file, img_dir, transform=None):
        self.df = pd.read_csv(csv_file)
        self.img_dir = img_dir
        self.transform = transform if transform is not None else val_transform

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
    char_to_idx = {"<BLANK>": 0}
    idx_to_char = {0: "<BLANK>"}

    for idx, char in enumerate(chars):
        new_idx = len(char_to_idx)
        char_to_idx[char] = new_idx
        idx_to_char[new_idx] = char

    return char_to_idx, idx_to_char

def export_tokens_file(idx_to_char, path="tokens.txt"):
    with open(path, "w", encoding="utf-8") as f:
        for idx in sorted(idx_to_char.keys()):
            char = idx_to_char[idx]
            f.write((char if char else "<blank>") + "\n")

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

        self.rnn = nn.LSTM(
            input_size = 768,
            hidden_size = 256,
            num_layers = 2,
            bidirectional = True,
            batch_first = True,
            dropout= 0.2
        )

        self.fc = nn.Linear(512, num_classes)
    
    def forward(self, x):
        x = self.cnn(x)

        x = x.permute(0, 3, 1, 2)
        
        batch_size, seq_len, channels, height = x.size()
        x = x.view(batch_size, seq_len, channels * height)

        x, _ = self.rnn(x)

        x = self.fc(x)

        return x

def encode_batch(labels, char_to_idx):
    targets = []
    target_lengths = []

    for label in labels:
        encoded = [char_to_idx[char] for char in str(label)]
        targets.extend(encoded)
        target_lengths.append(len(encoded))

    return torch.tensor(targets, dtype=torch.long), torch.tensor(target_lengths, dtype=torch.long)


def train_model(model, dataloader, char_to_idx, epochs=15, lr=0.001):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = optim.Adam(model.parameters(), lr=lr)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode='min', factor=0.5, patience=2
    )

    model.train()

    best_loss = float('inf')

    for epoch in range(epochs):
        running_loss = 0.0
        for batch_idx, (images, labels) in enumerate(dataloader):
            images = images.to(device)
            
            targets, target_lengths = encode_batch(labels, char_to_idx)
            targets = targets.to(device)
            target_lengths = target_lengths.to(device)

            optimizer.zero_grad()

            outputs = model(images)
            seq_len = outputs.size(1)
            log_probs = outputs.log_softmax(2).permute(1, 0, 2)
            batch_size = images.size(0)
            input_lengths = torch.full(size=(batch_size,), fill_value=seq_len, dtype=torch.long).to(device)
            loss = criterion(log_probs, targets, input_lengths, target_lengths)

            loss.backward()

            torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=2.0)
            optimizer.step()
            running_loss += loss.item()
        
        epoch_loss = running_loss / len(dataloader)
        scheduler.step(epoch_loss)
        current_lr = optimizer.param_groups[0]['lr']
        print(f"Epoch [{epoch+1}/{epochs}] - Loss: {epoch_loss:.4f} - LR: {current_lr:.6f}")

        if epoch_loss < best_loss:
            best_loss = epoch_loss
            torch.save(model.state_dict(), "model/ocr/UmaOCR_v6.pth")
            print(f"Checkpoint locked! Best Loss: {best_loss:.4f}")

def decoder_predictions(outputs, idx_to_char, allowed_chars=None, blank_idx=0):
    if allowed_chars is not None:
        outputs = outputs.clone()
        for idx, char in idx_to_char.items():
            if idx != blank_idx and char not in allowed_chars:
                outputs[:, :, idx] = float('-inf')
                
    preds = torch.argmax(outputs, dim=2)

    decoded_texts = []
    for pred in preds:
        pred_list = pred.tolist()
        char_list = []
        prev_idx = None

        for idx in pred_list:
            if idx != prev_idx and idx != 0:
                char_list.append(idx_to_char.get(idx, ""))
            prev_idx = idx

        decoded_texts.append("".join(char_list))

    return decoded_texts

if __name__ == "__main__":
    chars = build_vocab("uma_data/labels_dl.csv")
    char_to_idx, idx_to_char = build_char_maps(chars)
    num_classes = len(char_to_idx)

    train_dataset_full = UmaDataset(csv_file="uma_data/labels_dl.csv", img_dir="uma_data", transform=train_transform)
    val_dataset_full = UmaDataset(csv_file="uma_data/labels_dl.csv", img_dir="uma_data", transform=val_transform)

    total_len = len(train_dataset_full)
    train_size = int(0.8 * total_len)
    val_size = total_len - train_size

    train_subset, _ = random_split(train_dataset_full, [train_size, val_size], generator=torch.Generator().manual_seed(42))
    _, val_subset = random_split(val_dataset_full, [train_size, val_size], generator=torch.Generator().manual_seed(42))

    train_loader = DataLoader(train_subset, batch_size=32, shuffle=True, num_workers=4, pin_memory=True)
    val_loader = DataLoader(val_subset, batch_size=32, shuffle=False, num_workers=4, pin_memory=True)

    model = CrnnUma(num_classes=num_classes)
    print("Training...")
    train_model(model, train_loader, char_to_idx, epochs=24, lr=0.0012)

    print("Evaluation...")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.load_state_dict(torch.load("model/ocr/UmaOCR_v6.pth"))
    model.to(device)
    model.eval()

    with torch.no_grad():
        images, labels = next(iter(val_loader))
        images = images.to(device)
        outputs = model(images)
        predictions = decoder_predictions(outputs, idx_to_char)

        for idx in range(len(labels)):
            print(f"Target : {labels[idx]}")
            print(f"Prediction Result : {predictions[idx]}")
            print("-" * 30)
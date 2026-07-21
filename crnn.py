import torch
import torch.nn as nn
import torch.optim as optim
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
    char_to_idx = {"-": 0}
    idx_to_char = {0: "-"}
    
    for idx, char in enumerate(chars):
        if char != "-":
            new_idx = len(char_to_idx)
            char_to_idx[char] = new_idx
            idx_to_char[new_idx] = char

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

        self.rnn = nn.LSTM(
            input_size = 512,
            hidden_size = 256,
            num_layers = 2,
            bidirectional = True,
            batch_first = True
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



def train_model(model, dataloader, char_to_idx, epochs=10, lr=0.001):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    criterion = nn.CTCLoss(blank=0, zero_infinity=True)
    optimizer = optim.Adam(model.parameters(), lr=lr)

    model.train()

    for epoch in range(epochs):
        running_loss = 0.0
        for batch_idx, (images, labels) in enumerate(dataloader):
            images = images.to(device)
            
            targets, target_lengths = encode_batch(labels, char_to_idx)
            targets = targets.to(device)
            target_lengths = target_lengths.to(device)

            optimizer.zero_grad()

            outputs = model(images)
            log_probs = outputs.log_softmax(2).permute(1, 0, 2)
            batch_size = images.size(0)
            input_lengths = torch.full(size=(batch_size,), fill_value=62, dtype=torch.long).to(device)
            loss = criterion(log_probs, targets, input_lengths, target_lengths)

            loss.backward()

            optimizer.step()
            running_loss += loss.item()
        
        epoch_loss = running_loss / len(dataloader)
        print(f"Epoch [{epoch+1}/{epochs}] - Loss: {epoch_loss:.4f}")

if __name__ == "__main__":
    chars = build_vocab("uma_data/labels_dl.csv")
    char_to_idx, idx_to_char = build_char_maps(chars)
    num_classes = len(char_to_idx)

    dataset = UmaDataset(csv_file="uma_data/labels_dl.csv", img_dir="uma_data")
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)

    model = CrnnUma(num_classes=num_classes)
    print("Training...")
    train_model(model, dataloader, char_to_idx, epochs=5, lr=0.001)


"""if __name__ == "__main__":
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Running on device: {device}")

    dataset = UmaDataset(csv_file="uma_data/labels_dl.csv", img_dir="uma_data")
    dataloader = DataLoader(dataset, batch_size=4, shuffle=True)
    images_batch, labels_batch = next(iter(dataloader))

    images_batch = images_batch.to(device)
    model = CrnnUma(num_classes=50).to(device)

    output_full = model(images_batch)

    #=========== CTCLoss ===========

    log_probs = output_full.log_softmax(2).permute(1, 0, 2)
    targets = torch.randint(1, 50, (4 * 5,), dtype=torch.long).to(device)
    input_lengths = torch.full(size=(4,), fill_value=62, dtype=torch.long).to(device)
    target_lengths = torch.full(size=(4,), fill_value=5, dtype=torch.long).to(device)

    loss = criterion(log_probs, targets, input_lengths, target_lengths)
    print("=== TEST CTC LOSS ===")
    print("Nilai Eror Mentah (Loss):", loss.item())

    print("=== HASIL BATCH ===")
    print("Ukuran Tensor Output Full CRNN:", output_full.shape)"""
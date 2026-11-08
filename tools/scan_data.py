import torch
from torch.utils.data import DataLoader, Dataset
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from src.crnn import CrnnUma, UmaDataset, build_vocab, build_char_maps, decoder_predictions

def scan_all_data():
    csv_path = "uma_data/labels_dl.csv"
    chars = build_vocab(csv_path)
    char_to_idx, idx_to_char = build_char_maps(chars)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = CrnnUma(num_classes=len(char_to_idx)).to(device)
    model.load_state_dict(torch.load("umaocr/model/UmaOCR_v6.pth", map_location=device))
    model.eval()

    dataset = UmaDataset(csv_file=csv_path, img_dir="uma_data")
    batch_size = 64
    full_loader = DataLoader(dataset, batch_size=batch_size, shuffle=False, num_workers=2, pin_memory=True)

    errors = []

    with torch.no_grad():
        for batch_idx, (images, labels) in enumerate(full_loader):
            images = images.to(device)

            outputs = model(images)
            predictions = decoder_predictions(outputs, idx_to_char)

            for in_batch_idx, (target, pred) in enumerate(zip(labels, predictions)):
                if target != pred:
                    global_idx = batch_idx * batch_size + in_batch_idx
                    filename = dataset.df.iloc[global_idx]['filename']
                    errors.append(f"[Wrong] File: {filename} | Target: {target} | Pred: {pred}\n")

    with open("unused/all_errors.txt", "w", encoding="utf-8") as f:
        f.writelines(errors)

if __name__ == "__main__":
    scan_all_data()
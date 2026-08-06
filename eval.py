import torch
import pandas as pd
from torch.utils.data import DataLoader, Dataset
from PIL import Image
import torchvision.transforms as transforms
import os

from crnn import CrnnUma, UmaDataset, build_vocab, build_char_maps, decoder_predictions

def calculate_cer(reference, hypothesis):
    r = list(reference)
    h = list(hypothesis)

    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j

    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i-1] == h[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = min(d[i-1][j] + 1,
                              d[i][j-1] + 1,
                              d[i-1][j-1] + 1)
    if len(r) == 0:
        return 0.0
    return d[len(r)][len(h)] / len(r)

def evaluate_weights():
    csv_path = "uma_data/labels_dl.csv"
    chars = build_vocab(csv_path)
    char_to_idx, idx_to_char = build_char_maps(chars)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = CrnnUma(num_classes=len(char_to_idx)).to(device)
    model.load_state_dict(torch.load("crnn_uma_model_v8.pth", map_location=device))
    model.eval()

    dataset = UmaDataset(csv_file=csv_path, img_dir="uma_data")

    generator = torch.Generator().manual_seed(42)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    _, test_dataset = torch.utils.data.random_split(dataset, [train_size, val_size], generator=generator)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)

    total_cer = 0.0
    correct_exact_match = 0
    total_samples = len(test_loader)

    print("=== START EVALUATION ===")

    with torch.no_grad():
        for i, (image, label) in enumerate(test_loader):
            image = image.to(device)
            target = label[0]

            output = model(image)
            prediction = decoder_predictions(output, idx_to_char)[0]

            cer = calculate_cer(target, prediction)
            total_cer += cer

            if target == prediction:
                correct_exact_match += 1
            else:
                original_idx = test_dataset.indices[i]
                filename = dataset.df.iloc[original_idx]['filename']
                print(f"[Wrong] File: {filename} | Target: {target} | Pred: {prediction} | CER: {cer:.2f}")

    avg_cer = (total_cer / total_samples) * 100
    accuracy = (correct_exact_match / total_samples) * 100

    print("\n=== EVALUATION RESULT ===")
    print(f"Exact Match Accuracy : {accuracy:.2f}%")
    print(f"Average CER          : {avg_cer:.2f}%")

if __name__ == "__main__":
    evaluate_weights()
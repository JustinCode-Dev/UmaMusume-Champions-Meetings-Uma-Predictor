import torch
from torch.utils.data import DataLoader, Dataset
from crnn import CrnnUma, UmaDataset, build_vocab, build_char_maps, decoder_predictions

def scan_all_data():
    csv_path = "uma_data/labels_dl.csv"
    chars = build_vocab(csv_path)
    char_to_idx, idx_to_char = build_char_maps(chars)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    model = CrnnUma(num_classes=len(char_to_idx)).to(device)
    model.load_state_dict(torch.load("model/crnn_uma_model_v9.pth", map_location=device))
    model.eval()

    dataset = UmaDataset(csv_file=csv_path, img_dir="uma_data")
    full_loader = DataLoader(dataset, batch_size=1, shuffle=False)

    with open("all_errors.txt", "w", encoding="utf-8") as f:
        with torch.no_grad():
            for i, (image, label) in enumerate(full_loader):
                image = image.to(device)
                target = label[0]

                output = model(image)
                prediction = decoder_predictions(output, idx_to_char)[0]

                if target != prediction:
                    filename = dataset.df.iloc[i]['filename']
                    f.write(f"[Wrong] File: {filename} | Target: {target} | Pred: {prediction}\n")

if __name__ == "__main__":
    scan_all_data()
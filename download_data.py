import os
import urllib.request
import urllib.error

# Directory to save downloaded files
output_dir = "data/raw"
os.makedirs(output_dir, exist_ok=True)

sheets = {
    "sheet_01": "1ubUE2GhMiuwesqpjNneVupWaky7bmSY7",
    "sheet_02": "128BcUaeF-KIH8QMaBbG6JpYRFLdcrD_A",
    "sheet_03": "11xjpsbdP8Oi8Vh3EhL9TaCLxD7yLqVC9",
    "sheet_04": "1UTDuo5Qu84GuMOAT7Ttsrdfhj47KLYLD",
    "sheet_05": "1C7yK795D2_RffJGQmku0tOl7aQX5N9R8",
    "sheet_06": "11n0S1Xbro9EOFAYZdhyJWqPBlnxN2d8q",
    "sheet_07": "17G1_VUQkwPQgMBMt72KT0kGLE7rpOg_K",
    "sheet_08": "1OyqYLX1aHLtFaSPfs0gP5_IsVJWoXV4o",
    "sheet_09": "1ecGhiVfH1Qv5PFAExsNTh_Ig5_IbBLOY",
    "sheet_10": "11xfvXksr-n80Y1QEYfHvFRiRCwcmWpGS",
    "sheet_11": "1QHf-2SeVdHxGV-3dkyH1Ann0uVtUbU-m",
    "sheet_12": "1XGhHl8ct_n1uwWAsj4yG-Z5yJyJsX1Us",
}

doc_id = "1a6NFu43mESTuqWJ_VmZsvFmW0knpQ7SO"

def download_sheet(name, sheet_id):
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    filepath = os.path.join(output_dir, f"{name}.xlsx")
    print(f"Downloading {name} from {url} ...")
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"Saved to {filepath}")
    except Exception as e:
        print(f"Failed to download {name}: {e}")

def download_doc(doc_id):
    url = f"https://drive.google.com/uc?export=download&id={doc_id}"
    filepath = os.path.join(output_dir, "document.pdf")
    print(f"Downloading document from {url} ...")
    try:
        urllib.request.urlretrieve(url, filepath)
        print(f"Saved to {filepath}")
    except Exception as e:
        print(f"Failed to download document: {e}")

if __name__ == "__main__":
    for name, sheet_id in sheets.items():
        download_sheet(name, sheet_id)
    download_doc(doc_id)

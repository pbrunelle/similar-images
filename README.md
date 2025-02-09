# similar-images
Crawl for similar images

## Commands

EC2 Ubuntu:

```bash
sudo apt update
sudo apt install python3.12-venv
```

Then:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.in

python -m pytest tests

autopep8 -i -r -aa similar_images
```
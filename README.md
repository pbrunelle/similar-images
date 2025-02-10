# similar-images
Crawl for similar images

## Commands

EC2 Ubuntu:

```bash
# Python
sudo apt update
sudo apt install python3.12-venv

# AWS CLI
sudo apt install unzip
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
\rm -rf aws awscliv2.zip
```

EC2 Amazon Linux:

```bash
sudo yum install git
```

Then:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.in

python -m pytest tests

autopep8 -i -r -aa similar_images
```
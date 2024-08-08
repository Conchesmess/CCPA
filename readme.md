CCPA is an app built by Steve Wright as a way to manage some classroom activities and also as an example of a Flask website
https://deploy.cloud.run/?git_repo=https://github.com/conchesness/CCPA

Create new local ssl key pair
openssl req -newkey rsa:2048 -new -nodes -x509 -days 3650 -keyout key.pem -out cert.pem


gcloud config set account <email address> <br>
gcloud auth login <br>
gcloud projects list <br>
gcloud config set project ccpa-394520 <br>
gcloud config set run/region us-west1 <br>
<!--Deploy current directory with settings set from above commands-->
gcloud run deploy --source .
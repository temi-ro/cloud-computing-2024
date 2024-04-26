export KOPS_STATE_STORE="gs://cca-eth-2024-group-020-tmessmer/"
PROJECT='gcloud config get-value project'
kops create -f part4.yaml

kops update cluster --name part4.k8s.local --yes --admin
kops validate cluster --wait 10m
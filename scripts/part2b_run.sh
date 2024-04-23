#!/bin/bash
set -o xtrace

check_job_completion() {
    local completions=$(kubectl get job | awk '$1 == "'"$1"'" {print $2}')
    echo "$completions"
}


# Create the cluster
# export KOPS_STATE_STORE=gs://cca-eth-2024-group-020-tmessmer/
# PROJECT=`gcloud config get-value project`
# kops create -f part2b.yaml
# kops update cluster part2b.k8s.local --yes --admin
# kops validate cluster --wait 10m

parsec_server_name=$(kubectl get nodes -o wide | awk '/parsec-server/{print $1}')
echo "Parsec server name: $parsec_server_name"

gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$parsec_server_name \
--zone europe-west3-a &

kubectl label nodes $parsec_server_name cca-project-nodetype=parsec


jobs=("dedup" "blackscholes" "canneal" "ferret" "freqmine" "radix" "vips")

# Error when thread=1 because there is another occurence of 1 in the file
for thread in 1 2 4 8; do
    for job in "${jobs[@]}"; do
        echo "Job $job with $thread threads"

        # Modify the number of threads
        sed -i "15 s/\${NUM_THREADS}/$thread/g" "parsec-benchmarks/part2b/parsec-$job.yaml"

        # Start the job
        kubectl create -f parsec-benchmarks/part2b/parsec-$job.yaml

        # Wait for the job to complete
        while true; do
            completions=$(check_job_completion "parsec-$job")
            if [ "$completions" = "1/1" ]; then
                echo "Job $job has completed successfully."
                break
            fi
            echo "Job $job is still running. Waiting 20 seconds before polling again..."
            sleep 20
        done

        kubectl logs $(kubectl get pods --selector=job-name=parsec-$job \
    --output=jsonpath='{.items[*].metadata.name}') | tee ./data/data_part2b/output_parsec_$job\_$thread.txt
        
        kubectl delete pods --all
        kubectl delete jobs --all

        # Reset the number of threads
        sed -i "15 s/$thread/\${NUM_THREADS}/g" "parsec-benchmarks/part2b/parsec-$job.yaml"
        sleep 30
    done
done

set +o xtrace
echo "All done!"
#!/bin/bash
set -o xtrace

check_job_completion() {
    local completions=$(kubectl get job | awk '$1 == "'"$1"'" {print $2}')
    echo "$completions"
}


# Create the cluster
# export KOPS_STATE_STORE=gs://cca-eth-2024-group-020-tmessmer/
# PROJECT=`gcloud config get-value project`
# kops create -f part2a.yaml
# kops update cluster part2a.k8s.local --yes --admin
# kops validate cluster --wait 10m

parsec_server_name=$(kubectl get nodes -o wide | awk '/parsec-server/{print $1}')
echo "Parsec server name: $parsec_server_name"

gcloud compute ssh --ssh-key-file ~/.ssh/cloud-computing ubuntu@$parsec_server_name \
--zone europe-west3-a &

kubectl label nodes $parsec_server_name cca-project-nodetype=parsec


jobs=("dedup" "blackscholes" "canneal" "ferret" "freqmine" "radix" "vips")
# pods
benchmarks=("none" "ibench-cpu" "ibench-l1d" "ibench-l1i" "ibench-l2" "ibench-llc" "ibench-membw")
for job in "${jobs[@]}"; do
    index_i=0
    for benchmark in "${benchmarks[@]}"; do
        # Create the benchmark
        # If i!= 0 introduce interference
        if [ $index_i -ne 0 ]; then
            echo "Benchmark $benchmark"
            kubectl create -f interference/$benchmark.yaml
            sleep 60
        fi

        # Start the job
        kubectl create -f parsec-benchmarks/part2a/parsec-$job.yaml
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
--output=jsonpath='{.items[*].metadata.name}') | tee ./data/data_part2/output_parsec_$job\_$benchmark.txt
        
        kubectl delete pods --all
        kubectl delete jobs --all

        #increment index
        ((index_i++))
        echo "Index $index_i"
    done
done

set +o xtrace
echo "All done!"
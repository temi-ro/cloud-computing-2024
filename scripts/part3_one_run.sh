

# Run initial jobs: 
kubectl create -f part3/parsec-freqmine.yaml
kubectl create -f part3/parsec-radix.yaml  
kubectl create -f part3/parsec-dedup.yaml
kubectl create -f part3/parsec-ferret.yaml
kubectl create -f part3/parsec-canneal.yaml


# At Each tick
while true
do
    # For each dependency check if job completed
    # Record job status
    kubectl get jobs -o wide > temporary_file.raw
    ferret=`kubectl get jobs -o wide | grep parsec-ferret | awk '{print $2}'`
    freqmine=`kubectl get jobs -o wide | grep parsec-freqmine | awk '{print $2}'`
    blackscholes=`kubectl get jobs -o wide | grep parsec-blackscholes | awk '{print $2}'`
    dedup=`kubectl get jobs -o wide | grep parsec-dedup | awk '{print $2}'`
    canneal=`kubectl get jobs -o wide | grep parsec-canneal | awk '{print $2}'`
    vips=`kubectl get jobs -o wide | grep parsec-vips | awk '{print $2}'`
    radix=`kubectl get jobs -o wide | grep parsec-radix | awk '{print $2}'`
    
    incomplete="0/1"
    complete="1/1"

    

    #  dedup complete => vips
    if [ "$dedup" == "$complete" ]; then
        kubectl create -f part3/parsec-vips.yaml
        echo 'create vips '
    fi

    #  radix complete => blackscholes
    if [ "$radix" == "$complete" ]; then
        kubectl create -f part3/parsec-blackscholes.yaml
        echo 'create blackscholes '
    fi

    # Check for end of all jobs to deploy results 
    if [ "$ferret" == "$complete" ] && [ "$freqmine" == "$complete" ] && [ "$canneal"=="$complete" ] && [ "$dedup"=="$complete" ] && [ "$blackscholes"=="$complete" ] && [ "$vips"=="$complete" ] && [ "$radix"=="$complete" ]; then
		kubectl get pods -o json > results13.json
		python3 get_time.py results13.json
		break
    fi

    sleep 1

done


wait
echo "All done!"

# echo "Launching client-agent and client-measure..."
# client_commands &
# measure_commands &

# wait
set +o xtrace

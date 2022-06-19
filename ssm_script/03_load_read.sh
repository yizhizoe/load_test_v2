#!/bin/bash
cd /tmp/ycsb-0.17.0/
start=`date +"%s"`
for (( i=0; i<6; i++ ))
do
    {
        bin/ycsb run dynamodb -P workloads/workloadc -P conf/table_1.properties -threads 64 -p recordcount=100000 -p operationcount=1000000
    } &
done
wait
end=`date +"%s"`
echo "time: " `expr $end - $start`
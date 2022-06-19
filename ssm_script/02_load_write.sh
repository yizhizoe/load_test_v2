#!/bin/bash
cd /tmp/ycsb-0.17.0/
start=`date +"%s"`
for (( i=0; i<6; i++ ))
do
    {
        bin/ycsb load dynamodb -P workloads/workloada -P conf/table_1.properties -threads 64 -p recordcount=5000000 -load
    } &
done
wait
end=`date +"%s"`
echo "time: " `expr $end - $start`
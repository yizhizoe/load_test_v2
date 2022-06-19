sudo yum install -y java-1.8.0-devel
cd /tmp/
aws s3 cp s3://cn-poc-bucket/ycsb-0.17.0.tar.gz /tmp/ --region cn-northwest-1
tar xfvz ycsb-0.17.0.tar.gz
cd ycsb-0.17.0
mkdir conf
aws s3 cp s3://cn-poc-bucket/table_1.properties /tmp/ycsb-0.17.0/conf/ --region cn-northwest-1
aws s3 cp s3://cn-poc-bucket/table_2.properties /tmp/ycsb-0.17.0/conf/ --region cn-northwest-1
touch /tmp/ycsb-0.17.0/conf/AWSCredentials.properties
echo "accessKey = <accessKey>
secretKey = <secretKey>" >> /tmp/ycsb-0.17.0/conf/AWSCredentials.properties

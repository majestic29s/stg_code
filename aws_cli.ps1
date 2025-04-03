#https://www.isoroot.jp/blog/3188/
#CIDR作成
aws ec2 create-vpc --cidr-block 10.10.0.0/16
#VPCサブネット作成
VpcId="vpc-0d72d0c51e4c9bf96"
aws ec2 create-subnet --vpc-id ${VpcId} --cidr-block 10.10.0.0/24 --availability-zone us-west-2a
SubnetId="subnet-0450d5948c5f3b195"

# インターネットゲートウェイの作成
aws ec2 create-internet-gateway
$EC2_INTERNET_GATEWAY_TAG_NAME='cli-igw-20240918'
$STRING_EC2_INTERNET_GATEWAY_TAG="ResourceType=internet-gateway,Tags=[{Key=Name,Value=${EC2_INTERNET_GATEWAY_TAG_NAME}}]"
aws ec2 create-internet-gateway --tag-specifications ${STRING_EC2_INTERNET_GATEWAY_TAG}
$igw_id=$(aws ec2 describe-internet-gateways --filters Name=tag:Name,Values=${EC2_INTERNET_GATEWAY_TAG_NAME} --query "InternetGateways[].InternetGatewayId"  | jq -r values[0])
aws ec2 attach-internet-gateway --internet-gateway-id $igw_id  --vpc-id ${VpcId} #作成したインターネットゲートウェイをアタッチ

#ルートテーブルの作成とルートの紐付け
$EC2_ROUTE_TABLE_TAG_NAME='route-table-20240918'
$STRING_EC2_ROUTE_TABLE_TAG="ResourceType=route-table,Tags=[{Key=Name,Value=${EC2_ROUTE_TABLE_TAG_NAME}}]"
aws ec2 create-route-table --vpc-id ${VpcId} --tag-specifications ${STRING_EC2_ROUTE_TABLE_TAG}
$route_id=$(aws ec2 describe-route-tables --filters Name=tag:Name,Values=${EC2_ROUTE_TABLE_TAG_NAME} --query "RouteTables[].RouteTableId"  | jq -r values[0])
#ルートテーブルとIGWの紐付け
aws ec2 create-route --route-table-id ${route_id} --destination-cidr-block 0.0.0.0/0 --gateway-id $igw_id

aws ec2 associate-route-table --route-table-id ${route_id} --subnet-id ${SubnetId} #ルートをルートテーブルに紐付け

#サブネット内で起動したインスタンスにパブリックIPアドレスが自動的に割り当て
aws ec2 modify-subnet-attribute --subnet-id ${SubnetId} --map-public-ip-on-launch
#NSG作成
aws ec2 create-security-group --group-name "test-scg-20240918" --description "This is test security group" --vpc-id ${VpcId}
$nsg_id=$(aws ec2 describe-security-groups --filters Name=vpc-id,Values=${VpcId} Name=group-name,Values="test-scg-20240918" --query 'SecurityGroups[].GroupId' | jq -r values[0])

#外部から22でアクセス許可
aws ec2 authorize-security-group-ingress --group-id ${nsg_id} --protocol tcp --port 22 --cidr 0.0.0.0/0 #外部から22でアクセス許可

#EC２インスタンスの起動
aws ec2 run-instances --image-id ami-048a3a89c9760319a --count 1 --instance-type t2.micro --key-name TestKeyPair --security-group-ids ${nsg_id} --subnet-id ${SubnetId}

$InstanceId=$(aws ec2 describe-instances --filters Name=vpc-id,Values=${VpcId} --query 'Reservations[].Instances[].InstanceId[]' | jq -r values[0])
#EC２確認
aws ec2 describe-instances --instance-id ${InstanceId}
#EC2停止
aws ec2 stop-instances --instance-ids ${InstanceId}



#①EC2インスタンスの削除
aws ec2 terminate-instances --instance-ids ${InstanceId}
#②セキュリティグループの削除
aws ec2 delete-security-group --group-id ${nsg_id}
#③サブネットの削除
aws ec2 delete-subnet --subnet-id ${SubnetId}
#④ルートテーブルの削除
aws ec2 delete-route-table --route-table-id ${route_id}
#⑤インターネットゲートウェイのデタッチ
aws ec2 detach-internet-gateway --internet-gateway-id ${igw_id} --vpc-id ${VpcId}
#⑥インターネットゲートウェイの削除
aws ec2 delete-internet-gateway --internet-gateway-id ${igw_id}
#⑦VPCの削除
aws ec2 delete-vpc --vpc-id ${VpcId}
#⑧キーペアの削除
aws ec2 delete-key-pair --key-name TestKeyPair.pem
rm TestKeyPair.pem
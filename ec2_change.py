import boto3

ec2_client = boto3.client("ec2")
elbv2_client = boto3.client("elbv2")

# ターゲットグループのARN（事前に取得する）
TARGET_GROUP_ARN = "arn:aws:elasticloadbalancing:REGION:ACCOUNT_ID:targetgroup/TARGET_GROUP_NAME/TARGET_GROUP_ID"

# 停止しているEC2インスタンスを検索
def get_stopped_instance():
    response = ec2_client.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
    )
    instances = [
        instance["InstanceId"]
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]
    return instances[0] if instances else None

# EC2インスタンスの起動
def start_instance(instance_id):
    ec2_client.start_instances(InstanceIds=[instance_id])
    print(f"Instance {instance_id} has been started.")

# EC2インスタンスの停止
def stop_instance(instance_id):
    ec2_client.stop_instances(InstanceIds=[instance_id])
    print(f"Instance {instance_id} has been stopped.")


# EC2インスタンスをターゲットグループに追加
def register_instance_to_target_group(instance_id, target_group_arn):
    response = elbv2_client.register_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{"Id": instance_id}]
    )
    print(f"Instance {instance_id} has been added to target group.")
    return response

# インスタンスをターゲットグループから削除
def deregister_instance_from_target_group(instance_id, target_group_arn):
    response = elbv2_client.deregister_targets(
        TargetGroupArn=target_group_arn,
        Targets=[{"Id": instance_id}]
    )
    print(f"Instance {instance_id} has been removed from target group.")
    return response

def lambda_handler(event, context):
    instance_id = get_stopped_instance()

    if instance_id:
        start_instance(instance_id)
        register_instance_to_target_group(instance_id)
    else:
        print("No stopped instances found.")

    return {"status": "completed"}


import boto3
import csv
from datetime import datetime, timedelta, timezone

# タイムゾーン設定
JST = timezone(timedelta(hours=9))

# Boto3クライアント
logs_client = boto3.client("logs")
lambda_client = boto3.client("lambda")

# CloudWatchログから特定期間内のログを取得
def get_lambda_logs(log_group_name, start_time, end_time):
    log_streams = logs_client.describe_log_streams(
        logGroupName=log_group_name,
        orderBy="LastEventTime",
        descending=True
    )["logStreams"]

    events = []
    for stream in log_streams:
        log_stream_name = stream["logStreamName"]
        response = logs_client.get_log_events(
            logGroupName=log_group_name,
            logStreamName=log_stream_name,
            startTime=int(start_time.timestamp() * 1000),
            endTime=int(end_time.timestamp() * 1000)
        )
        for event in response["events"]:
            events.append(event)
    return events

# Lambda関数の処理結果をCSVに出力
def write_logs_to_csv(logs, output_file):
    with open(output_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["FunctionName", "StartTime", "EndTime", "Result"])
        for log in logs:
            writer.writerow(log)

def main():
    # 日時設定
    now = datetime.now(JST)
    yesterday = now - timedelta(days=1)

    # CSV出力用
    output_file = f"lambda_logs_{now.strftime('%Y%m%d')}.csv"

    # Lambda関数のリストを取得
    functions = lambda_client.list_functions()["Functions"]

    logs = []
    for function in functions:
        function_name = function["FunctionName"]
        log_group_name = f"/aws/lambda/{function_name}"

        try:
            # CloudWatchログを取得
            events = get_lambda_logs(log_group_name, yesterday, now)
            for event in events:
                # サンプルとして、開始時間・終了時間・結果の一部を解析
                log_entry = {
                    "FunctionName": function_name,
                    "StartTime": yesterday.strftime("%Y-%m-%d %H:%M:%S"),
                    "EndTime": now.strftime("%Y-%m-%d %H:%M:%S"),
                    "Result": event["message"][:50]  # メッセージの一部を表示
                }
                logs.append([log_entry["FunctionName"], log_entry["StartTime"], log_entry["EndTime"], log_entry["Result"]])
        except logs_client.exceptions.ResourceNotFoundException:
            print(f"No logs found for {function_name}")

    # 結果をCSVに書き出し
    write_logs_to_csv(logs, output_file)
    print(f"Logs have been written to {output_file}")

if __name__ == "__main__":
    main()



import csv
from fpdf import FPDF

class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 12)
        self.cell(0, 10, "AWS Lambda Daily Report", border=False, ln=True, align="C")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def generate_pdf_from_csv(csv_file, pdf_file):
    pdf = PDFReport()
    pdf.add_page()
    pdf.set_font("Arial", size=10)

    # CSVファイルを読み込んでPDFに書き込む
    with open(csv_file, mode="r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            pdf.cell(0, 10, " | ".join(row), ln=True)

    pdf.output(pdf_file)
    print(f"PDF report has been saved as {pdf_file}")

if __name__ == "__main__":
    # CSVファイルとPDF出力ファイルのパス
    csv_file = "lambda_logs_20250405.csv"  # 前スクリプトで生成したCSVファイル名
    pdf_file = "lambda_report_20250405.pdf"

    generate_pdf_from_csv(csv_file, pdf_file)
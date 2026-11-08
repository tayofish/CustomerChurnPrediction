"""Send email alerts for newly predicted High and Critical-risk accounts."""
import json,os,hashlib,smtplib,ssl
from pathlib import Path
from email.message import EmailMessage
import pandas as pd

ROOT=Path("data_to_predict")
SUMMARY=ROOT/"run_summary.json"
HISTORY=ROOT/"notification_history.json"

# Load SMTP configuration from environment variables.
required=["SMTP_HOST","SMTP_USERNAME","SMTP_PASSWORD","SMTP_RECIPIENTS"]
missing=[key for key in required if not os.getenv(key)]
print("SMTP environment variables loaded:",", ".join(key for key in required if os.getenv(key)))

# Read only datasets processed by the current workflow run.
summary=json.loads(SUMMARY.read_text(encoding="utf-8"))
files=[Path(item["output"]) for item in summary.get("processed",[])]
history=json.loads(HISTORY.read_text(encoding="utf-8")) if HISTORY.exists() else {}
pending=[]

for path in files:
    df=pd.read_csv(path,dtype={"accountid":"string"})
    alerts=df[df["Risk Segment"].isin(["High","Critical"])]
    for _,row in alerts.iterrows():
        account=str(row["accountid"]).strip()
        risk=str(row["Risk Segment"])
        key=hashlib.sha256(f"{account}|{risk}".encode()).hexdigest()
        if key not in history:
            pending.append((key,row))

if not pending:
    print("No new High/Critical-risk accounts to notify.")
else:
    if missing:
        raise ValueError("Missing SMTP secrets: "+", ".join(missing))

    # Prepare email notification.
    lines=["ChurnGuard early warning — new high-risk accounts","",
           "Account ID | Risk | Churn Probability | Recommended Action"]
    for _,row in pending:
        lines.append(
            f"{row['accountid']} | {row['Risk Segment']} | "
            f"{row['Churn Probability']:.1%} | {row['Recommended Action']}"
        )

    msg=EmailMessage()
    msg["Subject"]=f"ChurnGuard: {len(pending)} new high-risk account(s)"
    msg["From"]=os.getenv("SMTP_SENDER") or os.environ["SMTP_USERNAME"]
    msg["To"]=os.environ["SMTP_RECIPIENTS"]
    msg.set_content("\n".join(lines))

    # Send email using Gmail SMTP.
    host=os.environ["SMTP_HOST"]
    port=int(os.getenv("SMTP_PORT","587"))
    user=os.environ["SMTP_USERNAME"]
    password=os.environ["SMTP_PASSWORD"]

    if port==465:
        with smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=30) as smtp:
            smtp.login(user,password)
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(host,port,timeout=30) as smtp:
            smtp.starttls(context=ssl.create_default_context())
            smtp.login(user,password)
            smtp.send_message(msg)

    # Record successful notifications to prevent duplicate alerts.
    for key,row in pending:
        history[key]={"accountid":str(row["accountid"]),"risk":str(row["Risk Segment"])}

    HISTORY.write_text(json.dumps(history,indent=2),encoding="utf-8")
    print(f"Email sent for {len(pending)} new High/Critical-risk account(s).")

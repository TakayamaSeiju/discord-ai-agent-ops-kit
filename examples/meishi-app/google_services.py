import base64
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/gmail.compose",
]

SHEET_HEADERS = [
    "氏名", "ふりがな", "会社名", "部署", "役職",
    "メール", "電話", "携帯", "住所", "ウェブサイト",
]


def _get_credentials() -> Credentials:
    # 環境変数からトークンを読み込む（Railwayなどのクラウド環境用）
    if os.environ.get("GOOGLE_TOKEN_JSON"):
        import json as _json
        token_data = _json.loads(os.environ["GOOGLE_TOKEN_JSON"])
        creds = Credentials(
            token=token_data.get("token"),
            refresh_token=token_data.get("refresh_token"),
            token_uri=token_data.get("token_uri"),
            client_id=token_data.get("client_id"),
            client_secret=token_data.get("client_secret"),
            scopes=token_data.get("scopes"),
        )
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
        return creds

    # ローカル開発用：token.jsonファイルから読み込む
    token_file = os.environ.get("GOOGLE_TOKEN_FILE", "token.json")
    creds_file = os.environ.get("GOOGLE_CREDENTIALS_FILE", "credentials.json")

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    else:
        creds = None

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(creds_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())

    return creds


def append_to_sheet(card_info: dict) -> dict:
    creds = _get_credentials()
    service = build("sheets", "v4", credentials=creds)

    spreadsheet_id = os.environ["SPREADSHEET_ID"]
    sheet_name = os.environ.get("SHEET_NAME", "名刺データ")
    range_name = f"{sheet_name}!A1"

    # シートが空の場合はヘッダーを追加
    result = service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=f"{sheet_name}!A1:A1",
    ).execute()

    if not result.get("values"):
        service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption="USER_ENTERED",
            body={"values": [SHEET_HEADERS]},
        ).execute()

    row = [
        card_info.get("name", ""),
        card_info.get("name_kana", ""),
        card_info.get("company", ""),
        card_info.get("department", ""),
        card_info.get("title", ""),
        card_info.get("email", ""),
        card_info.get("phone", ""),
        card_info.get("mobile", ""),
        card_info.get("address", ""),
        card_info.get("website", ""),
    ]

    return service.spreadsheets().values().append(
        spreadsheetId=spreadsheet_id,
        range=range_name,
        valueInputOption="USER_ENTERED",
        body={"values": [row]},
    ).execute()


def create_gmail_draft(to: str, subject: str, body: str) -> dict:
    creds = _get_credentials()
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return service.users().drafts().create(
        userId="me",
        body={"message": {"raw": raw}},
    ).execute()

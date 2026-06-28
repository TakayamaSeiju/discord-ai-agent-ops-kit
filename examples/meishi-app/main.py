import base64
import json
import os
from pathlib import Path

import anthropic
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from google_services import append_to_sheet, create_gmail_draft

load_dotenv()

app = FastAPI(title="名刺スキャンアプリ")
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def extract_card_info(image_bytes: bytes, mime_type: str) -> dict:
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")
    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": mime_type,
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "この名刺画像から情報を抽出してください。"
                            "以下のJSON形式で返してください。項目が不明な場合は空文字にしてください。\n"
                            '{"name": "氏名", "name_kana": "ふりがな", "company": "会社名", '
                            '"department": "部署", "title": "役職", "email": "メールアドレス", '
                            '"phone": "電話番号", "mobile": "携帯番号", "address": "住所", '
                            '"website": "ウェブサイト"}'
                        ),
                    },
                ],
            }
        ],
    )
    text = message.content[0].text
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


def generate_email_body(card_info: dict, memo: str) -> str:
    name = card_info.get("name", "")
    company = card_info.get("company", "")
    title = card_info.get("title", "")

    message = client.messages.create(
        model="claude-opus-4-8",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": (
                    f"以下の情報をもとに、ビジネスシーンにふさわしい丁寧な御礼メールの文面を作成してください。\n\n"
                    f"【相手の情報】\n"
                    f"氏名: {name}\n"
                    f"会社: {company}\n"
                    f"役職: {title}\n\n"
                    f"【メールに含めたい内容（箇条書き）】\n{memo}\n\n"
                    f"件名と本文を以下のJSON形式で返してください:\n"
                    f'{{"subject": "件名", "body": "本文"}}'
                ),
            }
        ],
    )
    text = message.content[0].text
    start = text.find("{")
    end = text.rfind("}") + 1
    return json.loads(text[start:end])


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process")
async def process_card(
    image: UploadFile = File(...),
    memo: str = Form(""),
):
    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if image.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="対応フォーマット: JPEG, PNG, GIF, WebP")

    image_bytes = await image.read()
    if len(image_bytes) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="ファイルサイズは5MB以下にしてください")

    card_info = extract_card_info(image_bytes, image.content_type)

    sheet_result = None
    gmail_result = None
    errors = []

    try:
        sheet_result = append_to_sheet(card_info)
    except Exception as e:
        errors.append(f"スプレッドシート書き込みエラー: {e}")

    if card_info.get("email") and memo.strip():
        try:
            email_content = generate_email_body(card_info, memo)
            gmail_result = create_gmail_draft(
                to=card_info["email"],
                subject=email_content["subject"],
                body=email_content["body"],
            )
        except Exception as e:
            errors.append(f"Gmail下書き作成エラー: {e}")

    return JSONResponse({
        "card_info": card_info,
        "sheet_updated": sheet_result is not None,
        "draft_created": gmail_result is not None,
        "errors": errors,
    })

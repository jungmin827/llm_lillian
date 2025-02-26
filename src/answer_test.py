from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from openai import Client
import os
import pdfplumber
from config import OPENAI_API_KEY

MODEL = "gpt-4o"

# FastAPI 앱 생성
app = FastAPI()

class ResumeRequest(BaseModel):
    content: str  # 텍스트 변환된 이력서 내용

# GPT 호출 함수
def post_gpt(system_content, user_content):
    try:
        client = Client(api_key=OPENAI_API_KEY)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_content}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"GPT 호출 오류: {e}")
        return None

# PDF에서 텍스트 추출 함수
def extract_text_from_pdf(file_path) -> str:
    try:
        with pdfplumber.open(file_path) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        print(f"PDF 텍스트 추출 중 오류 발생: {e}")
        return ""

# 기술 면접 질문 생성 함수
def generate_technical_questions(resume_text):
    system_content = "You are an AI interview assistant specializing in technical questions."
    user_prompt = (
        "다음은 한 지원자의 이력서 내용입니다. 이를 분석하여 해당 지원자의 이력서와 관련된 면접 기술 질문을 1개 생성해주세요.\n"
        "면접 질문은 전문적이며 실무 능력을 평가할 수 있는 형태로 만들어주세요.\n"
        "답변은 질문만 출력해주세요.\n\n"
        f"{resume_text}"
    )
    
    response = post_gpt(system_content, user_prompt)
    if response:
        return response.strip()  # 질문 1개만 반환
    return None

@app.post("/api/sessions/{sessionId}/questions/generate")
def create_technical_questions(sessionId: str, file: UploadFile = File(...)):
    try:
        resume_text = extract_text_from_pdf(file.file)
        if not resume_text:
            raise HTTPException(status_code=400, detail="이력서에서 텍스트를 추출할 수 없습니다.")
        questions = generate_technical_questions(resume_text)
        if not questions:
            raise HTTPException(status_code=500, detail="면접 질문 생성 실패")
        return JSONResponse(content={"status": 200, "sessionId": sessionId, "questions": [questions]})
    except HTTPException as e:
        return JSONResponse(content={"status": e.status_code, "message": "오류 발생: 면접 질문을 생성할 수 없습니다."})

# 🔥 테스트용 실행 코드 (터미널에서 실행 가능) 🔥
if __name__ == "__main__":
    pdf_path = "/Users/jungmin/Downloads/김선화 개발자 이력서.pdf"
    print("📄 PDF에서 텍스트 추출 중...")
    extracted_text = extract_text_from_pdf(pdf_path)
    if extracted_text:
        print("✅ 추출된 텍스트:")
        print(extracted_text[:500])  # 긴 텍스트의 경우 일부만 출력
        print("\n🤖 GPT-4o를 사용하여 질문 생성 중...")
        question = generate_technical_questions(extracted_text)
        if question:
            print("🎯 생성된 면접 질문:")
            print(question)
        else:
            print("⚠️ 질문 생성 실패!")
    else:
        print("⚠️ PDF에서 텍스트를 추출하지 못했습니다.")


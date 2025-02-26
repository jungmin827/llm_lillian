from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.responses import JSONResponse
import openai
import os
import pdfplumber
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
OPENAI_KEY = os.getenv("OPENAI_KEY")
MODEL = "gpt-4o"

# FastAPI 앱 생성
app = FastAPI()

class ResumeRequest(BaseModel):
    content: str  # 텍스트 변환된 이력서 내용

# GPT 호출 함수
def post_gpt(system_content, user_content):
    try:
        openai.api_key = OPENAI_KEY
        response = openai.ChatCompletion.create(
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
def extract_text_from_pdf(file) -> str:
    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        print(f"PDF 텍스트 추출 중 오류 발생: {e}")
        return ""

# 기술 면접 질문 생성 함수
def generate_technical_questions(resume_text):
    system_content = "You are an AI interview assistant specializing in technical questions."
    user_prompt = (
        "다음은 한 지원자의 이력서 내용입니다. 이를 분석하여 해당 지원자의 경력과 관련된 면접 기술 질문을 2개 생성해주세요.\n"
        "면접 질문은 전문적이며 실무 능력을 평가할 수 있는 형태로 만들어주세요.\n"
        "답변은 번호를 붙여서 질문만 출력해주세요.\n\n"
        f"{resume_text}"
    )
    
    response = post_gpt(system_content, user_prompt)
    if response:
        questions = response.split("\n")
        questions = [q.strip() for q in questions if q.strip()]
        return questions[:2]  # 상위 2개 질문 반환
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
        return JSONResponse(content={"status": 200, "sessionId": sessionId, "questions": questions})
    except HTTPException as e:
        return JSONResponse(content={"status": e.status_code, "message": "오류 발생: 면접 질문을 생성할 수 없습니다."})

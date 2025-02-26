from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel
from fastapi.responses import JSONResponse
from openai import Client
import pdfplumber
from config import OPENAI_API_KEY

MODEL = "gpt-4o"

# FastAPI 앱 생성
app = FastAPI()

class ResumeQuestionResponse(BaseModel):
    sessionId: int
    question: str

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
def extract_pdf(file) -> str:
    try:
        with pdfplumber.open(file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return text.strip()
    except Exception as e:
        print(f"PDF 텍스트 추출 중 오류 발생: {e}")
        return ""

# 기술 면접 질문 생성 함수
def generate_answer(resume_text):
    system_content = "You are an AI interview assistant specializing in technical questions."
    user_prompt = (
        "다음은 한 지원자의 이력서 내용입니다. 이를 분석하여 해당 지원자의 이력서와 관련된 면접 기술 질문을 1개 생성해주세요.\n"
        "면접 질문은 전문적이며 실무 능력을 평가할 수 있는 형태로 만들어주세요.\n"
        "답변은 질문만 출력해주세요.\n\n"
        f"{resume_text}"
    )
    
    response = post_gpt(system_content, user_prompt)
    return response.strip() if response else None

@app.post("/api/sessions/{sessionId}/questions/generate", response_model=ResumeQuestionResponse)
async def generate_interview_question(sessionId: str, file: UploadFile = File(...)):
    try:
        # PDF 파일을 읽고 텍스트 추출
        resume_text = extract_pdf(file.file)
        if not resume_text:
            raise HTTPException(status_code=400, detail="이력서에서 텍스트를 추출할 수 없습니다.")
        
        # GPT를 사용하여 면접 질문 생성
        question_text = generate_answer(resume_text)
        if not question_text:
            raise HTTPException(status_code=500, detail="면접 질문 생성 실패")

        # JSON 형태로 반환
        return JSONResponse(content={
            "sessionId": sessionId,
            "question": question_text
        })
    except HTTPException as e:
        return JSONResponse(content={
            "status": e.status_code,
            "message": e.detail
        })

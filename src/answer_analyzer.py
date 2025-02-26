import openai
import json
import re
from hanspell import spell_checker
from kiwipiepy import Kiwi
import kss

# OpenAI API Key (사용자의 키로 변경 필요)
OPENAI_API_KEY = "your-openai-api-key"
openai.api_key = OPENAI_API_KEY

# Kiwi 초기화
kiwi = Kiwi()


def clean_text(text):
    """불필요한 공백 및 줄바꿈을 제거"""
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def grammar_check(text):
    """한스펠을 이용한 맞춤법 및 문법 검사"""
    checked = spell_checker.check(text)
    return checked.checked  # 교정된 문장 반환


def analyze_readability(text):
    """문장 길이 및 가독성 분석"""
    sentences = kss.split_sentences(text)
    words = sum(len(kiwi.tokenize(sent)) for sent in sentences)
    avg_words_per_sentence = words / len(sentences) if sentences else 0
    return {
        "문장 수": len(sentences),
        "평균 단어 수": avg_words_per_sentence
    }


def analyze_relevance(answer, question, job_role):
    """GPT를 활용한 답변 적절성 평가"""
    prompt = f"""
    지원 직무: {job_role}
    면접 질문: {question}
    지원자의 답변: {answer}

    위의 답변이 질문과 관련성이 있는지 평가해주세요.
    또한 부족한 내용이 있다면 어떤 부분을 보완하면 좋은지 피드백을 제공하세요.
    답변의 완성도를 1~10점으로 점수화하고, JSON 형식으로 제공해주세요.
    JSON 키: "점수", "피드백"
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "당신은 전문 면접관입니다."},
                  {"role": "user", "content": prompt}]
    )

    try:
        feedback = json.loads(response["choices"][0]["message"]["content"])
    except json.JSONDecodeError:
        feedback = {"점수": 5, "피드백": "답변을 평가하는 데 문제가 발생했습니다."}

    return feedback


def generate_follow_up(answer, question, job_role):
    """추가적인 상세 답변을 유도하는 후속 질문 생성"""
    prompt = f"""
    지원 직무: {job_role}
    면접 질문: {question}
    지원자의 답변: {answer}

    위의 답변을 기반으로 부족한 내용을 보완할 수 있도록 후속 질문을 생성해주세요.
    JSON 형식으로 제공해주세요.
    JSON 키: "후속 질문"
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "당신은 면접 질문을 잘 만드는 전문가입니다."},
                  {"role": "user", "content": prompt}]
    )

    try:
        follow_up = json.loads(response["choices"][0]["message"]["content"])
    except json.JSONDecodeError:
        follow_up = {"후속 질문": "조금 더 자세히 설명해 주실 수 있나요?"}

    return follow_up


def analyze_answer(question, answer, job_role):
    """면접 답변을 종합적으로 분석하여 반환"""
    cleaned_answer = clean_text(answer)
    grammar_fixed = grammar_check(cleaned_answer)
    readability = analyze_readability(grammar_fixed)
    relevance_feedback = analyze_relevance(grammar_fixed, question, job_role)
    follow_up_question = generate_follow_up(grammar_fixed, question, job_role)

    analysis_result = {
        "원본 답변": answer,
        "정리된 답변": cleaned_answer,
        "맞춤법 교정된 답변": grammar_fixed,
        "가독성 분석": readability,
        "답변 적절성 평가": relevance_feedback,
        "후속 질문": follow_up_question
    }

    return analysis_result


if __name__ == "__main__":
    # 예제 실행
    question = "자신의 강점은 무엇인가요?"
    answer = "음.. 저는 문제 해결 능력이 좋고, 새로운 기술을 배우는 걸 좋아합니다. 그리고..."
    job_role = "소프트웨어 개발자"

    analysis = analyze_answer(question, answer, job_role)
    print(json.dumps(analysis, indent=4, ensure_ascii=False))

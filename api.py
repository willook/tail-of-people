import glob
import os

import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


def get_recent_resumes(current_path, limit=5):
    """
    현재 이력서와 동일한 포지션에서 최근 업로드된 이력서들을 가져옵니다.

    Args:
        current_path (str): 현재 이력서의 경로
        limit (int): 가져올 최근 이력서 수 (기본값: 5)

    Returns:
        list: 최근 이력서 경로 및 텍스트 정보 리스트
    """
    # 현재 포지션 폴더 경로 추출
    parts = current_path.split(os.sep)
    position_idx = parts.index("database") + 1
    position_folder = parts[position_idx]
    position_path = os.path.join("database", position_folder)

    # 포지션 폴더 내 모든 날짜 폴더 가져오기
    date_folders = glob.glob(os.path.join(position_path, "*"))
    date_folders.sort(reverse=True)  # 최신 날짜 순으로 정렬

    # 각 폴더에서 이력서 파일과 리뷰 결과 파일 찾기
    resume_data = []
    for folder in date_folders[:limit]:
        # PDF 파일 찾기
        pdf_files = glob.glob(os.path.join(folder, "*.pdf"))
        if not pdf_files:
            continue

        if pdf_files[0] == current_path:
            continue

        # 리뷰 파일 찾기
        review_file = os.path.join(folder, "review_result.txt")
        if not os.path.exists(review_file):
            continue

        # with open(pdf_files[0], "rb") as f:
        #     resume_text = f.read()

        with open(review_file, "r", encoding="utf-8") as f:
            review_content = f.read()

        resume_data.append(
            {
                "folder": folder,
                "pdf_path": pdf_files[0],
                "review_content": review_content,
            }
        )

        if len(resume_data) >= limit:
            break

    return resume_data


def compare_recent_5_resumes(file_path, model="gpt-4o"):
    """
    최근 5개의 이력서를 비교 평가합니다.

    Args:
        file_path (str): 현재 이력서의 경로
        model (str): 사용할 GPT 모델명

    Returns:
        str: 비교 평가 결과
    """
    try:
        # 현재 이력서의 리뷰 결과 가져오기
        current_folder = os.path.dirname(file_path)
        current_review_path = os.path.join(current_folder, "review_result.txt")

        if not os.path.exists(current_review_path):
            return "현재 이력서의 리뷰 결과를 찾을 수 없습니다."

        with open(current_review_path, "r", encoding="utf-8") as f:
            current_review = f.read()

        # with open(file_path, "rb") as f:
        #     current_resume = f.read()

        # 최근 이력서들 가져오기
        recent_resumes = get_recent_resumes(file_path)

        if len(recent_resumes) < 2:  # 현재 이력서 포함하여 최소 2개 이상 필요
            return "비교할 이력서가 충분하지 않습니다. 최소 2개 이상의 이력서가 필요합니다."

        # 비교를 위한 프롬프트 작성
        prompt = f"""
다음은 최근에 검토된 이력서들의 리뷰 결과입니다. 이 이력서들을 정량적으로 비교 분석하고, 현재 이력서의 순위를 제시해주세요.

현재 이력서:
{current_review}

다른 이력서 리뷰들:
"""
        # 다른 이력서 리뷰 추가 (현재 이력서는 제외)
        for i, resume in enumerate(recent_resumes):
            # 현재 이력서와 동일한 폴더는 건너뛰기
            if os.path.normpath(resume["folder"]) == os.path.normpath(current_folder):
                continue

            prompt += f"""
이력서 {i+1} 리뷰:
{resume["review_content"]}
"""

        prompt += """
위 이력서들을 비교 분석하여 다음 사항에 대해 답변해주세요:
1. 현재 이력서의 다른 이력서들 대비 상대적 순위 (상위 몇 %)
2. 현재 이력서의 다른 이력서들과 비교했을 때 두드러진 강점
3. 현재 이력서의 다른 이력서들과 비교했을 때 개선이 필요한 부분
4. 최종적으로 이 지원자를 채용해야 할지에 대한 추천 (다른 이력서들과 비교하여)
"""

        # OpenAI API 호출
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "당신은 액트노바라는 소규모 스타트업 채용 담당자입니다. 여러 이력서를 비교 분석하고 상대적인 평가를 제공합니다.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=2500,
        )

        # API 응답에서 비교 결과 추출
        comparison_result = response.choices[0].message.content
        return comparison_result

    except Exception as e:
        # 오류 발생 시 상세 메시지 반환
        error_message = f"이력서 비교 중 오류가 발생했습니다: {str(e)}"
        return error_message


def review_resume(
    resume_text: str,
    model: str = "gpt-4o",
    position: str = "컴퓨터 비전 머신러닝 엔지니어",
) -> str:
    """
    이력서 텍스트를 GPT에 전송하여 리뷰 결과를 받아옵니다.

    Args:
        resume_text (str): 이력서 텍스트 내용
        model (str): 사용할 GPT 모델명
        position (str): 지원 포지션

    Returns:
        str: GPT가 제공한 이력서 리뷰 결과
    """
    try:
        # 이력서 리뷰 프롬프트 작성
        prompt = f"""
다음은 이력서 내용입니다. 이 이력서를 채용 담당자의 관점에서 정량적으로 평가한 후 서류 합격 여부를 엄격하게 판단해주세요.

이력서 내용:
{resume_text}
        """

        # OpenAI API 호출
        response = openai.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": f"당신은 액트노바라는 소규모 스타트업 {position}(으)로서 뛰어난 동료를 구하고 있습니다. 이력서를 보고 서류 통과 여부를 결정하고 그 이유를 제시해주세요.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=2500,
        )

        # API 응답에서 리뷰 결과 추출
        review_result = response.choices[0].message.content
        return review_result

    except Exception as e:
        # 오류 발생 시 상세 메시지 반환
        error_message = f"이력서 리뷰 중 오류가 발생했습니다: {str(e)}"
        return error_message

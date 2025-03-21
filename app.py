import datetime
import io
import os
import time

import streamlit as st
from dotenv import load_dotenv

from api import compare_recent_5_resumes, review_resume
from utils import extract_text_from_pdf, save_file

load_dotenv()

model = "gpt-4o"


# Streamlit 페이지 제목
st.title("Tail Of People")

# 📌 포지션 선택
positions = {
    "컴퓨터 비전 머신러닝 엔지니어": "컴퓨터 비전 머신러닝 엔지니어",
    "디자이너": "디자이너",
    "Next.js 프론트엔드 개발자": "Next.js 프론트엔드 개발자",
}

# 📌 session_state에서 결과 초기화
if "resume_text" not in st.session_state:
    st.session_state.resume_text = None
if "review_result" not in st.session_state:
    st.session_state.review_result = None
if "elapsed_time" not in st.session_state:
    st.session_state.elapsed_time = None
if "selected_position" not in st.session_state:
    st.session_state.selected_position = "컴퓨터 비전 머신러닝 엔지니어"
if "saved_file_path" not in st.session_state:
    st.session_state.saved_file_path = None
if "file_path" not in st.session_state:
    st.session_state.file_path = None
if "reviews_5_resumes" not in st.session_state:
    st.session_state.reviews_5_resumes = None

# 📌 포지션 선택 라디오 버튼
selected_position = st.radio(
    "지원 포지션을 선택하세요:",
    list(positions.keys()),
    index=0,  # 기본값은 첫 번째 항목 (컴퓨터 비전 머신러닝 엔지니어)
)
st.session_state.selected_position = positions[selected_position]

# 📌 파일 업로드 (PDF 파일만 허용)
uploaded_file = st.file_uploader("이력서 파일을 업로드하세요", type=["pdf"])

if uploaded_file is not None and st.session_state.resume_text is None:
    # 📌 업로드된 PDF 파일 저장
    try:
        # 파일 저장
        position_folder = st.session_state.selected_position
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        save_folder = os.path.join("database", position_folder, current_time)
        file_path = os.path.join(save_folder, uploaded_file.name)
        save_file(uploaded_file, file_path)
        st.session_state.saved_file_path = file_path
        st.success("이력서 파일을 업로드했습니다.")

        # PDF 파일 읽기
        text_data = extract_text_from_pdf(file_path)
        st.session_state.resume_text = text_data
        st.session_state.file_path = file_path

    except Exception as e:
        st.error(f"PDF 파일 처리 중 오류가 발생했습니다: {e}")

if st.session_state.resume_text is not None:
    # 📌 추출된 이력서 내용 보여주기
    st.write("📄 업로드한 이력서 내용:")
    st.text_area("이력서 내용", st.session_state.resume_text, height=200)

    # 📌 이력서 리뷰 버튼
    if st.button("이력서 리뷰 시작") and st.session_state.review_result is None:
        start_time = time.perf_counter()

        # 📌 이력서 리뷰 처리
        with st.status(
            f"{st.session_state.selected_position} 포지션에 대한 이력서 리뷰 중입니다... (수 분 내외 소요)",
            expanded=True,
        ) as status:
            try:
                review_result = review_resume(
                    st.session_state.resume_text,
                    model=model,
                    position=st.session_state.selected_position,
                )
                end_time = time.perf_counter()  # ⏳ 종료 시간 기록
                elapsed_time = end_time - start_time  # 경과 시간 계산
                status.update(
                    label=f"✅ 이력서 리뷰 완료! (처리 시간: {elapsed_time:.2f}초)",
                    state="complete",
                )
                st.session_state.review_result = review_result
                st.session_state.elapsed_time = elapsed_time
            except Exception as e:
                status.update(
                    label=f"❌ 이력서 리뷰 실패: {e}",
                    state="error",
                )

if st.session_state.review_result is not None:
    # 📌 리뷰 결과 보여주기
    st.write("### 💡 이력서 리뷰 결과")
    st.markdown(st.session_state.review_result)

    # 📌 리뷰 결과 파일로 저장
    if st.session_state.saved_file_path:
        save_folder = os.path.dirname(st.session_state.saved_file_path)
        review_file_path = os.path.join(save_folder, "review_result.txt")

        try:
            with open(review_file_path, "w", encoding="utf-8") as f:
                f.write(st.session_state.review_result)
            st.success("이력서 리뷰를 완료했습니다.")
        except Exception as e:
            st.error(f"리뷰 결과 저장 중 오류가 발생했습니다: {e}")

    # 📌 리뷰 결과 다운로드 기능
    output = io.BytesIO()
    output.write(st.session_state.review_result.encode("utf-8"))
    output.seek(0)  # 스트림의 시작 위치로 이동

    # 📌 다운로드 버튼 생성
    st.download_button(
        label="📥 이력서 리뷰 결과 다운로드",
        data=output,
        file_name=f"resume_review_{time.strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
    )

    # 📌 최근 5개의 이력서 비교
    if (
        st.button("최근 5개의 이력서 비교")
        and st.session_state.reviews_5_resumes is None
    ):
        # 현재 파일 경로가 있는지 확인
        if st.session_state.file_path:
            with st.status(
                "최근 이력서들과 비교 분석 중입니다... (수 분 내외 소요)",
                expanded=True,
            ) as status:
                try:
                    # 비교 분석 실행
                    comparison_result = compare_recent_5_resumes(
                        st.session_state.file_path, model=model
                    )
                    st.session_state.reviews_5_resumes = comparison_result
                    status.update(
                        label="✅ 이력서 비교 분석 완료!",
                        state="complete",
                    )
                except Exception as e:
                    status.update(
                        label=f"❌ 이력서 비교 분석 실패: {e}",
                        state="error",
                    )
        else:
            st.error("현재 이력서 파일 경로를 찾을 수 없습니다.")

    # 📌 비교 결과 표시
    if st.session_state.reviews_5_resumes is not None:
        st.write("### 📊 최근 이력서와의 비교 분석 결과")
        st.markdown(st.session_state.reviews_5_resumes)

        # 📌 비교 결과 다운로드 기능
        comparison_output = io.BytesIO()
        comparison_output.write(st.session_state.reviews_5_resumes.encode("utf-8"))
        comparison_output.seek(0)

        st.download_button(
            label="📥 비교 분석 결과 다운로드",
            data=comparison_output,
            file_name=f"resume_comparison_{time.strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            key="download_comparison",
        )

    # 📌 새로운 리뷰 시작 버튼
    if st.button("새로운 이력서 업로드"):
        st.session_state.resume_text = None
        st.session_state.review_result = None
        st.session_state.elapsed_time = None
        st.session_state.saved_file_path = None
        st.session_state.file_path = None
        st.session_state.reviews_5_resumes = None
        st.rerun()

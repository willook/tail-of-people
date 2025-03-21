.PHONY: dev prod stop clean

# 개발 환경 실행
dev:
	@echo "Starting development server..."
	@python -m streamlit run app.py

# 프로덕션 환경 실행 (nohup으로 백그라운드 실행)
prod:
	@echo "Starting production server..."
	@nohup python -m streamlit run app.py > logs/server.log 2>&1 &

# 실행 중인 프로세스 종료
stop:
	@echo "Stopping server processes..."
	@-pkill -f "python -m streamlit run app.py"

# 좀비 프로세스 정리
clean:
	@echo "Cleaning up zombie processes..."
	@-ps aux | grep "python -m streamlit run app.py" | grep -v grep | awk '{print $$2}' | xargs -r kill -9

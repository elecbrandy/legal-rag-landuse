# 컨테이너 빌드 및 실행
up:
	docker-compose up --build -d

# 서비스 중지
down:
	docker-compose down

# 로그 확인
logs:
	docker-compose logs -f

# 프론트엔드만 재빌드 및 재시작
rebuild-frontend:
	docker-compose build frontend
	docker-compose up -d frontend

# 백엔드만 재빌드 및 재시작
rebuild-backend:
	docker-compose build backend
	docker-compose up -d backend
	
# 정리 (볼륨 포함 삭제)
clean:
	docker-compose down -v

# 완전 정리 (이미지, 볼륨, 네트워크 등 모두 삭제)
fclean:
	docker-compose down --rmi all -v --remove-orphans
	rm -rf chroma_data

	docker-compose up -d backend

# 백엔드 로그만 확인
logs-backend:
	docker-compose logs -f backend

# 프론트엔드 로그만 확인
logs-frontend:
	docker-compose logs -f frontend
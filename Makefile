.PHONY: install run test clean docker-build docker-run

install:
	pip install -r requirements.txt

run:
	python run.py

dev:
	streamlit run app/main.py

test:
	pytest tests/ -v

clean:
	rm -rf __pycache__ .pytest_cache outputs/*.wav outputs/*.mid outputs/*.npy

docker-build:
	docker build -t whispers-of-the-wires .

docker-run:
	docker-compose up -d

docker-stop:
	docker-compose down

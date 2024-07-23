cd web
docker build ./ -t ai-study-web 
cd ..
cd api 
docker build ./ -t ai-study-api -f Dockerfile_prod

cd ..

docker compose up -d


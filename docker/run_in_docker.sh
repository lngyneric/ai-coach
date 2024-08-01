cd ../src/api
docker build ./ -t ai-shifu-api
cd ../web
docker build ./ -t ai-shifu-web
cd ../admin-web 
docker build ./ -t ai-shifu-admin-web
cd ..
cd ..
cd docker
docker compose up 


start:
	docker-compose up

stop:
	docker-compose down -v

tests:
	docker-compose -f docker-compose.test.yml run --rm --service-ports run-tests

zip-1:
	docker-compose run --rm awscli awslocal s3 cp ./elife-666-vor-r1.zip s3://dev-elife-style-content-adapter-incoming
	date

zip-2:
	docker-compose run --rm awscli awslocal s3 cp ./elife-666-vor-r2.zip s3://dev-elife-style-content-adapter-incoming
	date

del-zip-1:
	docker-compose run --rm awscli awslocal s3 rm s3://dev-elife-style-content-adapter-incoming/elife-666-vor-r1.zip
	date

del-zip-2:
	docker-compose run --rm awscli awslocal s3 rm s3://dev-elife-style-content-adapter-incoming/elife-666-vor-r2.zip
	date

.PHONY: start stop tests zip-1 zip-2 del-zip-1 del-zip-2

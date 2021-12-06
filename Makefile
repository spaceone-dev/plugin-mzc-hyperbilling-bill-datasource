export WS_ROOT=$(shell pwd)
export PLUGIN=plugin-mzc-hyperbilling-bill-datasource
export CACHE = 
export REPO=pyengine
export VERSION=1.0

define banner
	@echo "========================================================================"
	@echo " $(1)"
	@echo "========================================================================"
	@echo " "
endef

.PHONY: build
build:
	docker build -t debug/${PLUGIN} . $(CACHE)
	docker tag debug/${PLUGIN} ${REPO}/${PLUGIN}:${VERSION}

.PHONY: debug
debug: build
	docker run -ti --name ${PLUGIN} -v ${WS_ROOT}:/opt debug/${PLUGIN}

.PHONY: test
test: build
	docker run -d --name ${PLUGIN} -v ${WS_ROOT}:/opt debug/${PLUGIN}
	docker exec ${PLUGIN} bash -c "export Email=${Email}; export Key=${Email}; export Account=${Account}; cd /opt/test/grpc; spaceone test"

.PHONY: upload
upload: build
	docker tag debug/${PLUGIN} ${REPO}/${PLUGIN}:${VERSION}       
	docker push ${REPO}/${PLUGIN}:${VERSION}

.PHONY: clean
clean:
	docker rm -f ${PLUGIN}

help:
	@echo "Make Targets:"
	@echo " build                                        - build Plugin Docker Image"
	@echo " debug                                        - build Plugin Docker Image and Run"
	@echo " test                                         - build Plugin Docker Image then Run UnitTest case"
	@echo " upload VERSION=x.y                           - build Plugin Docker Image then upload image"
	@echo " clean                                        - stop Plugin Docker"

BASE_STACK_NAME=geolocator
LOGGER ?= DEBUG
STACK_NAME_SUFFIX ?= $(USER)
BUILD_BUCKET ?= geolocator

PILLAR=hs
DOMAIN=source
TEAM=consolidation
PROJECT=geolocator

ACCOUNT=311937351692
REGION=eu-west-1
ENV?=development
KINESIS_INPUT_STREAM?=consolidation-geocoder-input-dev
KINESIS_OUTPUT_STREAM?=consolidation-geocoder-output-dev

# GITHUB_ACTIONS is set only in github actions environment.
# Deployment to prod is not allowed outside github actions
#ifndef GITHUB_ACTIONS
#    ifeq ($(ENV), production)
#    $(error Deployment to production is not allowed from a development environment!)
#    endif
#endif

ifeq ($(ENV), production)
	OWNER=$(TEAM)
	STACK_NAME_SUFFIX=$(ENV)
	KINESIS_INPUT_STREAM=inventory--matchbox-streams--content.accommodation.candidate--prod
    KINESIS_OUTPUT_STREAM=consolidation-geolocator-output-prod
else
	ENV=development
	OWNER=$(USER)
endif

ifdef TARGET
	TPL=cloudformation/$(TARGET).yaml
endif

# CloudFormation stacks do not allow underscores but support dashes. Python package names support underscores
# but not dashes. The Stackname contains the component name (or TARGET) which is often the same as the package name.
# To prevent clashes we replace underscores with dashes.
TARGET_TPL=$(subst _,-,$(TARGET))
PACKAGED_TPL=$(TARGET_TPL)-packaged-cloudformation-template.yaml

# The SNS Topic ARN must be changed if/when the stack name format or the topic name changes.
SNS_TOPIC_ARN ?= arn:aws:sns:$(REGION):$(ACCOUNT):$(BASE_STACK_NAME)--resources--$(STACK_NAME_SUFFIX)--alarms-topic

.PHONY: install-dependencies sync build package deploy release clean test-component test test-coverage flake8


init:
	python3 -m venv .venv
	@echo Please run "source .venv/bin/activate" to activate the Python environment.

dev:
	@echo "Installing Dev Dependencies"
	pip install --upgrade pip
	pip install -r requirements-dev.txt -t _build

clean:
	@echo "Cleaning old build files..."
	@find . -name "*.pyc" -exec rm -f {} \;
	@rm -rf _build

sync:

ifdef TARGET
	@echo "Copy the codes related to the specific TARGET=$(TARGET)"
	@mkdir -p _build/$(TARGET)
	@mkdir -p _build/data
	@mkdir -p _build/schemas
ifneq ("$(wildcard src/$(TARGET))","")
	@cp -R src/$(TARGET)/* _build/$(TARGET)/
endif
ifneq ("$(wildcard data)","")
	@cp -R data/* _build/data/
endif
ifneq ("$(wildcard schemas)","")
	@cp -R schemas/* _build/schemas/
endif
else
	$(error "No TARGET is specified.")
endif


install-dependencies:
	@pip install -r src/consolidator/requirements.txt -t _build
	@pip install -r src/geocode/requirements.txt -t _build
	@pip install -r src/router/requirements.txt -t _build
	@pip install -r requirements-dev.txt -t _build


build: clean
ifdef TARGET
	@mkdir -p _build
	@pip install --upgrade pip
ifneq ("$(wildcard src/$(TARGET)/requirements.txt)","")
	@pip install -r src/$(TARGET)/requirements.txt -t _build
endif
else
	$(error "No TARGET is specified.")
endif

	@$(MAKE) sync

package:
	@mkdir -p _build
	@echo "Preparing and uploading AWS package for $(TPL) for $(TARGET_TPL)."
	aws cloudformation package \
		--template-file $(TPL) \
		--s3-bucket $(BUILD_BUCKET) \
		--s3-prefix packages \
		--output-template-file _build/$(PACKAGED_TPL)

deploy:
	@echo "Deploying template for $(TPL) for $(TARGET_TPL)."
	aws cloudformation deploy \
		--template-file _build/$(PACKAGED_TPL) \
		--stack-name $(BASE_STACK_NAME)--$(TARGET_TPL)--$(STACK_NAME_SUFFIX) \
		--capabilities CAPABILITY_NAMED_IAM \
		--no-fail-on-empty-changeset \
		--parameter-overrides \
			Environment=$(ENV) \
			Owner=$(OWNER) \
			LogLevel=$(LOGGER) \
			DeploymentBucket=$(BUILD_BUCKET) \
			KinesisInputStream=$(KINESIS_INPUT_STREAM) \
			KinesisOutputStream=$(KINESIS_OUTPUT_STREAM)

		--tags Pillar=$(PILLAR) Domain=$(DOMAIN) Team=$(TEAM) Project=$(PROJECT) Owner=$(OWNER) Environment=$(ENV)

release: flake8 test build package deploy
	@echo "CloudFormation stacks deployment completed"

test-coverage:
	SECRET_NAME=consolidation/geolocator GEOCODER_API_KEYS=geocoder_api_key PYTHONPATH=./_build:./src pytest tests/consolidator --cov=src --full-trace
	SECRET_NAME=consolidation/geolocator GEOCODER_API_KEYS=geocoder_api_key PYTHONPATH=./_build:./src pytest tests/geocode --cov=src --full-trace
	SECRET_NAME=consolidation/geolocator GEOCODER_API_KEYS=geocoder_api_key PYTHONPATH=./_build:./src pytest tests/router --cov=src --full-trace

test-component:
	@$(MAKE) sync TARGET=$(TARGET)
	SECRET_NAME=consolidation/geolocator GEOCODER_API_KEYS=geocoder_api_key PYTHONPATH=./_build python -m pytest tests/$(TARGET)

flake8:
	#  Need all the dependecies to run flake8
	@$(MAKE) install-dependencies
	pip install flake8
	@echo "flake8 errors: " && flake8 ./src --count --select=E9,F63,F7,F82 --show-source --statistics

test:
	@$(MAKE) install-dependencies
	@$(MAKE) test-component TARGET=consolidator
	@$(MAKE) test-component TARGET=geocode
	@$(MAKE) test-component TARGET=router

notify-failure:
	aws sns publish \
		--topic-arn $(SNS_TOPIC_ARN) \
		--subject "$(NOTIFICATION_SUBJECT)" \
		--message "$(NOTIFICATION_MESSAGE)"
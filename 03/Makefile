plan_file=./tfplan
src='-chdir=src'
BUCKET=${ENVIRONMENT}.tf-state.bevel.internal
KEY=${ENVIRONMENT}_infrastructure.tfstate
LINT_OUTPUT=logs

.PHONY: lint
lint: ## Runs all autoformatting and linting targets
lint: tf/fmt
lint: tf/validate

.PHONY: tflint
tflint:
	tflint --chdir src | tee ../${LINT_OUTPUT}/root.log
	tflint --chdir src/assets | tee ../${LINT_OUTPUT}/assets.log
	tflint --chdir src/ecs_service | tee ../${LINT_OUTPUT}/ecs_service.log

.PHONY: tf/fmt
tf/fmt: ## checks the format of terraform files.
tf/fmt:
	terraform fmt -check -recursive modules
	terraform fmt -check -recursive src

.PHONY: tf/fmt/update
tf/fmt/update: ## Formats terraform files.
tf/fmt/update:
	terraform ${src} fmt -recursive

.PHONY: tf/validate
tf/validate: ## Validates terraform file (pre plan)
tf/validate: tf/init
tf/validate:
	terraform ${src} validate

.PHONY: tf/plan
tf/plan: ## Does all pre apply actions
tf/plan: tf/init
tf/plan: 
	terraform ${src} plan \
		-out ${plan_file} \
		-var "environment=${ENVIRONMENT}" \
		-var "ops_infra_gitlab_registry_token=${ops_infra_gitlab_registry_token}" \
		-var "auth0_client_secret=${${ENVIRONMENT}_auth0_client_secret}" \
		-var "auth0_client_id=${${ENVIRONMENT}_auth0_client_id}" \
		-var "webex_integration_key=${webex_integration_key}" 

.PHONY: tf/apply
tf/apply: ## Take plan file and apply to aws
tf/apply:
	terraform ${src} apply ${plan_file} \
		-var "environment=${ENVIRONMENT}" \
		-var "gitlab_registry_token=${gitlab_registry_token}"

.PHONY: tf/build-and-apply
tf/build-and-apply: ## Format, validated, plan and apply in a single step
tf/build-and-apply: tf/fmt
tf/build-and-apply: tf/init
tf/build-and-apply: tf/validate
tf/build-and-apply: tf/plan
tf/build-and-apply: tf/apply

.PHONY: tf/init
tf/init: ## Pulls required terraform modules
tf/init: 
	terraform ${src} init \
		-backend-config="bucket=${BUCKET}" \
		-backend-config="dynamodb_table=bevel-${ENVIRONMENT}-terraform-lock" \
		-backend-config="key=${KEY}" \
		-backend-config="region=${AWS_REGION}"


.PHONY: tf/deploy
tf/deploy: ## End-to-end deploy, intended for only CICD usage
tf/deploy: tf/init
tf/deploy: 
	terraform ${src} apply \
		--auto-approve \
		--input=false \
		-var "environment=${ENVIRONMENT}" \
		-var "ops_infra_gitlab_registry_token=${ops_infra_gitlab_registry_token}" \
		-var "auth0_client_secret=${${ENVIRONMENT}_auth0_client_secret}" \
		-var "auth0_client_id=${${ENVIRONMENT}_auth0_client_id}" \
		-var "webex_integration_key=${webex_integration_key}" 


.PHONY: tf/danger/destroy
tf/danger/destroy: ## End-to-end destory everything, forever, no going back.
tf/danger/destroy: tf/init
tf/danger/destroy: 
	terraform ${src} destroy \
		--auto-approve \
		--input=false \
		-var "environment=${ENVIRONMENT}" \
		-var "ops_infra_gitlab_registry_token=${ops_infra_gitlab_registry_token}"\
		-var "auth0_client_secret=${${ENVIRONMENT}_auth0_client_secret}"\
		-var "auth0_client_id=${${ENVIRONMENT}_auth0_client_id}"\
		-var "webex_integration_key=${webex_integration_key}"


.PHONY: help
help: ## Shows all targets and help from the Makefile (this message).
	@grep --no-filename -E '^([a-z.A-Z_%-/]+:.*?)##' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = "(: *?)## ?"}; { \
			if (length($$1) > 0) { \
				printf "  \033[36m%-30s\033[0m %s\n", $$1, $$2; \
			} else { \
				printf "%s\n", $$2; \
			} \
		}'
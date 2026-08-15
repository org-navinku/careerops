#!/bin/bash

# ============================================================================
# CareerOps DynamoDB Deployment Script
# ============================================================================
# This script creates the DynamoDB tables used by CareerOps:
# - applications
# - runbook
#
# Usage: ./deploy-dynamodb.sh [--region us-east-1]
# ============================================================================

set -e

REGION="us-east-1"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --region)
            REGION="${2:-us-east-1}"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./deploy-dynamodb.sh [--region us-east-1]"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: ./deploy-dynamodb.sh [--region us-east-1]"
            exit 1
            ;;
    esac
done

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}INFO: $1${NC}"
}

log_success() {
    echo -e "${GREEN}OK: $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}WARN: $1${NC}"
}

log_error() {
    echo -e "${RED}ERROR: $1${NC}"
}

log_section() {
    echo -e "\n${BLUE}--------------------------------------------------------${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}--------------------------------------------------------${NC}\n"
}

check_aws_cli() {
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Install it before running this script."
        log_info "Visit: https://aws.amazon.com/cli/"
        exit 1
    fi

    log_success "AWS CLI found"
}

check_aws_credentials() {
    if ! aws sts get-caller-identity --region "$REGION" &> /dev/null; then
        log_error "AWS credentials are not configured or are invalid."
        log_info "Run: aws configure"
        exit 1
    fi

    log_success "AWS credentials valid"
}

create_table() {
    local table_name="$1"
    local purpose="$2"

    log_info "Checking '$table_name' table..."
    if aws dynamodb describe-table --table-name "$table_name" --region "$REGION" &> /dev/null; then
        log_warning "'$table_name' table already exists"
        return
    fi

    log_info "Creating '$table_name' table..."
    aws dynamodb create-table \
        --table-name "$table_name" \
        --attribute-definitions \
            AttributeName=userId,AttributeType=S \
            AttributeName=id,AttributeType=S \
        --key-schema \
            AttributeName=userId,KeyType=HASH \
            AttributeName=id,KeyType=RANGE \
        --billing-mode PAY_PER_REQUEST \
        --region "$REGION" \
        --tags Key=Name,Value=CareerOps Key=Purpose,Value="$purpose"

    log_info "Waiting for '$table_name' table to be active..."
    aws dynamodb wait table-exists --table-name "$table_name" --region "$REGION"
    log_success "'$table_name' table created"
}

create_dynamodb_tables() {
    log_section "Creating DynamoDB Tables"
    create_table "applications" "ApplicationTracking"
    create_table "runbook" "InterviewRunbook"
    log_success "DynamoDB tables ready"
}

verify_deployment() {
    log_section "Verifying DynamoDB Tables"

    local tables
    tables=$(aws dynamodb list-tables --region "$REGION" --query 'TableNames' --output text)

    for table_name in applications runbook; do
        if echo "$tables" | grep -q "$table_name"; then
            log_success "'$table_name' table found"
        else
            log_error "'$table_name' table not found"
            return 1
        fi
    done
}

print_summary() {
    log_section "Deployment Summary"

    cat << EOF
${GREEN}DynamoDB setup complete.${NC}

Tables:
  - applications (userId HASH, id RANGE)
  - runbook (userId HASH, id RANGE)

Billing:
  - PAY_PER_REQUEST

Region:
  - ${REGION}

Application configuration:
  - Set AWS_REGION=${REGION} when running the backend.
  - Provide AWS credentials through the standard AWS credential provider chain.

EOF
}

main() {
    echo -e "${BLUE}CareerOps DynamoDB Deployment${NC}\n"
    log_info "Region: $REGION"

    log_section "Pre-flight Checks"
    check_aws_cli
    check_aws_credentials

    create_dynamodb_tables
    verify_deployment
    print_summary
}

main "$@"

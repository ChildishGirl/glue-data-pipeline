# Serverless data transformation pipeline
**Table of Contents**

- [Data pipeline requirements](#data-pipeline-requirements)
  * [Problem Context](#problem-context)
  * [Constraints](#constraints)
  * [Functional requirements](#functional-requirements)
  * [Non-functional requirements](#non-functional-requirements)
- [Proposed solution](#proposed-solution)
  * [Architecture diagram](#architecture-diagram)
  * [Cost breakdown](#cost-breakdown)
  * [Deployment](#deployment)

## Data pipeline requirements

### Problem Context

Data providers upload raw data into S3  bucket. Then data engineers complete data checks and perform simple transformations before loading processed data to another S3 bucket, namely:
- Ensure "Currency" column contains only "USD".
- Ensure "Currency" column has no missing values.
- Drop  "Currency" column as there is only one value given - "USD".
- Add a new "Average" column based on "High" and "Low" columns.
- Save processed data to S3 bucket in parquet format.

For process testing, you can use [coffee dataset from Kaggle](https://www.kaggle.com/datasets/psycon/daily-coffee-price "coffee dataset from Kaggle").

### Constraints

- AWS is the preferred cloud provider
- Development team has limited capacity, so the solution should require minimal development and maintenance effort

### Functional requirements

- **FR-1** Application should save table schema
- **FR-2** Application should be triggered by file upload event
- **FR-3** Application should perform data quality checks and transformations
- **FR-4** Data should be stored in query-optimised format
- **FR-5** Application should notify users if data checks fail via corporate messenger

### Non-functional requirements
- **NFR-1** Due to massive file size processing can take up to 20 minutes
- **NFR-2** Solution should be cost effective

## Proposed solution

> 💡 *Everything in software architecture is a trade-off. First Law of Software Architecture*


### Architecture diagram

![Architecture diagram](images/Architecture_diagram.png)

---

All resources will be deployed as a Stack to allow centralised creation, modification and deletion of resources in any account. The process will be monitored by CloudWatch and all errors will be sent to Slack channel.

To trigger the process by raw file upload event, (1) enable S3 Events Notifications to send event data to SQS queue and (2) create EventBridge Rule to send event data and trigger Glue Workflow. Both event handlers are needed because they have different ranges of targets and different event JSON structures.

Once the new raw file is uploaded, Glue Workflow starts:

- The first component of Glue Workflow is Glue Crawler. It polls SQS queue to get information on newly uploaded files and crawls only them instead of a full bucket scan. If the file is corrupted, then process will stop and error event will be generated.

- The second component of Glue Workflow is Glue Job. It completes the business logic (data transformation and end user notification) and saves the processed data to another S3 bucket.

### Cost breakdown

| Service | Configuration | Monthly cost |
| --- | --- | --- |
| Glue Job | 1 DPU, running time 600 minutes | $4.40 |
| Amazon S3 | S3 standard (100 GB), S3 Glacier Flexible Retrieval (100 GB) | $2.88 |
| Glue Crawler | Running time 300 minutes | $2.20 |
| AWS CloudFormation | Third-party extension operations (0) | $0.00 |
| Amazon SQS | Requests per month 600 | $0.00 |
|TOTAL COST |  | $9.48 |

### Deployment

All infrastructure components are prepared using IaC tool - AWS CDK.

[CDK assets](cdk-assets/) 
# swe1-app

[![Build Status](https://app.travis-ci.com/jay-den-21/swe1-app.svg?branch=main)](https://app.travis-ci.com/github/jay-den-21/swe1-app)
[![Coverage Status](https://coveralls.io/repos/github/jay-den-21/swe1-app/badge.svg?branch=main)](https://coveralls.io/github/jay-den-21/swe1-app?branch=main)

Individual Software Engineering I assignment: the Django 5.2 polls application
from tutorial parts 1–4, prepared for AWS Elastic Beanstalk.

- Repository: https://github.com/jay-den-21/swe1-app
- Public application: http://swe1-app-jayden.us-east-1.elasticbeanstalk.com/polls/
- AWS environment: `swe1-app-env` in `us-east-1`, single `t3.micro` instance.

## Run locally

Use Python 3.12.6 or newer in the 3.12 series (matching the Elastic Beanstalk
platform). Black does not support Python 3.12.5 because of a Python AST safety bug.

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_polls
python manage.py runserver
```

Open http://127.0.0.1:8000/polls/. The root URL also redirects to the polls list.
Two example questions are created by `seed_polls`. Running it again preserves
existing questions and vote counts.

To manage questions and choices through Django admin:

```bash
python manage.py createsuperuser
```

Then open http://127.0.0.1:8000/admin/. Admin accounts belong to each environment's
database; credentials are never committed. The admin login protects question and
choice management. There is no public registration page, and public voting does
not require an account.

## Tutorial coverage

| Part | Implementation |
| --- | --- |
| 1 | Django project, polls application, views and URL routing |
| 2 | Question/Choice models, migrations, admin registration and authenticated question/choice management |
| 3 | Templates, question list/detail/results views and 404 responses |
| 4 | CSRF-protected voting form, atomic vote increment, redirect after POST and generic views |

## Verify

```bash
python manage.py check
python manage.py test
python manage.py makemigrations --check --dry-run
```

Tests cover published questions, empty lists, detail pages, missing questions,
valid/invalid votes, choices belonging to other questions, POST-only voting,
CSRF protection and repeatable example data initialization.

## Continuous integration

Install the development tools and run the same checks used by Travis CI:

```bash
python -m pip install -r requirements-dev.txt
python -m black --check .
python -m flake8
python manage.py check
python manage.py makemigrations --check --dry-run
python -m coverage run manage.py test --noinput
python -m coverage report
```

To fix formatting, run `python -m black .`. Flake8 uses the same 88-character
line length. Coverage measures `mysite` and `polls`, including branches, while
excluding generated migrations and test code. There is no minimum coverage gate.

`.travis.yml` runs these checks on pushes and pull requests and uploads coverage
to Coveralls. Every command, including the upload, must succeed. Only a successful
push build of this repository's `main` branch deploys to `swe1-app-env`; pull
requests never deploy. The build waits for Elastic Beanstalk to finish updating.

Enable this repository in Travis CI and Coveralls. In Travis repository settings,
enable both push and pull-request builds, then configure:

| Variable | Purpose |
| --- | --- |
| `AWS_ACCESS_KEY_ID` | Dedicated CI deployment identity; hide from build logs |
| `AWS_SECRET_ACCESS_KEY` | Deployment secret; hide from build logs |
| `EB_BUCKET` | Existing S3 deployment bucket in `us-east-1` |
| `COVERALLS_REPO_TOKEN` | Only if required by Coveralls; hide from build logs |

Keep credentials out of Git and do not share encrypted environment variables
with fork pull requests. Formatting, lint and tests do not require AWS credentials.
`COVERALLS_SERVICE_NAME=travis-pro` selects the Travis CI `.com` integration.

After a PR build has appeared in GitHub, protect `main` with an active rule that
requires the exact Travis PR check shown on that PR. Invite `slurpysalmon` as a
collaborator with Write access for the course integration check.

## Elastic Beanstalk deployment

Use a **single-instance Python 3.12 / Amazon Linux 2023** environment. Install the
EB CLI separately from application requirements:

```bash
python -m pip install awsebcli 'botocore[crt]'
aws login --profile swe1-app --region us-east-1
aws sts get-caller-identity --profile swe1-app
eb init swe1-app --platform "Python 3.12" --region us-east-1 --profile swe1-app
```

The AWS identity needs permission to deploy Elastic Beanstalk and pass its service
role and EC2 instance profile. Confirm these roles and a usable VPC exist before
creating the environment. Use the intended personal AWS account.

The course deployment configuration expects `swe1-app-eb-service-role` with
`AWSElasticBeanstalkEnhancedHealth`, and the `swe1-app-eb-ec2-role` instance profile
with `AWSElasticBeanstalkWebTier`. Managed platform updates are disabled, so no
managed-update policy is required. AWS CLI browser sessions require the
`botocore[crt]` extra for EB CLI credential refresh.

For a first deployment, create a sample environment so its exact hostname is
known before configuring Django:

```bash
eb create swe1-app-env --single --sample --instance_type t3.micro \
  --service-role swe1-app-eb-service-role \
  --instance_profile swe1-app-eb-ec2-role
eb status
```

Set the following environment properties through Elastic Beanstalk's environment
configuration or `eb setenv`, before deploying the Django code:

| Variable | Value |
| --- | --- |
| `DJANGO_SECRET_KEY` | A private random value; generate with `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `DJANGO_ALLOWED_HOSTS` | The exact CNAME from `eb status`, without a scheme or path |
| `DJANGO_DEBUG` | `false` (also set in the committed EB configuration) |
| `DJANGO_DB_PATH` | `/var/app/data/db.sqlite3` (set in the committed EB configuration) |

Do not put the secret in source code or a committed configuration file. Production
startup intentionally fails if the secret is missing. `.env` files are ignored
by Git and EB, and are not automatically loaded by Django.

```bash
eb deploy
eb health
eb open
```

The deployment hook applies migrations, creates example polls if absent, and
collects static assets. EB runs Gunicorn using `mysite.wsgi:application`; nginx
serves `/static/`. The hook gives the application user write access to SQLite.

SQLite lives outside the deployed source directory to survive ordinary code
deployments on the same instance. **Instance replacement or environment
termination can still erase all votes and admin users.** Example polls will be
recreated on a new instance. Use an external database such as RDS PostgreSQL for
durable data or multiple instances.

The default setup supports HTTP. Enable `DJANGO_HTTPS_ENABLED=true` only after a
valid HTTPS endpoint and certificate are configured. This enables secure cookies
and HTTPS redirects. Do not use the public admin login over unencrypted HTTP.
`check --deploy` will report HTTPS/HSTS warnings until HTTPS is configured.

If deployment fails, inspect `eb logs` and `eb events`. Never commit credentials,
private keys, local databases or collected static files.

## Submission check

For the continuous integration assignment, submit these three URLs to Brightspace
after verifying a real Travis build, coverage upload and automatic deployment:

```text
Travis: https://app.travis-ci.com/github/jay-den-21/swe1-app
Application: http://swe1-app-jayden.us-east-1.elasticbeanstalk.com/polls/
GitHub: https://github.com/jay-den-21/swe1-app
```

- Open the actual public `/polls/` URL in a signed-out browser.
- Open a question, select an answer, vote, and verify the result count changes.
- Confirm the GitHub repository is accessible to the course team.
- Open a PR and confirm Travis starts automatically. Formatting or lint violations
  must fail the build; fixing them must allow it to pass.
- Confirm the required Travis PR check blocks merging until it passes.
- Confirm Coveralls receives coverage and both README badges resolve.
- Confirm the successful `main` build updates the EB application version.
- Submit the tested Travis dashboard, application and repository URLs to Brightspace.
- Keep the environment running until grading is complete. AWS resources can
  incur charges; terminate the environment only after it is no longer needed.

## References

- [Django tutorial, part 1](https://docs.djangoproject.com/en/5.2/intro/tutorial01/)
- [Django tutorial, part 2](https://docs.djangoproject.com/en/5.2/intro/tutorial02/)
- [Django tutorial, part 3](https://docs.djangoproject.com/en/5.2/intro/tutorial03/)
- [Django tutorial, part 4](https://docs.djangoproject.com/en/5.2/intro/tutorial04/)
- [AWS Django deployment guide](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html)

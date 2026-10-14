# swe1-app

Individual Software Engineering I assignment: the Django 5.2 polls application
from tutorial parts 1–4, prepared for AWS Elastic Beanstalk.

- Repository: https://github.com/jay-den-21/swe1-app
- Public application: http://swe1-app-jayden.us-east-1.elasticbeanstalk.com/polls/
- AWS environment: `swe1-app-env` in `us-east-1`, single `t3.micro` instance.

## Run locally

Use Python 3.12 (the same version as the intended Elastic Beanstalk platform).

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

Then open http://127.0.0.1:8000/admin/. Admin credentials are created locally and
are never committed. Online public voting does not require an account.

## Tutorial coverage

| Part | Implementation |
| --- | --- |
| 1 | Django project, polls application, views and URL routing |
| 2 | Question/Choice models, migrations and Django admin registration |
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

Submit these two URLs to Brightspace:

```text
Application: http://swe1-app-jayden.us-east-1.elasticbeanstalk.com/polls/
GitHub: https://github.com/jay-den-21/swe1-app
```

- Open the actual public `/polls/` URL in a signed-out browser.
- Open a question, select an answer, vote, and verify the result count changes.
- Confirm the GitHub repository is accessible to the course team.
- Submit the tested application URL and repository URL to Brightspace.
- Keep the environment running until grading is complete. AWS resources can
  incur charges; terminate the environment only after it is no longer needed.

## References

- [Django tutorial, part 1](https://docs.djangoproject.com/en/5.2/intro/tutorial01/)
- [Django tutorial, part 2](https://docs.djangoproject.com/en/5.2/intro/tutorial02/)
- [Django tutorial, part 3](https://docs.djangoproject.com/en/5.2/intro/tutorial03/)
- [Django tutorial, part 4](https://docs.djangoproject.com/en/5.2/intro/tutorial04/)
- [AWS Django deployment guide](https://docs.aws.amazon.com/elasticbeanstalk/latest/dg/create-deploy-python-django.html)

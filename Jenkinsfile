#!/usr/bin/env groovy

REPOSITORY = 'mapit'

node {
  def govuk = load '/var/lib/jenkins/groovy_scripts/govuk_jenkinslib.groovy'

  try {
    stage('Checkout') {
      checkout scm
      govuk.cleanupGit()
      govuk.mergeMasterBranch()
    }

    stage('Installing Packages') {
      sh("rm -rf ./test-venv")
      sh("virtualenv --no-site-packages ./test-venv")
      sh("./test-venv/bin/pip -q install -r requirements.txt")
    }

    stage('Tests') {
      govuk.setEnvar("GOVUK_ENV", "ci")
      sh("./test-venv/bin/python manage.py test mapit mapit_gb")
    }

    if (env.BRANCH_NAME == 'master') {
      stage('Push release tag') {
        govuk.pushTag(REPOSITORY, BRANCH_NAME, 'release_' + BUILD_NUMBER)
      }

      stage('Deploy to Integration') {
        govuk.deployIntegration(REPOSITORY, BRANCH_NAME, 'release', 'deploy')
      }
    }
  } catch (e) {
    currentBuild.result = 'FAILED'
    step([$class: 'Mailer',
          notifyEveryUnstableBuild: true,
          recipients: 'govuk-ci-notifications@digital.cabinet-office.gov.uk',
          sendToIndividuals: true])
    throw e
  }
}

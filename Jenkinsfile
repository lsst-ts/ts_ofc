#!/usr/bin/env groovy

pipeline {

    agent {
        // Use the docker to assign the Python version.
        // Use the label to assign the node to run the test.
        // It is recommended by SQUARE team do not add the label and let the
        // system decide.
        docker {
          image 'lsstts/develop-env:develop'
          args "-u root --entrypoint=''"
        }
    }

    options {
      disableConcurrentBuilds()
    }

    environment {
        // Position of LSST stack directory
        LSST_STACK = "/opt/lsst/software/stack"
        // saluser home directory
        SALUSER_HOME = "/home/saluser"
        // PlantUML url
        PLANTUML_URL = "https://managedway.dl.sourceforge.net/project/plantuml/plantuml.jar"
        // Pipeline stack Version
        STACK_VERSION = "current"
        // XML report path
        XML_REPORT = "jenkinsReport/report.xml"
        // Module name used in the pytest coverage analysis
        MODULE_NAME = "lsst.ts.ofc"
        // Authority to publish the document online
        user_ci = credentials('lsst-io')
        LTD_USERNAME = "${user_ci_USR}"
        LTD_PASSWORD = "${user_ci_PSW}"
        DOCUMENT_NAME = "ts-ofc"
    }

    stages {
        stage ('Unit Tests and Coverage Analysis') {
            steps {
                // Direct the HOME to WORKSPACE for pip to get the
                // installed library.
                // 'PATH' can only be updated in a single shell block.
                // We can not update PATH in 'environment' block.
                // Pytest needs to export the junit report.
                withEnv(["WORK_HOME=${env.WORKSPACE}"]) {
                    sh """
                        source ${env.LSST_STACK}/loadLSST.bash

                        cd ${WORK_HOME}
                        setup -k -r .
                        pytest --cov-report html --cov=${env.MODULE_NAME} --junitxml=${env.XML_REPORT}
                    """
                }
            }
        }
    }

    post {
        always {
            // The path of xml needed by JUnit is relative to
            // the workspace.
            junit "${env.XML_REPORT}"

            // Publish the HTML report
            publishHTML (target: [
                allowMissing: false,
                alwaysLinkToLastBuild: false,
                keepAll: true,
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: "Coverage Report"
            ])

            script{
              withEnv(["WORK_HOME=${env.WORKSPACE}"]) {
                def RESULT = sh returnStatus: true, script: """
                  source ${env.LSST_STACK}/loadLSST.bash

                  curl ${env.PLANTUML_URL} -o ${env.SALUSER_HOME}/plantuml.jar

                  pip install sphinxcontrib-plantuml

                  cd ${WORK_HOME}

                  setup -k -r .

                  package-docs build

                  pip install ltd-conveyor

                  ltd upload --product ${env.DOCUMENT_NAME} --git-ref \${GIT_BRANCH} --dir doc/_build/html
                    """

                if ( RESULT != 0 ) {
                    unstable("Failed to push documentation.")
                }
              }
            }

            // Change the ownership of workspace to Jenkins for the clean up
            // This is to work around the condition that the user ID of jenkins
            // is 1003 on TSSW Jenkins instance. In this post stage, it is the
            // jenkins to do the following clean up instead of the root in the
            // docker container.
            withEnv(["WORK_HOME=${env.WORKSPACE}"]) {
                sh 'chown -R 1003:1003 ${WORK_HOME}/'
            }

        }

        cleanup {
            // clean up the workspace
            deleteDir()
        }
    }
}

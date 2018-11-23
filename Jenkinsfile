#!/usr/bin/env groovy

pipeline {

    agent {
        // Use the docker to assign the Python version.
        // Use the label to assign the node to run the test.
        // The nodes in T&S teams are 'jenkins-master' and 'jenkins-el7-1'
        docker {
            image 'python:3.6.2'
            label 'jenkins-master'
        }
    }

    triggers {
        pollSCM('H * * * *')
    }

    environment {
        // Use the double quote instead of single quote
        // Add the PYTHONPATH
        PYTHONPATH="${env.WORKSPACE}/python"
        // XML report path
        XML_REPORT="jenkinsReport/report.xml"
    }

    stages {
        stage ('Install Requirements') {
            steps {
                // When using the docker container, we need to change
                // the HOME path to WORKSPACE to have the authority
                // to install the packages.
                withEnv(["HOME=${env.WORKSPACE}"]) {
                    sh """
                        pip install --user numpy scipy pytest coverage
                    """
                }
            }
        }

        stage('Unit Tests') { 
            steps {
                // Direct the HOME to WORKSPACE for pip to get the
                // installed library.
                // 'PATH' can only be updated in a single shell block.
                // We can not update PATH in 'environment' block.
                // Pytest needs to export the junit report. 
                withEnv(["HOME=${env.WORKSPACE}"]) {
                    sh """
                        export PATH=$PATH:${env.WORKSPACE}/.local/bin
                        pytest --junitxml=${env.WORKSPACE}/${env.XML_REPORT} ${env.WORKSPACE}/tests/*.py
                    """
                }
            }
        }

        stage('Coverage Analysis') { 
            steps {
                // Do the coverage analysis for multiple files.
                withEnv(["HOME=${env.WORKSPACE}"]) {
                    sh """
                        export PATH=$PATH:${env.WORKSPACE}/.local/bin
                        ./coverageAnalysis.sh "${env.WORKSPACE}/tests/test*.py"
                    """
                }
            }
        }
    }

    post {        
        always {
            // The path of xml needed by JUnit is relative to
            // the workspace.
            junit 'jenkinsReport/*.xml'

            // Publish the HTML report
            publishHTML (target: [
                allowMissing: false,
                alwaysLinkToLastBuild: false,
                keepAll: true,
                reportDir: 'htmlcov',
                reportFiles: 'index.html',
                reportName: "Coverage Report"
              ])
        }

        cleanup {
            // clean up the workspace
            deleteDir()
        }  
    }
}

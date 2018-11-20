#!/usr/bin/env groovy

pipeline {
    agent any
    stages {
        stage ('Build') {
            steps {
                sh """
                    virtualenv venv
                    . ./venv/bin/activate
                    python --version
                    python3 --version
                    pip --version
                """
            }
        }
        stage ('Install_Requirements') {
            steps {
                sh """
                    pip install numpy scipy pytest
                """
            }
        }
        stage('Unit Tests') {            
            steps {
                sh 'pytest ${WORKSPACE}/tests/*.py'   
            }        
        }
    }
 
    post {        
        always {            
            echo 'One way or another, I have finished'            
            deleteDir() /* clean up our workspace */        
        }        
        success {            
            echo 'I succeeeded!'        
        }        
        unstable {            
            echo 'I am unstable :/'        
        }        
        failure {            
            echo 'I failed :('        
        }        
        changed {            
            echo 'Things were different before...'        
        }    
    }
}

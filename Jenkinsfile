#!/usr/bin/env groovy

pipeline {
    agent {
        docker { image 'python:3.6.2' }
    }
    environment {
        PACKAGE_DIR=$WORKSPACE
        PYTHONPATH=$PYTHONPATH:${PACKAGE_DIR}/python
    }
    stages {
        stage ('Install_Requirements') {
            steps {
                sh """
                    pip install --upgrade pip
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

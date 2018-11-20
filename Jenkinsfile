#!/usr/bin/env groovy

pipeline {
    agent {
        docker { image 'python:3.6.2' }
    }
    stages {
        stage ('Install_Requirements') {
            steps {
                sh 'pip install --upgrade pip'
                sh 'pip install numpy scipy pytest'
            }
        }
        stage('Unit Tests') {            
            steps {
                sh 'echo $WORKSPACE'
                sh 'export PYTHONPATH=$PYTHONPATH:${WORKSPACE}/python'
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
